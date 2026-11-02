import math, os, random, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = "/workspace/donghai-bibao/keyframes/ep01/anim2d"
os.makedirs(OUT, exist_ok=True)
W, H = 760, 1320
CW, CH = 720, 1280
M = 20  # margin for camera shake crop
FPS = 24
DUR = 5.0
N = int(FPS * DUR)
random.seed(7)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): return 0.5 - 0.5 * math.cos(math.pi * clamp(t))
def lerp(a, b, t): return a + (b - a) * clamp(t)

# fonts
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]
def font(sz, mono=False):
    p = FONT_PATHS[1] if mono and os.path.exists(FONT_PATHS[1]) else FONT_PATHS[0]
    try: return ImageFont.truetype(p, sz)
    except Exception: return ImageFont.load_default()

F_UI = font(16)
F_UI_B = font(20)
F_TAG = font(13, mono=True)
F_BIG = font(26, mono=True)

# ---------- persistent particles ----------
smoke = []
for i in range(90):
    smoke.append({
        "x": 380 + random.uniform(-40, 40),
        "y": 1200 + random.uniform(-25, 25),
        "vx": random.uniform(-18, 18),
        "vy": random.uniform(-42, -16),
        "r": random.uniform(8, 26),
        "life": random.uniform(0.0, 2.2),
        "seed": random.uniform(0, 100),
    })

stars = [(random.uniform(0, W), random.uniform(0, H - 120), random.uniform(0.4, 1.0), random.uniform(0, 6.28), random.uniform(0.4, 1.6)) for _ in range(190)]

def background(frame, t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    # vertical gradient
    for y in range(H):
        k = y / H
        col = (int(2 + 5 * k), int(3 + 7 * k), int(10 + 12 * k), 255)
        d.line([(0, y), (W, y)], fill=col)
    # soft nebula band
    neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    nd = ImageDraw.Draw(neb)
    for i in range(6):
        cx = 220 + i * 70
        cy = 380 + i * 30
        nd.ellipse([cx - 260, cy - 90, cx + 260, cy + 90], fill=(22, 40, 70, 10))
    neb = neb.filter(ImageFilter.GaussianBlur(70))
    im = Image.alpha_composite(im, neb)
    # stars
    sd = ImageDraw.Draw(im)
    for x, y, b, ph, sp in stars:
        tw = 0.55 + 0.45 * math.sin(t * sp + ph)
        a = int(150 * b * tw)
        r = 1 if b < 0.8 else 2
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(190, 215, 255, a))
    # horizon / ground silhouette
    d.polygon([(0, H), (0, H - 120), (W, H - 150), (W, H)], fill=(1, 2, 4, 255))
    return im

