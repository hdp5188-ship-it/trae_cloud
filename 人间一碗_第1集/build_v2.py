import subprocess, os, json

BASE = "/workspace/人间一碗_第1集"
os.chdir(BASE)

CLIP = {
    "K": "clips/ep1_01_kitchen_00001_.mp4",
    "T": "clips/ep1_02_linwan_taste_00001_.mp4",
    "X": "clips/ep1_03_xiaozhou_00001_.mp4",
    "L": "clips/ep1b_01_laozhao_00001_.mp4",
    "P": "clips/ep1_04_press_00001_.mp4",
    "S": "clips/ep1_05_suman_toast_00001_.mp4",
    "Q": "clips/ep1b_02_packet_00001_.mp4",
    "R": "clips/ep1b_03_reporters_00001_.mp4",
    "A": "clips/ep1_07_linwan_stand_00001_.mp4",
    "C": "clips/ep1_08_suman_cold_00001_.mp4",
    "V": "clips/ep1b_04_suman_save_00001_.mp4",
    "N": "clips/ep1_06_chen_00001_.mp4",
    "B": "clips/ep1b_05_badge_00001_.mp4",
    "D": "clips/ep1_09_street_00001_.mp4",
    "M": "clips/ep1_10_phone_00001_.mp4",
    "H": "clips/ep1b_06_hotel_00001_.mp4",
}

LINES = {
    "m1": ("林晚（心声）：这不是汤。是盐，加香精。", 3.84),
    "m2": ("小周：林姐，发布会用这个。出餐快，成本低一半。", 4.848),
    "m3": ("苏蔓：我们做的不是生意，是记忆里的那碗汤。", 3.648),
    "m4": ("记者：苏总！有员工爆料，贵司汤底全是料理包！", 4.344),
    "m5": ("林晚：他说得对。我们的汤，是料理包。", 3.84),
    "m6": ("苏蔓：林晚，你被停职了。", 2.472),
    "m7": ("陈启明：林晚，说设备调试失误。听见没有？", 4.488),
    "m8": ("林晚：那我就不检验了。我辞职。", 3.288),
    "m9": ("苏蔓：各位，我们的汤，经得起检验。", 3.432),
    "m10": ("林晚（心声）：陈启明。你连今晚都等不及。", 3.96),
}

# clip, tin, base_dur, zoom, y_bias, line
SEGS = [
    ("R", 1.8, 2.2, 1.30, .15, None),
    ("C", 0.6, 1.4, 1.30, .10, None),
    ("BLACK", 0, 0.9, 1, 0, None),
    ("K", 0.4, 1.6, 1.10, 0, None),
    ("T", 0.6, 2.2, 1.22, .15, "m1"),
    ("X", 0.8, 1.8, 1.15, .10, "m2"),
    ("L", 0.8, 1.5, 1.30, .10, None),
    ("Q", 0.8, 1.6, 1.18, .05, None),
    ("T", 4.6, 1.5, 1.45, .20, None),
    ("K", 2.6, 1.4, 1.18, 0, None),
    ("P", 0.6, 1.6, 1.05, 0, None),
    ("S", 0.8, 2.2, 1.18, .10, "m3"),
    ("R", 0.8, 1.4, 1.20, .10, None),
    ("R", 2.8, 2.2, 1.38, .12, "m4"),
    ("A", 0.6, 1.6, 1.12, .10, None),
    ("C", 2.2, 1.3, 1.32, .10, None),
    ("A", 3.2, 1.6, 1.20, .15, "m5"),
    ("C", 3.4, 1.3, 1.35, .10, "m6"),
    ("N", 0.8, 1.6, 1.18, .10, "m7"),
    ("B", 1.6, 1.4, 1.18, .15, None),
    ("B", 3.0, 2.0, 1.40, .18, "m8"),
    ("V", 1.4, 1.4, 1.18, .10, "m9"),
    ("R", 4.8, 1.3, 1.28, .10, None),
    ("C", 5.2, 1.3, 1.40, .10, None),
    ("D", 0.8, 1.6, 1.08, 0, None),
    ("M", 1.2, 2.0, 1.12, 0, None),
    ("H", 0.8, 1.4, 1.08, 0, None),
    ("H", 3.6, 1.8, 1.40, .15, None),
    ("H", 3.5, 1.3, 1.18, .05, "m10"),
    ("BLACK", 0, 1.4, 1, 0, None),
]

