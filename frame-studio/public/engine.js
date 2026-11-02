const TAU = Math.PI * 2;

export const EFFECTS = [
  {
    id: 'push', label: '推近', group: 'motion',
    keywords: ['推近', '推进', '推镜头', '拉近', '放大', 'zoom in', 'push in', 'dolly in'],
  },
  {
    id: 'pull', label: '拉远', group: 'motion',
    keywords: ['拉远', '后拉', '缩小', '远推', 'zoom out', 'pull back', 'dolly out'],
  },
  {
    id: 'panLeft', label: '左摇', group: 'motion',
    keywords: ['左摇', '向左', '左移', 'pan left', 'pan-left'],
  },
  {
    id: 'panRight', label: '右摇', group: 'motion',
    keywords: ['右摇', '向右', '右移', 'pan right', 'pan-right'],
  },
  {
    id: 'tiltUp', label: '上摇', group: 'motion',
    keywords: ['上摇', '向上', '上移', '抬镜', 'tilt up'],
  },
  {
    id: 'tiltDown', label: '下摇', group: 'motion',
    keywords: ['下摇', '向下', '下移', '俯拍', 'tilt down'],
  },
  {
    id: 'rotate', label: '旋转', group: 'motion',
    keywords: ['旋转', '转动', '翻滚', '倾斜', 'rotate', 'roll'],
  },
  {
    id: 'shake', label: '手持晃动', group: 'motion',
    keywords: ['晃动', '抖动', '手持', '震颤', 'shake', 'handheld'],
  },
  {
    id: 'breathe', label: '呼吸感', group: 'motion',
    keywords: ['呼吸', '脉动', '心跳', 'breathe', 'pulse', 'breathing'],
  },
  {
    id: 'drift', label: '漂浮', group: 'motion',
    keywords: ['漂移', '漂浮', '缓动', '游动', 'drift', 'float'],
  },
  {
    id: 'orbit', label: '环绕', group: 'motion',
    keywords: ['环绕', '旋转视角', '绕行', 'orbit', 'parallax'],
  },
  {
    id: 'blur', label: '拖影', group: 'motion',
    keywords: ['拖影', '残影', '速度感', '动感', 'motion blur', 'speed'],
  },
  {
    id: 'rain', label: '雨', group: 'weather',
    keywords: ['下雨', '雨滴', '雨夜', '暴雨', 'rain', 'storm'],
  },
  {
    id: 'snow', label: '雪', group: 'weather',
    keywords: ['下雪', '飘雪', '雪花', 'snow'],
  },
  {
    id: 'fog', label: '雾', group: 'weather',
    keywords: ['雾', '烟', '朦胧', 'mist', 'fog', 'haze'],
  },
  {
    id: 'dust', label: '光尘', group: 'weather',
    keywords: ['尘埃', '灰尘', '粒子', '星尘', '光尘', '光斑', 'dust', 'particles', 'bokeh'],
  },
  {
    id: 'rays', label: '光束', group: 'light',
    keywords: ['光束', '丁达尔', '耶稣光', '阳光', '逆光', '光晕', 'god rays', 'sunbeam', 'glow'],
  },
  {
    id: 'neon', label: '霓虹', group: 'light',
    keywords: ['霓虹', '赛博', 'cyberpunk', 'neon', '电子'],
  },
  {
    id: 'glitch', label: '故障', group: 'stylize',
    keywords: ['故障', '扫描线', '像素', 'glitch', 'scanline', 'vhs'],
  },
  {
    id: 'flicker', label: '闪烁', group: 'light',
    keywords: ['闪烁', '忽明忽暗', '灯光闪烁', 'flicker', 'strobe'],
  },
  {
    id: 'ripple', label: '水波', group: 'stylize',
    keywords: ['水波', '涟漪', '波动', '扭曲', '热浪', 'ripple', 'wave'],
  },
  {
    id: 'grain', label: '胶片颗粒', group: 'stylize',
    keywords: ['胶片', '颗粒', '做旧', 'film grain', 'grain'],
  },
  {
    id: 'warm', label: '暖调', group: 'grade',
    keywords: ['暖', '夕阳', '黄昏', '日落', 'golden', 'warm'],
  },
  {
    id: 'cool', label: '冷调', group: 'grade',
    keywords: ['冷', '蓝调', '蓝光', 'blue', 'cool'],
  },
  {
    id: 'mono', label: '黑白', group: 'grade',
    keywords: ['黑白', '单色', 'monochrome', 'black and white', 'grayscale'],
  },
  {
    id: 'contrasty', label: '高对比', group: 'grade',
    keywords: ['高对比', '暗黑', '电影感', 'cinematic', 'dramatic'],
  },
  {
    id: 'dreamy', label: '柔光', group: 'grade',
    keywords: ['梦幻', '柔光', '唯美', 'dreamy', 'soft light'],
  },
  {
    id: 'vintage', label: '复古', group: 'grade',
    keywords: ['复古', '怀旧', 'vintage', 'retro'],
  },
  {
    id: 'night', label: '夜色', group: 'grade',
    keywords: ['夜晚', '夜景', '夜色', 'night'],
  },
];