def draw_hatch(frame, t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 380, 1235
    # concrete rim
    d.ellipse([cx - 235, cy - 95, cx + 235, cy + 95], fill=(31, 35, 42, 255), outline=(70, 78, 90, 255), width=3)
    d.ellipse([cx - 210, cy - 82, cx + 210, cy + 82], fill=(20, 24, 30, 255), outline=(52, 58, 70, 255), width=2)
    # inner pit
    d.ellipse([cx - 170, cy - 62, cx + 170, cy + 62], fill=(5, 7, 10, 255), outline=(38, 44, 55, 255), width=2)
    # doors slide open
    op = ease((t - 0.25) / 1.0)
    door_w = 170 * (1 - op)
    if door_w > 1:
        for s in (-1, 1):
            x0 = cx + s * 4
            x1 = cx + s * (4 + door_w)
            d.polygon([(x0, cy - 58), (x1, cy - 58), (x1, cy + 58), (x0, cy + 58)], fill=(26, 31, 39, 255))
            d.line([(x1, cy - 58), (x1, cy + 58)], fill=(90, 100, 115, 255), width=3)
            for k in range(4):
                yy = cy - 40 + k * 26
                d.line([(min(x0, x1), yy), (max(x0, x1), yy)], fill=(40, 46, 56, 255), width=1)
    # warning lights
    for i in range(8):
        ang = i * math.pi / 4
        lx = cx + 205 * math.cos(ang)
        ly = cy + 70 * math.sin(ang)
        on = 0.5 + 0.5 * math.sin(t * 8 + i * 0.8)
        a = int(120 + 110 * on)
        d.ellipse([lx - 5, ly - 5, lx + 5, ly + 5], fill=(255, 40, 30, a))
    return im

def draw_missile_and_fire(frame, t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rise = ease((t - 0.9) / 3.2)
    base_y = 1215 - 790 * rise
    scale = 1.0 - 0.34 * rise
    bw, bh = 64 * scale, 330 * scale
    cx = 380
    # smoke trail particles (behind body)
    sd = ImageDraw.Draw(im)
    for p in smoke:
        age = (t - p["life"])
        if age < 0: continue
        if age > 2.5: continue
        x = p["x"] + p["vx"] * age + math.sin(age * 2 + p["seed"]) * 4
        y = p["y"] + p["vy"] * age
        r = p["r"] * (0.6 + age * 0.9)
        a = int(150 * max(0, 1 - age / 2.5))
        sd.ellipse([x - r, y - r, x + r, y + r], fill=(120, 125, 132, a))
    # exhaust glow behind body
    if t > 0.9:
        glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for rr, aa in [(86, 35), (56, 70), (30, 130)]:
            gd.ellipse([cx - rr, base_y + bh * 0.5 - rr, cx + rr, base_y + bh * 0.5 + rr], fill=(255, 170, 90, aa))
        glow = glow.filter(ImageFilter.GaussianBlur(22))
        im = Image.alpha_composite(im, glow)
    # body
    d = ImageDraw.Draw(im)
    x0, x1 = cx - bw / 2, cx + bw / 2
    y0, y1 = base_y - bh * 0.5, base_y + bh * 0.5
    d.rounded_rectangle([x0, y0 + 20 * scale, x1, y1], radius=9 * scale, fill=(222, 228, 235, 255), outline=(150, 160, 172, 255), width=2)
    # nose cone
    d.polygon([(x0 + 4 * scale, y0 + 20 * scale), (x1 - 4 * scale, y0 + 20 * scale), (cx, y0 - 16 * scale)], fill=(240, 244, 250, 255), outline=(150, 160, 172, 255))
    # dark bands
    for k in range(3):
        yy = y0 + (80 + k * 72) * scale
        d.rectangle([x0 + 5, yy, x1 - 5, yy + 13 * scale], fill=(44, 50, 60, 255))
    # red stripe
    d.rectangle([x0 + 5, y0 + 205 * scale, x1 - 5, y0 + 219 * scale], fill=(190, 35, 35, 255))
    # small side fins
    d.polygon([(x0, y1 - 38 * scale), (x0 - 22 * scale, y1 - 2 * scale), (x0, y1)], fill=(160, 170, 182, 255))
    d.polygon([(x1, y1 - 38 * scale), (x1 + 22 * scale, y1 - 2 * scale), (x1, y1)], fill=(160, 170, 182, 255))
    # exhaust flame on top of body base
    if t > 0.9:
        flame = 0.55 + 0.45 * math.sin(t * 30) + 0.2 * random.random()
        fl = 95 * scale * flame
        d.polygon([
            (cx - 16 * scale, base_y + bh * 0.5),
            (cx + 16 * scale, base_y + bh * 0.5),
            (cx, base_y + bh * 0.5 + fl)
        ], fill=(255, 220, 150, 235))
        d.polygon([
            (cx - 9 * scale, base_y + bh * 0.5),
            (cx + 9 * scale, base_y + bh * 0.5),
            (cx, base_y + bh * 0.5 + fl * 0.62)
        ], fill=(255, 255, 245, 250))
    return im

def draw_target(frame, t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 380, 255
    # faint halo so the black dot reads against dark sky
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(40, 70, 95, 90))
    d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(0, 0, 0, 255))
    # lock reticle
    pul = 0.5 + 0.5 * math.sin(t * 3)
    r = 44 + 6 * pul
    col = (255, 60, 45, 210)
    d.arc([cx - r, cy - r, cx + r, cy + r], 20, 160, fill=col, width=3)
    d.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=col, width=3)
    # rotating brackets
    a0 = t * 0.8
    for k in range(4):
        a = a0 + k * math.pi / 2
        x = cx + r * 0.92 * math.cos(a)
        y = cy + r * 0.92 * math.sin(a)
        d.line([(x - 8, y), (x + 8, y)], fill=col, width=2)
        d.line([(x, y - 8), (x, y + 8)], fill=col, width=2)
    d.line([(cx - 14, cy), (cx - 5, cy)], fill=col, width=2)
    d.line([(cx + 5, cy), (cx + 14, cy)], fill=col, width=2)
    d.line([(cx, cy - 14), (cx, cy - 5)], fill=col, width=2)
    d.line([(cx, cy + 5), (cx, cy + 14)], fill=col, width=2)
    # lock label
    d.text((cx + 58, cy - 10), "LOCK", font=F_TAG, fill=(255, 90, 70, 230))
    return im