# compute durations and start times
segs = []
t = 0.0
line_pos = {}
for clip, tin, base, zoom, yb, line in SEGS:
    dur = base * 1.6
    if line:
        dur = max(dur, LINES[line][1] + 0.55)
    if clip != "BLACK":
        dur = min(dur, 8.0 - tin - 0.05)
    t0 = t
    if line:
        line_pos[line] = t0 + 0.25
    segs.append((clip, tin, dur, zoom, yb, line, t0))
    t += dur
TOTAL = t
print("TOTAL", round(TOTAL, 2))
for s in segs:
    print(s[0], round(s[6], 2), round(s[2], 2))

# ---------------- inputs ----------------
inputs = []
idx = 0
def add(*args):
    global idx
    inputs.extend(args)
    i = idx
    idx += 1
    return i

vin_idx = {}
for name, path in CLIP.items():
    vin_idx[name] = add("-i", path)
color_title = add("-f", "lavfi", "-i", "color=c=black:s=640x1152:r=24:d=2")
color_end = add("-f", "lavfi", "-i", "color=c=black:s=640x1152:r=24:d=2")
tts_idx = {}
for k in [f"m{i}" for i in range(1, 11)]:
    tts_idx[k] = add("-i", f"tts2/{k}.mp3")
noise_i = add("-f", "lavfi", "-i", f"anoisesrc=d={TOTAL+1}:c=pink:a=0.5")
sine_i = add("-f", "lavfi", "-i", f"sine=f=52:d={TOTAL+1}")

fc = []
vlabels = []
for i, (clip, tin, dur, zoom, yb, line, t0) in enumerate(segs):
    lab = f"v{i}"
    vlabels.append(f"[{lab}]")
    if clip == "BLACK":
        src = color_title if i < 10 else color_end
        fc.append(f"[{src}:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS,scale=640:1152,setsar=1,fps=24[{lab}]")
    else:
        idx = vin_idx[clip]
        fc.append(
            f"[{idx}:v]trim=start={tin}:duration={dur:.3f},setpts=PTS-STARTPTS,"
            f"scale=640:1152:force_original_aspect_ratio=increase,crop=640:1152,"
            f"crop=iw/{zoom}:ih/{zoom}:(iw-iw/{zoom})/2:(ih-ih/{zoom})*{yb},"
            f"scale=640:1152,setsar=1,fps=24[{lab}]"
        )

fc.append("".join(vlabels) + f"concat=n={len(segs)}:v=1:a=0,"
          f"eq=contrast=1.05:saturation=1.02:brightness=0.005,"
          f"subtitles=字幕_v2.ass:fontsdir=/usr/share/fonts[vout]")

# audio
mix = []
fc.append(f"[{noise_i}:a]asplit=6[namb][ns0][ns1][ns2][ns3][ns4]")
fc.append(f"[namb]lowpass=f=240,volume=0.05,atrim=0:{TOTAL:.3f},asetpts=N/SR/TB[amb]")
mix.append("[amb]")

fc.append(f"[{tts_idx['m4']}:a]asplit=2[m4x][m4y]")
for k, (txt, d) in LINES.items():
    st = int(line_pos[k] * 1000)
    src = "[m4x]" if k == "m4" else f"[{tts_idx[k]}:a]"
    fc.append(f"{src}adelay={st}|{st},volume=2.2[{k}]")
    mix.append(f"[{k}]")

mix.append("[m4b]")
fc.append("[m4y]adelay=200|200,volume=2.2[m4b]")

whoosh_times = [3.55, 20.0, 27.95, 34.25, 41.85]
whoosh_labels = []
for j, wt in enumerate(whoosh_times):
    st = int(wt * 1000)
    fc.append(f"[ns{j}]highpass=f=350,lowpass=f=5000,volume=0.30,"
              f"afade=t=out:st=0.32:d=0.12,atrim=0:0.45,asetpts=N/SR/TB,adelay={st}|{st}[w{j}]")
    whoosh_labels.append(f"[w{j}]")
    mix.append(f"[w{j}]")

