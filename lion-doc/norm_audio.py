import json, re, subprocess, os, sys

SRC = "/workspace/lion-doc/output"
OUT = os.path.join(SRC, "norm")
os.makedirs(OUT, exist_ok=True)
SHOTS = [f"S{i:02d}" for i in range(1, 11)]
TARGET_I, TARGET_TP, TARGET_LRA = -18.0, -2.0, 11.0

for s in SHOTS:
    src = os.path.join(SRC, f"{s}.mp4")
    dst = os.path.join(OUT, f"{s}.mp4")
    p = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", src, "-map", "0:a:0",
         "-af", f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True)
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
    if not m:
        print(f"{s}: measure failed"); continue
    d = json.loads(m.group(0))
    af = (f"loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}"
          f":measured_I={d['input_i']}:measured_TP={d['input_tp']}"
          f":measured_LRA={d['input_lra']}:measured_thresh={d['input_thresh']}"
          f":offset={d['target_offset']}:linear=true"
          f",aresample=48000,afade=t=in:st=0:d=0.06")
    r = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", src,
         "-map", "0:v:0", "-map", "0:a:0", "-c:v", "copy",
         "-af", af, "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", dst],
        capture_output=True, text=True)
    print(f"{s}: in={d['input_i']} LUFS -> out {'ok' if r.returncode == 0 else r.stderr[-200:]}")