def draw_ui(frame, t):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cyan = (120, 220, 240, 220)
    red = (255, 70, 55, 220)
    # top bar
    d.text((34, 26), "SILO-01 // LAUNCH SEQUENCE", font=F_TAG, fill=cyan)
    d.text((34, 46), "TARGET: UNKNOWN // OPTICAL LOCK", font=F_TAG, fill=(180, 200, 215, 190))
    # top right status
    st = "ARMED" if t < 1.4 else ("LAUNCH" if t < 4.2 else "AWAY")
    d.text((W - 150, 26), st, font=F_UI_B, fill=red if st != "ARMED" else (255, 190, 60, 230))
    # corner brackets
    for x, y, sx, sy in [(24, 24, 1, 1), (W - 24, 24, -1, 1), (24, H - 24, 1, -1), (W - 24, H - 24, -1, -1)]:
        d.line([(x, y), (x + sx * 30, y)], fill=cyan, width=2)
        d.line([(x, y), (x, y + sy * 30)], fill=cyan, width=2)
    # bottom data
    alt = 0 if t < 0.9 else int(1200 * ease((t - 0.9) / 3.2))
    d.text((38, H - 88), f"ALT {alt:04d} m", font=F_UI, fill=cyan)
    d.text((38, H - 62), "VEL 0.0 m/s", font=F_UI, fill=cyan)
    d.text((W - 210, H - 88), "WIND 12 m/s", font=F_UI, fill=(170, 190, 205, 190))
    d.text((W - 210, H - 62), "LINK 98%", font=F_UI, fill=(170, 190, 205, 190))
    # launch warning
    if 0.9 < t < 1.6:
        a = int(180 * (0.5 + 0.5 * math.sin(t * 18)))
        d.rectangle([0, H * 0.44, W, H * 0.44 + 54], fill=(180, 20, 15, a))
        d.text((W / 2 - 96, H * 0.44 + 14), "LAUNCH", font=F_BIG, fill=(255, 245, 235, 255))
    # scanline
    sy = (t * 260) % H
    d.line([(0, sy), (W, sy)], fill=(120, 220, 240, 22), width=2)
    return im

def apply_post(im, frame, t):
    # vignette
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    for i in range(80):
        a = int(140 * (i / 80) ** 2)
        vd.rectangle([i * 3, i * 4, W - i * 3, H - i * 4], outline=a)
    # simpler radial vignette
    yy, xx = np.mgrid[0:H, 0:W]
    dx = (xx - W / 2) / (W / 2)
    dy = (yy - H / 2) / (H / 2)
    r = np.sqrt(dx * dx + dy * dy)
    v = np.clip((r - 0.35) / 0.9, 0, 1) ** 1.6 * 0.55
    arr = np.array(im.convert("RGB")).astype(np.float32)
    arr *= (1.0 - v[..., None])
    # grain
    rng = np.random.default_rng(frame + 99)
    grain = rng.normal(0, 3.0, (H, W, 1))
    arr = np.clip(arr + grain, 0, 255)
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")