const STRONG = /强烈|剧烈|大幅|夸张|猛烈|强烈地/;
const FAST = /快速|急速|加速|飞快|迅速/;
const GENTLE = /轻微|微微|缓慢|轻柔|缓缓|细腻|微妙|淡淡/;
const ONE_SHOT = /不循环|单次|一次性|不回环|one-shot|no loop|no-loop/;

export function parsePrompt(prompt = '') {
  const text = String(prompt).toLowerCase();
  const ids = [];
  for (const effect of EFFECTS) {
    if (effect.keywords.some((k) => text.includes(k.toLowerCase()))) ids.push(effect.id);
  }
  const intensity = STRONG.test(text) ? 1.5 : GENTLE.test(text) ? 0.68 : 1;
  const speed = FAST.test(text) ? 1.45 : GENTLE.test(text) ? 0.72 : 1;
  const loop = !ONE_SHOT.test(text);
  return {
    ids,
    intensity,
    speed,
    loop,
    labels: EFFECTS.filter((e) => ids.includes(e.id)).map((e) => e.label),
  };
}

function clamp(v, min, max) {
  return Math.min(max, Math.max(min, v));
}

function mulberry32(seed) {
  let a = seed >>> 0;
  return function random() {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeCanvas(width, height) {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  return canvas;
}

export class FrameRenderer {
  constructor({ image, keyframes = null, width = 1280, height = 720, effects = [], intensity = 1, speed = 1, frameCount = 48, fps = 12, loop = true, seed = 7 }) {
    this.image = image;
    this.keyframes = keyframes && keyframes.length > 1 ? keyframes : null;
    this.width = width;
    this.height = height;
    this.effects = new Set(effects);
    this.has = (id) => this.effects.has(id);
    this.intensity = intensity;
    this.speed = speed;
    this.frameCount = Math.max(2, Math.min(400, frameCount));
    this.fps = Math.max(1, Math.min(60, fps));
    this.loop = loop;
    this.seed = seed;

    this.stage = makeCanvas(width, height);
    this.glow = this.buildGlow();
    this.noise = this.buildNoise();

    const rand = mulberry32(seed);
    this.particles = this.buildParticles(rand);
    this.sliceSeed = mulberry32(seed + 977);
  }

  buildGlow() {
    const size = 64;
    const c = makeCanvas(size, size);
    const ctx = c.getContext('2d');
    const g = ctx.createRadialGradient(size / 2, size / 2, 0, size / 2, size / 2, size / 2);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.35, 'rgba(255,255,255,0.55)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, size, size);
    return c;
  }

  buildNoise() {
    const size = 160;
    const c = makeCanvas(size, size);
    const ctx = c.getContext('2d');
    const img = ctx.createImageData(size, size);
    const rand = mulberry32(this.seed + 31);
    for (let i = 0; i < img.data.length; i += 4) {
      const v = Math.floor(rand() * 255);
      img.data[i] = v;
      img.data[i + 1] = v;
      img.data[i + 2] = v;
      img.data[i + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
    return c;
  }

  buildParticles(rand) {
    const rain = [];
    for (let i = 0; i < 150; i++) {
      rain.push({ x: rand(), y: rand(), speed: 1 + rand() * 2, len: 0.045 + rand() * 0.09, alpha: 0.18 + rand() * 0.45 });
    }
    const snow = [];
    for (let i = 0; i < 90; i++) {
      snow.push({ x: rand(), y: rand(), speed: 0.35 + rand() * 0.65, r: 0.8 + rand() * 3.4, alpha: 0.3 + rand() * 0.55, phase: rand() * TAU, sway: 0.01 + rand() * 0.03 });
    }
    const dust = [];
    for (let i = 0; i < 55; i++) {
      dust.push({ x: rand(), y: rand(), r: 0.004 + rand() * 0.02, alpha: 0.08 + rand() * 0.3, phase: rand() * TAU, speed: 0.2 + rand() * 0.5 });
    }
    return { rain, snow, dust };
  }

  setEffects(effects) {
    this.effects = new Set(effects);
  }

  get duration() {
    return this.frameCount / this.fps;
  }

  phase(index) {
    if (this.keyframes) return this.frameCount > 1 ? index / (this.frameCount - 1) : 0;
    if (this.loop) return index / this.frameCount;
    return this.frameCount > 1 ? index / (this.frameCount - 1) : 0;
  }

  motion(p) {
    const e = this.has;
    const a = this.intensity;
    const sp = this.speed;
    const q = p * sp;
    const smooth = 0.5 - 0.5 * Math.cos(TAU * q);
    let scale = 1;
    let tx = 0;
    let ty = 0;
    let rot = 0;

    if (e('push')) scale *= 1 + 0.115 * a * smooth;
    if (e('pull')) scale *= 1 + 0.115 * a * (1 - smooth);
    if (e('panLeft')) tx += 0.055 * a * smooth;
    if (e('panRight')) tx -= 0.055 * a * smooth;
    if (e('tiltUp')) ty += 0.04 * a * smooth;
    if (e('tiltDown')) ty -= 0.04 * a * smooth;
    if (e('rotate')) rot += (1.4 * a * Math.PI / 180) * Math.sin(TAU * q);
    if (e('shake')) {
      tx += 0.0075 * a * Math.sin(TAU * q * 9 + 0.6);
      ty += 0.0065 * a * Math.sin(TAU * q * 7 + 2.1);
      rot += (0.3 * a * Math.PI / 180) * Math.sin(TAU * q * 11 + 1.2);
    }
    if (e('breathe')) scale *= 1 + 0.022 * a * Math.sin(TAU * q);
    if (e('drift')) {
      tx += 0.022 * a * Math.sin(TAU * q);
      ty += 0.016 * a * Math.sin(TAU * q + Math.PI / 2);
    }
    if (e('orbit')) {
      tx += 0.038 * a * Math.sin(TAU * q);
      ty += 0.024 * a * Math.sin(TAU * q + Math.PI / 2);
      rot += (0.7 * a * Math.PI / 180) * Math.sin(TAU * q);
    }
    return { scale, tx, ty, rot };
  }

  filterString(p) {
    const e = this.has;
    const parts = [];
    if (e('mono')) parts.push('grayscale(1)');
    if (e('warm')) parts.push('sepia(0.18)', 'saturate(1.22)', 'hue-rotate(-6deg)');
    if (e('cool')) parts.push('saturate(0.92)', 'hue-rotate(12deg)');
    if (e('night')) parts.push('brightness(0.78)', 'contrast(1.06)', 'saturate(0.92)');
    if (e('contrasty')) parts.push('contrast(1.16)', 'saturate(1.08)');
    if (e('dreamy')) parts.push('saturate(1.05)', 'contrast(0.94)', 'brightness(1.04)');
    if (e('vintage')) parts.push('sepia(0.22)', 'saturate(0.82)', 'contrast(0.96)');
    if (e('flicker')) parts.push(`brightness(${1 + 0.07 * Math.sin(TAU * p * 6)})`);
    return parts.length ? parts.join(' ') : 'none';
  }

  drawCover(ctx, img) {
    const iw = img.naturalWidth || img.width;
    const ih = img.naturalHeight || img.height;
    if (!iw || !ih) return;
    const s = Math.max(this.width / iw, this.height / ih);
    const dw = iw * s;
    const dh = ih * s;
    ctx.drawImage(img, -dw / 2, -dh / 2, dw, dh);
  }

  drawBase(p) {
    const { width: w, height: h, stage } = this;
    const ctx = stage.getContext('2d');
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = '#05060a';
    ctx.fillRect(0, 0, w, h);

    const m = this.motion(p);
    const baseScale = Math.max(1.1 + Math.abs(m.rot) * 0.9, 1 + Math.abs(m.tx) * 2.4, 1 + Math.abs(m.ty) * 2.4);
    const safeX = ((baseScale - 1) / 2) * 0.94;
    const safeY = ((baseScale - 1) / 2) * 0.94;
    const tx = clamp(m.tx, -safeX, safeX) * w;
    const ty = clamp(m.ty, -safeY, safeY) * h;

    ctx.save();
    ctx.translate(w / 2 + tx, h / 2 + ty);
    ctx.rotate(m.rot);
    ctx.scale(baseScale * m.scale, baseScale * m.scale);
    ctx.filter = this.filterString(p);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    if (this.keyframes) {
      const kf = this.keyframes;
      const last = kf.length - 1;
      const pos = p * last;
      const i0 = Math.min(last, Math.floor(pos));
      const i1 = Math.min(last, i0 + 1);
      const t = pos - i0;
      const easeT = t * t * (3 - 2 * t);
      ctx.globalAlpha = 1 - easeT;
      this.drawCover(ctx, kf[i0]);
      if (i1 !== i0 && easeT > 0) {
        ctx.globalAlpha = easeT;
        ctx.save();
        const drift = 0.012 * this.intensity;
        ctx.translate(drift * w * (1 - 2 * easeT) * 0.3, 0);
        ctx.scale(1.015, 1.015);
        this.drawCover(ctx, kf[i1]);
        ctx.restore();
      }
      ctx.globalAlpha = 1;
    } else {
      this.drawCover(ctx, this.image);
    }
    ctx.restore();
    ctx.filter = 'none';
  }

  composite(ctx, p, index) {
    const { width: w, height: h, stage } = this;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.globalCompositeOperation = 'source-over';
    ctx.globalAlpha = 1;
    ctx.filter = 'none';

    if (this.has('ripple')) {
      const bandH = 5;
      const amp = 0.009 * this.intensity * w;
      for (let y = 0; y < h; y += bandH) {
        const dx = Math.sin((y / h) * Math.PI * 7 + TAU * p) * amp;
        ctx.drawImage(stage, 0, y, w, bandH, dx, y, w, bandH + 1);
      }
    } else {
      ctx.drawImage(stage, 0, 0);
    }

    if (this.has('blur')) {
      const strength = 0.012 * this.intensity;
      ctx.globalCompositeOperation = 'source-over';
      for (let i = 1; i <= 2; i++) {
        const off = i * strength * (w / 2) * (1 + 0.2 * i);
        ctx.globalAlpha = 0.16 / i;
        ctx.drawImage(stage, off, 0);
        ctx.globalAlpha = 0.1 / i;
        ctx.drawImage(stage, -off, 0);
      }
      ctx.globalAlpha = 1;
    }

    if (this.has('glitch') && index % 3 !== 0) {
      const rand = this.sliceSeed;
      for (let s = 0; s < 4; s++) {
        const sy = Math.floor((0.15 + 0.7 * rand()) * h);
        const sh = Math.floor((0.04 + 0.06 * rand()) * h);
        const dx = (rand() - 0.5) * 0.09 * w * this.intensity;
        ctx.drawImage(stage, 0, sy, w, sh, dx, sy, w, sh);
      }
    }

    if (this.has('neon')) {
      ctx.globalCompositeOperation = 'screen';
      ctx.globalAlpha = 0.18;
      ctx.drawImage(stage, 3, 0);
      ctx.globalCompositeOperation = 'source-over';
      ctx.globalAlpha = 1;
      const g = ctx.createLinearGradient(0, 0, w, h);
      g.addColorStop(0, 'rgba(0,220,255,0.16)');
      g.addColorStop(0.5, 'rgba(20,0,60,0.05)');
      g.addColorStop(1, 'rgba(255,0,180,0.2)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
    }
  }

  drawGrain(ctx, index) {
    const { width: w, height: h } = this;
    const pattern = ctx.createPattern(this.noise, 'repeat');
    if (!pattern) return;
    const rand = this.sliceSeed;
    ctx.save();
    ctx.globalCompositeOperation = 'overlay';
    ctx.globalAlpha = this.has('vintage') ? 0.14 : 0.08;
    ctx.translate(-Math.floor(rand() * 100), -Math.floor(rand() * 100));
    ctx.fillStyle = pattern;
    ctx.fillRect(0, 0, w + 100, h + 100);
    ctx.restore();
    ctx.globalAlpha = 1;
  }

  drawFog(ctx, p) {
    const { width: w, height: h } = this;
    const count = 5;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    for (let i = 0; i < count; i++) {
      const ph = i * 1.37;
      const cx = (0.2 + 0.6 * ((i / count + 0.12 * Math.sin(TAU * p + ph) + 1) % 1)) * w;
      const cy = (0.35 + 0.4 * Math.cos(TAU * p + ph)) * h;
      const r = (0.28 + 0.14 * Math.sin(ph)) * Math.max(w, h);
      const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, r);
      g.addColorStop(0, `rgba(210,225,245,${0.1 * this.intensity})`);
      g.addColorStop(1, 'rgba(210,225,245,0)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, w, h);
    }
    ctx.restore();
  }

  drawRays(ctx, p) {
    const { width: w, height: h } = this;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    const count = 6;
    for (let i = 0; i < count; i++) {
      const angle = -0.55 + i * 0.16 + 0.03 * Math.sin(TAU * p + i);
      const alpha = (0.24 + 0.12 * Math.sin(TAU * p * 2 + i * 1.2)) * this.intensity;
      ctx.save();
      ctx.translate(w * (0.78 + 0.05 * Math.sin(TAU * p + i)), -h * 0.1);
      ctx.rotate(angle);
      const grad = ctx.createLinearGradient(0, 0, 0, h * 1.5);
      grad.addColorStop(0, `rgba(255,240,205,${alpha})`);
      grad.addColorStop(0.55, `rgba(255,225,180,${alpha * 0.35})`);
      grad.addColorStop(1, 'rgba(255,220,170,0)');
      ctx.fillStyle = grad;
      ctx.fillRect(-w * 0.08, 0, w * 0.16, h * 1.5);
      ctx.restore();
    }
    ctx.restore();
  }

  drawRain(ctx, p) {
    const { width: w, height: h } = this;
    const parts = this.particles.rain;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    ctx.lineCap = 'round';
    for (const drop of parts) {
      const y = ((drop.y + p * drop.speed * 5) % 1) * (h + 40) - 20;
      const x = ((drop.x + p * 0.06 * drop.speed) % 1) * w;
      const len = drop.len * h * 0.5;
      ctx.strokeStyle = `rgba(190,215,245,${drop.alpha})`;
      ctx.lineWidth = Math.max(0.8, w * 0.0012);
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x - len * 0.22, y + len);
      ctx.stroke();
    }
    ctx.restore();
  }

  drawSnow(ctx, p) {
    const { width: w, height: h } = this;
    const parts = this.particles.snow;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    for (const flake of parts) {
      const y = ((flake.y + p * flake.speed * 2) % 1) * (h + 30) - 15;
      const x = (flake.x + Math.sin(TAU * (p * 2 + flake.phase)) * flake.sway) * w;
      const r = flake.r * (w / 1280) * 1.8;
      ctx.globalAlpha = flake.alpha;
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(x, y, Math.max(0.8, r), 0, TAU);
      ctx.fill();
    }
    ctx.restore();
    ctx.globalAlpha = 1;
  }

  drawDust(ctx, p) {
    const { width: w, height: h } = this;
    const parts = this.particles.dust;
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    for (const d of parts) {
      const y = ((d.y - p * d.speed * 0.9 + 1) % 1) * h;
      const x = (d.x + Math.sin(TAU * (p * 1 + d.phase)) * 0.03) * w;
      const r = Math.max(6, d.r * Math.max(w, h));
      ctx.globalAlpha = d.alpha * this.intensity;
      ctx.drawImage(this.glow, x - r, y - r, r * 2, r * 2);
    }
    ctx.restore();
    ctx.globalAlpha = 1;
  }

  drawScanlines(ctx) {
    const { width: w, height: h } = this;
    ctx.save();
    ctx.globalCompositeOperation = 'multiply';
    ctx.fillStyle = 'rgba(120,140,170,0.16)';
    const step = Math.max(3, Math.round(h / 200));
    for (let y = 0; y < h; y += step) ctx.fillRect(0, y, w, 1);
    ctx.restore();
  }

  drawVignette(ctx, strength = 0.42) {
    const { width: w, height: h } = this;
    const g = ctx.createRadialGradient(w / 2, h / 2, Math.min(w, h) * 0.36, w / 2, h / 2, Math.max(w, h) * 0.78);
    g.addColorStop(0, 'rgba(0,0,0,0)');
    g.addColorStop(0.65, 'rgba(0,0,0,0.12)');
    g.addColorStop(1, `rgba(0,0,0,${strength})`);
    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    ctx.restore();
  }

  drawDreamy(ctx) {
    const { width: w, height: h } = this;
    const g = ctx.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, Math.max(w, h) * 0.7);
    g.addColorStop(0, 'rgba(255,248,240,0.16)');
    g.addColorStop(1, 'rgba(255,248,240,0)');
    ctx.save();
    ctx.globalCompositeOperation = 'screen';
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    ctx.restore();
  }

  drawOverlays(ctx, p, index) {
    const { width: w, height: h } = this;
    const e = this.has;

    if (e('warm')) {
      ctx.save();
      ctx.globalCompositeOperation = 'overlay';
      ctx.fillStyle = 'rgba(255,146,58,0.12)';
      ctx.fillRect(0, 0, w, h);
      ctx.restore();
    }
    if (e('cool') || e('night')) {
      ctx.save();
      ctx.globalCompositeOperation = 'overlay';
      ctx.fillStyle = e('night') ? 'rgba(22,40,110,0.26)' : 'rgba(58,116,240,0.14)';
      ctx.fillRect(0, 0, w, h);
      ctx.restore();
    }
    if (e('fog')) this.drawFog(ctx, p);
    if (e('rays')) this.drawRays(ctx, p);
    if (e('dreamy')) this.drawDreamy(ctx);
    if (e('dust')) this.drawDust(ctx, p);
    if (e('rain')) this.drawRain(ctx, p);
    if (e('snow')) this.drawSnow(ctx, p);
    if (e('glitch')) this.drawScanlines(ctx);
    if (e('grain') || e('vintage')) this.drawGrain(ctx, index);

    if (e('flicker')) {
      const f = Math.max(0, Math.sin(TAU * p * 6));
      ctx.save();
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = `rgba(0,0,0,${0.1 * f})`;
      ctx.fillRect(0, 0, w, h);
      ctx.restore();
    }

    this.drawVignette(ctx, e('contrasty') ? 0.5 : e('night') ? 0.48 : 0.34);
  }

  render(ctx, index) {
    const p = this.phase(index);
    this.drawBase(p);
    this.composite(ctx, p, index);
    this.drawOverlays(ctx, p, index);
    return ctx;
  }
}

export function analyzePrompt(prompt, { width, height } = {}) {
  const parsed = parsePrompt(prompt);
  return {
    ...parsed,
    aspect: width && height ? width / height : 16 / 9,
  };
}
