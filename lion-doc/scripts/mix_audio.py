import subprocess, os, json

OUT = "/workspace/lion-doc/output"
WORK = "/tmp/mixwork"
os.makedirs(WORK, exist_ok=True)
SR = 48000
TOTAL = 82.125
STARTS = {"S01": 0, "S02": 8, "S03": 16, "S04": 24, "S05": 32,
          "S06": 40, "S07": 48, "S08": 56, "S09": 64, "S10": 72}
CLEAN = ["S03", "S05", "S07", "S09", "S10"]          # 无幻觉人声
DIRTY = ["S01", "S02", "S04", "S06", "S08"]          # 已剔除


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("FAIL: " + " ".join(cmd[:6]) + "\n" + r.stderr[-1500:])


# 1) 抽取干净镜头的音轨（用已归一化版本）
for s in CLEAN:
    run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", f"{OUT}/norm/{s}.mp4", "-map", "0:a:0", "-ar", str(SR), "-ac", "2",
         f"{WORK}/{s}_sfx.wav"])

# 2) 连续环境底：S05 与 S09 交替循环 6 轮，压到 -32 LUFS
LIST = []
for i in range(6):
    LIST += [f"file '{WORK}/S05_sfx.wav'", f"file '{WORK}/S09_sfx.wav'"]
open(f"{WORK}/bed_list.txt", "w").write("\n".join(LIST) + "\n")
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
     "-f", "concat", "-safe", "0", "-i", f"{WORK}/bed_list.txt",
     "-t", str(TOTAL), "-af", "volume=-14dB,lowpass=f=7000,afade=t=in:st=0:d=1.5,"
     f"afade=t=out:st={TOTAL - 2}:d=2", f"{WORK}/bed.wav"])

# 3) 干净镜头音效按时间线摆放（S10 咆哮保持力度）
inputs = ["-f", "lavfi", "-t", str(TOTAL), "-i", f"anullsrc=r={SR}:cl=stereo"]
filt = []
idx = 1
for s in ["S03", "S05", "S07", "S09", "S10"]:
    inputs += ["-i", f"{WORK}/{s}_sfx.wav"]
    vol = "-2dB" if s == "S10" else "-7dB"
    filt.append(f"[{idx}:a]adelay={int(STARTS[s] * 1000)}|{int(STARTS[s] * 1000)},"
                f"volume={vol}[s{idx}]")
    idx += 1
mix_in = "[0:a]" + "".join(f"[s{i}]" for i in range(1, idx))
filt.append(mix_in + f"amix=inputs={idx}:duration=first:normalize=0[sfx]")
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs +
    ["-filter_complex", ";".join(filt), "-map", "[sfx]", f"{WORK}/sfx.wav"])

# 4) 旁白按镜头起点 +0.8s 摆放
NAR = {}
inputs = ["-f", "lavfi", "-t", str(TOTAL), "-i", f"anullsrc=r={SR}:cl=stereo"]
filt = []
idx = 1
for s in STARTS:
    inputs += ["-i", f"{OUT}/vo/{s}.wav"]
    ms = int((STARTS[s] + 0.8) * 1000)
    filt.append(f"[{idx}:a]adelay={ms}|{ms},volume=0dB[n{idx}]")
    idx += 1
mix_in = "[0:a]" + "".join(f"[n{i}]" for i in range(1, idx))
filt.append(mix_in + f"amix=inputs={idx}:duration=first:normalize=0[vo]")
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + inputs +
    ["-filter_complex", ";".join(filt), "-map", "[vo]", f"{WORK}/vo.wav"])

# 5) 混音：旁白作 sidechain key，压环境音，再统一响度
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
     "-i", f"{WORK}/bed.wav", "-i", f"{WORK}/sfx.wav", "-i", f"{WORK}/vo.wav",
     "-filter_complex",
     "[0:a][1:a]amix=inputs=2:duration=first:normalize=0[bg];"
     "[2:a]asplit=2[vo][key];"
     "[bg][key]sidechaincompress=threshold=0.025:ratio=8:attack=20:release=450[bgd];"
     "[bgd][vo]amix=inputs=2:duration=first:normalize=0[mix];"
     "[mix]loudnorm=I=-17:TP=-1.5:LRA=11[out]",
     "-map", "[out]", "-ar", str(SR), "-ac", "2", f"{WORK}/final.wav"])

# 6) 与视频合流（视频流直接复制）
run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
     "-i", f"{OUT}/草原之王_82s.mp4", "-i", f"{WORK}/final.wav",
     "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
     "-c:a", "aac", "-b:a", "192k", "-shortest",
     f"{OUT}/草原之王_82s_解说版.mp4"])
print("MIX_OK")