def render():
    frames_dir = os.path.join(OUT, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    for f in range(N):
        t = f / FPS
        im = background(f, t)
        im = Image.alpha_composite(im, draw_target(f, t))
        im = Image.alpha_composite(im, draw_missile_and_fire(f, t))
        im = Image.alpha_composite(im, draw_hatch(f, t))
        im = Image.alpha_composite(im, draw_ui(f, t))
        im = apply_post(im, f, t).convert("RGB")
        # camera shake + slow push-in crop
        shake_x = int(2.2 * math.sin(t * 7.3) + 1.2 * math.sin(t * 17.1))
        shake_y = int(1.8 * math.sin(t * 9.1 + 1.0) + 1.0 * math.sin(t * 21.7))
        z = 1.0 + 0.012 * (t / DUR)
        nw, nh = int(CW / z), int(CH / z)
        x0 = int((W - nw) / 2 + shake_x)
        y0 = int((H - nh) / 2 + shake_y)
        x0 = max(0, min(W - nw, x0)); y0 = max(0, min(H - nh, y0))
        im = im.crop((x0, y0, x0 + nw, y0 + nh)).resize((CW, CH), Image.LANCZOS)
        im.save(os.path.join(frames_dir, f"f{f:04d}.jpg"), quality=93)
        if f % 24 == 0: print("frame", f)
    return frames_dir

def audio():
    sr = 44100
    n = int(sr * DUR)
    t = np.arange(n) / sr
    rng = np.random.default_rng(3)
    noise = rng.normal(0, 1, n)
    # low rumble: moving average
    k = 220
    kernel = np.ones(k) / k
    rumble = np.convolve(noise, kernel, mode="same")
    rumble = rumble / (np.max(np.abs(rumble)) + 1e-9)
    # alarm beeps before launch
    alarm = np.zeros(n)
    for start in np.arange(0.0, 3.0, 0.45):
        i0 = int(start * sr); i1 = min(n, i0 + int(0.18 * sr))
        env = np.sin(np.linspace(0, np.pi, i1 - i0)) ** 2
        alarm[i0:i1] += 0.22 * env * np.sin(2 * np.pi * 880 * t[i0:i1])
        alarm[i0:i1] += 0.08 * env * np.sin(2 * np.pi * 1320 * t[i0:i1])
    # launch roar from 1.0s
    launch = np.zeros(n)
    i0 = int(1.0 * sr)
    env = np.clip((t - 1.0) / 1.0, 0, 1)
    launch = 0.55 * env * rumble
    # deep boom at 3.7s
    boom = np.zeros(n)
    i0 = int(3.7 * sr)
    seg = t[i0:] - t[i0]
    boom[i0:] = 0.7 * np.exp(-seg * 7) * np.sin(2 * np.pi * 52 * seg)
    audio = 0.55 * alarm + 0.5 * launch + 0.65 * boom + 0.12 * rumble
    audio = np.clip(audio, -1, 1)
    # fade in/out
    fade = np.ones(n)
    fade[: int(0.15 * sr)] = np.linspace(0, 1, int(0.15 * sr))
    fade[-int(0.25 * sr):] = np.linspace(1, 0, int(0.25 * sr))
    audio *= fade
    pcm = (audio * 32767).astype(np.int16)
    path = os.path.join(OUT, "audio.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(pcm.tobytes())
    return path

if __name__ == "__main__":
    frames = render()
    wav = audio()
    vpath = os.path.join(OUT, "ep01_2d_layered_test_v2.mp4")
    subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", os.path.join(frames, "f%04d.jpg"),
                    "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", vpath], check=True)
    print(vpath)
