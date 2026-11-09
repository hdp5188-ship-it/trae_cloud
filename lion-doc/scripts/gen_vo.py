import asyncio, os, subprocess, edge_tts, json

OUT = "/root/autodl-tmp/vo"
os.makedirs(OUT, exist_ok=True)
VOICE, RATE, PITCH = "zh-CN-YunjianNeural", "-10%", "-4Hz"

LINES = [
    ("S01", "夜色退去，东非草原迎来第一缕光。"),
    ("S02", "它叫疤面，六岁，正是狮子的盛年。"),
    ("S03", "这样的凝视只意味着一件事——狩猎季开始了。"),
    ("S04", "十一口之家，狩猎靠母狮，守护靠它。"),
    ("S05", "猎手塔莉，每一步都踩在风的缝隙里。"),
    ("S06", "六十公里的冲刺，只换三秒钟的机会。"),
    ("S07", "草原最柔软的地方，藏在这些小爪子里。"),
    ("S08", "日落之后，鬣狗来了。王必须挺身而出。"),
    ("S09", "危机退去，夜晚安静得像战后的海。"),
    ("S10", "这一声传出去八公里。它在告诉草原：我还在。"),
]

async def gen(name, text):
    mp3 = f"{OUT}/{name}.mp3"
    await edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).save(mp3)
    wav = f"{OUT}/{name}.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mp3,
                    "-ar", "48000", "-ac", "1", wav], check=True)
    return round(float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", wav], capture_output=True, text=True).stdout.strip()), 2)

async def main():
    res = {}
    for n, t in LINES:
        res[n] = await gen(n, t)
        print(f"{n} {res[n]}s {t}", flush=True)
    json.dump(res, open(f"{OUT}/durations.json", "w"), ensure_ascii=False, indent=1)

asyncio.run(main())
print("VO_DONE")
