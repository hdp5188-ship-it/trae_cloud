"""Minimal Blender render service: token auth, serial GPU queue, MP4 output."""
import json
import os
import queue
import re
import secrets
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

ROOT = Path(os.environ.get("RENDER_ROOT", "/data")).resolve()
JOBS_DIR = ROOT / "jobs"
JOBS_DIR.mkdir(parents=True, exist_ok=True)

TOKEN = os.environ.get("RENDER_TOKEN", "").strip()
BLENDER = os.environ.get("BLENDER_BIN", "blender")
FFMPEG = os.environ.get("FFMPEG_BIN", "ffmpeg")
DEVICE = os.environ.get("RENDER_DEVICE", "auto").lower()
MAX_UPLOAD = int(os.environ.get("MAX_UPLOAD_MB", "4096")) * 1024 * 1024
MAX_RENDER_SECONDS = int(os.environ.get("MAX_RENDER_MINUTES", "240")) * 60
SCRIPT = Path(__file__).with_name("render.py")

app = FastAPI(title="Blender Render Service", version="0.1")
jobs: dict[str, dict] = {}
job_lock = threading.Lock()
job_queue: queue.Queue[str] = queue.Queue()


def now() -> float:
    return time.time()


def require_auth(authorization: Optional[str]) -> None:
    if not TOKEN:
        raise HTTPException(status_code=503, detail="RENDER_TOKEN is not configured")
    if not authorization or not secrets.compare_digest(authorization, f"Bearer {TOKEN}"):
        raise HTTPException(status_code=401, detail="Unauthorized")


def job_path(job_id: str) -> Path:
    return JOBS_DIR / job_id


def save_job(job: dict) -> None:
    path = job_path(job["id"]) / "job.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def public_job(job: dict) -> dict:
    data = dict(job)
    if job["status"] == "done":
        data["video_url"] = f"/jobs/{job['id']}/video"
    return data


def update_job(job_id: str, **fields) -> Optional[dict]:
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            return None
        job.update(fields)
        save_job(job)
        return dict(job)


def load_jobs() -> list[str]:
    """Reload job metadata after a restart; requeue unfinished jobs."""
    pending = []
    for entry in JOBS_DIR.iterdir():
        meta = entry / "job.json"
        if not meta.is_file():
            continue
        try:
            job = json.loads(meta.read_text(encoding="utf-8"))
        except Exception:
            continue
        if job.get("status") in ("queued", "running"):
            job["status"] = "queued"
            job["stage"] = "queued"
            job["progress"] = 0
            job["frame"] = 0
            save_job(job)
            pending.append(job["id"])
        with job_lock:
            jobs[job["id"]] = job
    return pending


def run_job(job_id: str) -> None:
    update_job(job_id, status="running", stage="render", started_at=now())
    with job_lock:
        job = dict(jobs[job_id])
    params = job["params"]
    work = job_path(job_id)
    scene = work / "scene.blend"
    frames = work / "frames"
    video = work / "out.mp4"
    shutil.rmtree(frames, ignore_errors=True)
    frames.mkdir(parents=True, exist_ok=True)

    total = params["end"] - params["start"] + 1
    cmd = [
        BLENDER, "--disable-autoexec", "-b", str(scene), "-P", str(SCRIPT), "--",
        "--out", str(frames),
        "--start", str(params["start"]),
        "--end", str(params["end"]),
        "--fps", str(params["fps"]),
        "--width", str(params["width"]),
        "--height", str(params["height"]),
        "--samples", str(params["samples"]),
        "--device", DEVICE,
    ]

    log_tail: list[str] = []
    started = now()
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1,
    )
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                log_tail.append(line)
                log_tail = log_tail[-30:]
            match = re.search(r"Fra:(\d+)", line)
            if match:
                frame = int(match.group(1))
                done = max(0, min(total, frame - params["start"] + 1))
                pct = int(round(done / total * 92))
                update_job(job_id, frame=frame, progress=max(0, min(92, pct)))
            if now() - started > MAX_RENDER_SECONDS:
                proc.kill()
                raise RuntimeError("render timed out")
        code = proc.wait()
    finally:
        if proc.stdout:
            proc.stdout.close()

    has_frames = any(frames.glob("frame_*.png"))
    if code != 0 or not has_frames:
        detail = "\n".join(log_tail[-10:]) or f"blender exited with {code}"
        update_job(job_id, status="failed", stage="render", error=detail[:2000])
        return

    update_job(job_id, stage="encode", progress=94)
    encode = [
        FFMPEG, "-y", "-framerate", str(params["fps"]),
        "-start_number", str(params["start"]),
        "-i", str(frames / "frame_%04d.png"),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(video),
    ]
    result = subprocess.run(encode, capture_output=True, text=True, timeout=600)
    if result.returncode != 0 or not video.exists():
        err = (result.stderr or "")[-2000:] or "ffmpeg failed"
        update_job(job_id, status="failed", stage="encode", error=err)
        return

    shutil.rmtree(frames, ignore_errors=True)
    update_job(
        job_id, status="done", stage="done", progress=100,
        frame=params["end"], video="out.mp4", finished_at=now(), error=None,
    )