impact_times = [3.5, TOTAL - 1.35]
for j, it in enumerate(impact_times):
    st = int(it * 1000)
    fc.append(f"[{sine_i}:a]volume=0.22,afade=t=out:st=0.05:d=0.55,"
              f"atrim=0:0.7,asetpts=N/SR/TB,adelay={st}|{st}[imp{j}]")
    mix.append(f"[imp{j}]")

fc.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,"
          f"alimiter=limit=0.95[aout]")

filt = ";".join(fc)
with open("filter_v2.txt", "w") as f:
    f.write(filt)

cmd = ["ffmpeg", "-y"] + inputs + ["-filter_complex", filt,
       "-map", "[vout]", "-map", "[aout]", "-t", f"{TOTAL:.3f}",
       "-c:v", "libx264", "-crf", "19", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "24",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
       "人间一碗_第1集_重剪版.mp4"]

# ---------------- subtitles ----------------
def ts(x):
    h = int(x // 3600); m = int((x % 3600) // 60); s = int(x % 60); cs = int(round((x - int(x)) * 100))
    if cs == 100:
        s += 1; cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

rows = []
for clip, tin, dur, zoom, yb, line, t0 in segs:
    if line:
        txt, d = LINES[line]
        rows.append(f"Dialogue: 0,{ts(line_pos[line])},{ts(line_pos[line]+d+0.15)},Default,,0,0,0,,{txt}")

first = segs[0][6]
title_start = segs[2][6]
title_end = title_start + segs[2][2]
rows.insert(0, f"Dialogue: 0,{ts(title_start+0.05)},{ts(title_end-0.05)},Title,,0,0,0,,人间一碗")
rows.insert(1, f"Dialogue: 0,{ts(title_start+0.35)},{ts(title_end-0.05)},Small,,0,0,0,,第 1 集")

rows.insert(2, f"Dialogue: 0,{ts(0.2)},{ts(0.2+LINES['m4'][1]+0.15)},Default,,0,0,0,,{LINES['m4'][0]}")

def seg_t(i):
    return segs[i][6]

rows.append(f"Dialogue: 0,{ts(seg_t(3)+0.05)},{ts(seg_t(3)+2.0)},Caption,,0,0,0,,味知集团 · 中央厨房")
rows.append(f"Dialogue: 0,{ts(seg_t(10)+0.05)},{ts(seg_t(10)+2.2)},Caption,,0,0,0,,三小时后 · 新品发布会")
rows.append(f"Dialogue: 0,{ts(seg_t(24)+0.05)},{ts(seg_t(24)+1.8)},Caption,,0,0,0,,傍晚 · 同福巷")
rows.append(f"Dialogue: 0,{ts(seg_t(25)+0.05)},{ts(seg_t(25)+2.0)},Default,,0,0,0,,短信：你老公今晚八点，\\N云顶酒店1808。")
rows.append(f"Dialogue: 0,{ts(seg_t(26)+0.05)},{ts(seg_t(26)+2.2)},Caption,,0,0,0,,同一时间 · 云顶酒店")
rows.append(f"Dialogue: 0,{ts(seg_t(29)+0.1)},{ts(TOTAL)},End,,0,0,0,,第 1 集 · 完")

head = """[Script Info]
ScriptType: v4.00+
PlayResX: 640
PlayResY: 1152
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Noto Sans CJK SC,33,&H00FFFFFF,&H000000FF,&H00000000,&H90000000,-1,0,0,0,100,100,1,0,1,3,1,2,36,36,150,1
Style: Title,Noto Serif CJK SC,62,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,4,0,5,40,40,0,1
Style: Small,Noto Sans CJK SC,27,&H00DDDDDD,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,2,0,2,60,60,120,1
Style: Caption,Noto Sans CJK SC,29,&H00E6E6E6,&H000000FF,&H00000000,&H70000000,0,0,0,0,100,100,2,0,1,2,1,8,40,40,120,1
Style: End,Noto Serif CJK SC,44,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,3,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with open("字幕_v2.ass", "w") as f:
    f.write(head + "\n".join(rows) + "\n")

print("DONE", TOTAL)
subprocess.run(cmd, check=True)