def worker_loop() -> None:
    while True:
        job_id = job_queue.get()
        if job_id is None:
            return
        try:
            run_job(job_id)
        except Exception as exc:  # noqa: BLE001 - worker must survive one bad job
            update_job(job_id, status="failed", stage="error", error=str(exc)[:2000])


@app.on_event("startup")
def on_startup() -> None:
    pending = load_jobs()
    if not TOKEN:
        print("WARNING: RENDER_TOKEN is empty; all requests will be rejected.")
    for job_id in pending:
        job_queue.put(job_id)
    threading.Thread(target=worker_loop, daemon=True).start()


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "blender": shutil.which(BLENDER) is not None,
        "ffmpeg": shutil.which(FFMPEG) is not None,
        "device": DEVICE,
        "queued": job_queue.qsize(),
        "token_configured": bool(TOKEN),
    }


@app.post("/jobs")
async def create_job(
    file: UploadFile = File(...),
    fps: int = Form(24),
    start: int = Form(1),
    end: int = Form(120),
    width: int = Form(1280),
    height: int = Form(720),
    samples: int = Form(64),
    authorization: Optional[str] = Header(default=None),
):
    require_auth(authorization)
    if not file.filename or not file.filename.lower().endswith(".blend"):
        raise HTTPException(status_code=400, detail="only .blend files are accepted")
    if not 1 <= fps <= 60:
        raise HTTPException(status_code=400, detail="fps must be 1-60")
    if start < 0 or end <= start or end - start + 1 > 5000:
        raise HTTPException(status_code=400, detail="invalid frame range")
    if not 16 <= width <= 4096 or not 16 <= height <= 4096:
        raise HTTPException(status_code=400, detail="width/height must be 16-4096")
    if not 1 <= samples <= 1024:
        raise HTTPException(status_code=400, detail="samples must be 1-1024")

    width -= width % 2
    height -= height % 2
    job_id = uuid.uuid4().hex[:12]
    work = job_path(job_id)
    work.mkdir(parents=True)
    target = work / "scene.blend"

    written = 0
    try:
        with target.open("wb") as output:
            while True:
                chunk = await file.read(1 << 20)
                if not chunk:
                    break
                written += len(chunk)
                if written > MAX_UPLOAD:
                    raise HTTPException(status_code=413, detail="file too large")
                output.write(chunk)
    except Exception:
        shutil.rmtree(work, ignore_errors=True)
        raise
    finally:
        await file.close()

    params = {
        "fps": fps, "start": start, "end": end,
        "width": width, "height": height, "samples": samples,
    }
    job = {
        "id": job_id, "status": "queued", "stage": "queued", "progress": 0,
        "frame": 0, "total": end - start + 1, "created_at": now(),
        "filename": file.filename, "size": written, "params": params,
        "error": None, "video": None,
    }
    with job_lock:
        jobs[job_id] = job
        save_job(job)
    job_queue.put(job_id)
    return {"job_id": job_id, "status": "queued", "params": params}


@app.get("/jobs")
def list_jobs(limit: int = 20, authorization: Optional[str] = Header(default=None)):
    require_auth(authorization)
    limit = max(1, min(100, limit))
    with job_lock:
        items = sorted(jobs.values(), key=lambda item: item["created_at"], reverse=True)[:limit]
    return {"jobs": [public_job(item) for item in items]}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, authorization: Optional[str] = Header(default=None)):
    require_auth(authorization)
    with job_lock:
        job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return public_job(dict(job))


@app.get("/jobs/{job_id}/video")
def get_video(job_id: str, authorization: Optional[str] = Header(default=None)):
    require_auth(authorization)
    with job_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        raise HTTPException(status_code=404, detail="video not ready")
    video = job_path(job_id) / "out.mp4"
    if not video.exists():
        raise HTTPException(status_code=404, detail="video missing")
    return FileResponse(video, media_type="video/mp4", filename=f"{job_id}.mp4")


@app.delete("/jobs/{job_id}")
def delete_job(job_id: str, authorization: Optional[str] = Header(default=None)):
    require_auth(authorization)
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="job not found")
        if job["status"] == "running":
            raise HTTPException(status_code=409, detail="job is running")
        jobs.pop(job_id, None)
    shutil.rmtree(job_path(job_id), ignore_errors=True)
    return {"deleted": job_id}
