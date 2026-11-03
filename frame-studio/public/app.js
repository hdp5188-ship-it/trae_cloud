import { FrameRenderer, parsePrompt, EFFECTS } from '/engine.js';

const $ = (sel) => document.querySelector(sel);

const canvas = $('#canvas');
const ctx = canvas.getContext('2d');
const fileInput = $('#fileInput');
const dropzone = $('#dropzone');
const dropEmpty = $('#dropEmpty');
const dropFilled = $('#dropFilled');
const refGrid = $('#refGrid');
const fileNameEl = $('#fileName');
const promptEl = $('#prompt');
const chipsEl = $('#chips');
const quickEl = $('#quickChips');
const resolutionEl = $('#resolution');
const fpsEl = $('#fps');
const frameCountEl = $('#frameCount');
const frameValEl = $('#frameVal');
const loopEl = $('#loop');
const generateBtn = $('#generateBtn');
const demoBtn = $('#demoBtn');
const playBtn = $('#playBtn');
const playIcon = $('#playIcon');
const scrubEl = $('#scrub');
const timecodeEl = $('#timecode');
const durationEl = $('#duration');
const stageEmpty = $('#stageEmpty');
const modeBadge = $('#modeBadge');
const statusPill = $('#statusPill');
const exportHint = $('#exportHint');
const exportBtns = Array.from(document.querySelectorAll('#exportBtns button'));
const progressWrap = $('#progressWrap');
const progressBar = $('#progressBar');
const progressText = $('#progressText');
const toastEl = $('#toast');

const aiProvider = $('#aiProvider');
const aiCount = $('#aiCount');
const aiBaseUrl = $('#aiBaseUrl');
const aiKey = $('#aiKey');
const aiModel = $('#aiModel');
const aiSize = $('#aiSize');
const aiBtn = $('#aiBtn');
const aiDetails = $('#aiDetails');

const PLAY_ICON = 'M8 5v14l11-7z';
const PAUSE_ICON = 'M6 5h4v14H6zM14 5h4v14h-4z';
const MAX_REFS = 8;

const state = {
  images: [],
  image: null,
  imageURL: null,
  imageName: '',
  keyframes: null,
  mode: 'local',
  renderer: null,
  width: 1280,
  height: 720,
  frameCount: 48,
  fps: 12,
  loop: true,
  index: 0,
  playing: false,
  raf: 0,
  lastTick: 0,
  busy: false,
  parseTimer: 0,
};

const QUICK_PRESETS = [
  { label: '推近 · 光尘', text: '镜头缓慢推近，夕阳暖光，空气中有漂浮的光尘，电影感' },
  { label: '雨夜霓虹', text: '雨夜霓虹街道，手持轻微晃动，冷色蓝调，地面有雨丝与反光' },
  { label: '梦幻漂移', text: '画面缓慢向右漂移，梦幻柔光，漂浮的光斑，轻微旋转' },
  { label: '水波复古', text: '水波涟漪扭曲，复古胶片颗粒，轻微闪烁，暖调' },
  { label: '雪夜拉远', text: '镜头缓慢拉远，下雪，夜色，呼吸感' },
];

/* ---------------- utilities ---------------- */

function toast(message, isError = false) {
  toastEl.textContent = message;
  toastEl.classList.toggle('error', isError);
  toastEl.hidden = false;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => { toastEl.hidden = true; }, 3200);
}

function nextFrame() {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

function setProgress(value, text) {
  progressWrap.hidden = false;
  progressBar.style.width = `${Math.max(0, Math.min(100, value))}%`;
  progressText.textContent = text;
}

function hideProgress() {
  progressWrap.hidden = true;
  progressBar.style.width = '0%';
}

function parseResolution() {
  const [w, h] = resolutionEl.value.split('x').map(Number);
  state.width = w;
  state.height = h;
}

function readPrompt() {
  return parsePrompt(promptEl.value.trim());
}

/* ---------------- prompt chips ---------------- */

function renderChips() {
  const parsed = readPrompt();
  chipsEl.innerHTML = '';
  if (!promptEl.value.trim()) {
    chipsEl.innerHTML = '<span class="chip muted">等待提示词</span>';
  } else if (parsed.labels.length === 0) {
    chipsEl.innerHTML = '<span class="chip muted">未匹配到效果关键词，将使用默认推镜</span>';
  } else {
    for (const id of parsed.ids) {
      const effect = EFFECTS.find((e) => e.id === id);
      if (!effect) continue;
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.dataset.group = effect.group;
      chip.textContent = effect.label;
      chipsEl.appendChild(chip);
    }
    const extras = [];
    if (parsed.intensity > 1.2) extras.push('强度加强');
    if (parsed.intensity < 0.8) extras.push('强度减弱');
    if (parsed.speed > 1.2) extras.push('速度加快');
    for (const text of extras) {
      const chip = document.createElement('span');
      chip.className = 'chip muted';
      chip.textContent = text;
      chipsEl.appendChild(chip);
    }
  }
  if (state.renderer) applyPromptToRenderer(parsed);
}

function applyPromptToRenderer(parsed) {
  if (!state.renderer || state.busy) return;
  state.renderer.effects = new Set(parsed.ids.length ? parsed.ids : ['push']);
  state.renderer.intensity = parsed.intensity;
  state.renderer.speed = parsed.speed;
  state.renderer.loop = state.loop;
  renderCurrent();
}

/* ---------------- image loading ---------------- */

function decodeImage(dataURL) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('图片解码失败'));
    img.src = dataURL;
  });
}

function syncPrimary() {
  const first = state.images[0];
  state.image = first ? first.img : null;
  state.imageURL = first ? first.dataURL : null;
  state.imageName = first ? first.name : '';
}

function renderRefs() {
  refGrid.innerHTML = '';
  refGrid.dataset.count = String(state.images.length);
  state.images.forEach((ref, index) => {
    const cell = document.createElement('div');
    cell.className = 'ref-item';

    const img = document.createElement('img');
    img.src = ref.dataURL;
    img.alt = ref.name;

    const badge = document.createElement('span');
    badge.className = 'ref-index';
    badge.textContent = String(index + 1);

    const del = document.createElement('button');
    del.type = 'button';
    del.className = 'ref-del';
    del.dataset.refDel = String(index);
    del.title = '移除这张';
    del.setAttribute('aria-label', `移除第 ${index + 1} 张参考图`);
    del.textContent = '×';

    cell.append(img, badge, del);
    refGrid.appendChild(cell);
  });
  fileNameEl.textContent = state.images.length > 1
    ? `${state.images.length} 张 · 首张为主参考`
    : '1 张参考图';
}

async function addRefs(items, { replace = false } = {}) {
  const decoded = [];
  for (const item of items) {
    try {
      decoded.push({ ...item, img: await decodeImage(item.dataURL) });
    } catch { /* 跳过无法解码的图片 */ }
  }
  if (!decoded.length) {
    toast('图片解码失败，请换一张试试', true);
    return;
  }

  const merged = replace ? decoded : [...state.images, ...decoded];
  if (merged.length > MAX_REFS) toast(`最多 ${MAX_REFS} 张参考图，多余的已忽略`, true);
  state.images = merged.slice(0, MAX_REFS);
  state.keyframes = null;
  state.mode = 'local';
  syncPrimary();
  renderRefs();
  dropEmpty.hidden = true;
  dropFilled.hidden = false;

  if (!promptEl.value.trim()) {
    promptEl.value = QUICK_PRESETS[0].text;
    renderChips();
  }
  generate(true);
  toast(state.images.length > 1 ? `已载入 ${state.images.length} 张参考图` : '参考图已载入');
}

function fileToDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(new Error('读取文件失败'));
    reader.readAsDataURL(file);
  });
}

async function handleFiles(files) {
  const list = Array.from(files || []);
  if (!list.length) return;

  const room = MAX_REFS - state.images.length;
  if (room <= 0) {
    toast(`最多上传 ${MAX_REFS} 张参考图`, true);
    return;
  }

  const picked = [];
  for (const file of list) {
    if (!file.type.startsWith('image/')) {
      toast(`「${file.name}」不是图片，已跳过`, true);
      continue;
    }
    if (file.size > 25 * 1024 * 1024) {
      toast(`「${file.name}」超过 25MB，已跳过`, true);
      continue;
    }
    if (picked.length < room) picked.push(file);
  }
  if (list.length > room) toast(`最多 ${MAX_REFS} 张参考图，多余的已忽略`, true);
  if (!picked.length) return;

  try {
    const items = [];
    for (const file of picked) {
      items.push({ dataURL: await fileToDataURL(file), name: file.name });
    }
    await addRefs(items);
  } catch (err) {
    toast(err.message, true);
  }
}

dropzone.addEventListener('click', (event) => {
  if (event.target === fileInput || event.target.closest('#addImg') || event.target.closest('.ref-del') || event.target.closest('#clearImg')) return;
  fileInput.click();
});
fileInput.addEventListener('click', (event) => event.stopPropagation());
fileInput.addEventListener('change', (event) => handleFiles(event.target.files));

['dragenter', 'dragover'].forEach((type) => {
  dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    dropzone.classList.add('drag');
  });
});
['dragleave', 'drop'].forEach((type) => {
  dropzone.addEventListener(type, (event) => {
    event.preventDefault();
    dropzone.classList.remove('drag');
  });
});
dropzone.addEventListener('drop', (event) => handleFiles(event.dataTransfer.files));

refGrid.addEventListener('click', (event) => {
  const btn = event.target.closest('[data-ref-del]');
  if (!btn) return;
  event.stopPropagation();
  state.images.splice(Number(btn.dataset.refDel), 1);
  if (!state.images.length) {
    resetAll();
    return;
  }
  state.keyframes = null;
  state.mode = 'local';
  syncPrimary();
  renderRefs();
  generate(true);
  toast('已移除 1 张参考图');
});

$('#addImg').addEventListener('click', (event) => {
  event.stopPropagation();
  fileInput.click();
});

$('#clearImg').addEventListener('click', (event) => {
  event.stopPropagation();
  resetAll();
});

$('#demoBtn').addEventListener('click', async () => {
  try {
    const res = await fetch('/demo.jpg');
    if (!res.ok) throw new Error('示例图不存在');
    const blob = await res.blob();
    const dataURL = await fileToDataURL(blob);
    await addRefs([{ dataURL, name: 'demo.jpg' }], { replace: true });
  } catch (err) {
    toast(err.message, true);
  }
});

function resetAll() {
  stopPlayback();
  state.images = [];
  state.image = null;
  state.imageURL = null;
  state.keyframes = null;
  state.renderer = null;
  refGrid.innerHTML = '';
  canvas.width = 1280;
  canvas.height = 720;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  dropEmpty.hidden = false;
  dropFilled.hidden = true;
  stageEmpty.hidden = false;
  modeBadge.hidden = true;
  fileInput.value = '';
  updateTransport();
  updateStatus('未载入素材');
  exportBtns.forEach((b) => { b.disabled = true; });
  playBtn.disabled = true;
  exportHint.textContent = '生成连续帧后可导出';
  hideProgress();
}

/* ---------------- rendering ---------------- */

function buildRenderer() {
  if (!state.image) return;
  parseResolution();
  if (canvas.width !== state.width || canvas.height !== state.height) {
    canvas.width = state.width;
    canvas.height = state.height;
  }
  const parsed = readPrompt();
  const effects = parsed.ids.length ? parsed.ids : ['push'];
  const refKeyframes = state.images.length > 1 ? state.images.map((ref) => ref.img) : null;
  state.renderer = new FrameRenderer({
    image: state.image,
    keyframes: state.mode === 'ai' ? state.keyframes : refKeyframes,
    width: state.width,
    height: state.height,
    effects,
    intensity: parsed.intensity,
    speed: parsed.speed,
    frameCount: state.frameCount,
    fps: state.fps,
    loop: state.loop,
    seed: 13,
  });
  if (state.index >= state.frameCount) state.index = 0;
  stageEmpty.hidden = true;
  playBtn.disabled = false;
  exportBtns.forEach((b) => { b.disabled = false; });
  exportHint.textContent = '导出会按当前参数重新渲染全部帧';
  modeBadge.hidden = false;
  modeBadge.textContent = state.mode === 'ai' ? 'AI 关键帧 · 本地插值' : '本地程序化生成';
  modeBadge.classList.toggle('ai', state.mode === 'ai');
  updateStatus(`已生成 ${state.frameCount} 帧 · ${state.width}×${state.height}`);
  renderCurrent();
  updateTransport();
}

function generate(autoplay = true) {
  if (!state.image) {
    toast('请先上传至少一张参考图', true);
    return;
  }
  stopPlayback();
  buildRenderer();
  if (autoplay) startPlayback();
}

function renderCurrent() {
  if (!state.renderer) return;
  state.renderer.render(ctx, state.index);
  updateTransport();
}

function startPlayback() {
  if (!state.renderer || state.busy) return;
  state.playing = true;
  state.lastTick = 0;
  playIcon.setAttribute('d', PAUSE_ICON);
  state.raf = requestAnimationFrame(tick);
}

function stopPlayback() {
  state.playing = false;
  cancelAnimationFrame(state.raf);
  playIcon.setAttribute('d', PLAY_ICON);
}

function tick(ts) {
  if (!state.playing || !state.renderer) return;
  const interval = 1000 / state.fps;
  if (!state.lastTick) state.lastTick = ts;
  const delta = ts - state.lastTick;
  if (delta >= interval) {
    const steps = Math.min(3, Math.floor(delta / interval));
    state.lastTick += steps * interval;
    let next = state.index + steps;
    if (next >= state.frameCount) {
      if (state.loop) next %= state.frameCount;
      else {
        next = state.frameCount - 1;
        stopPlayback();
      }
    }
    state.index = next;
    state.renderer.render(ctx, state.index);
    updateTransport();
  }
  if (state.playing) state.raf = requestAnimationFrame(tick);
}

function updateTransport() {
  const total = state.frameCount;
  scrubEl.max = Math.max(0, total - 1);
  scrubEl.value = String(Math.min(state.index, Math.max(0, total - 1)));
  timecodeEl.textContent = `${String(state.index + 1).padStart(2, '0')} / ${String(total).padStart(2, '0')}`;
  durationEl.textContent = `${(total / state.fps).toFixed(2)}s`;
}

function updateStatus(text) {
  statusPill.textContent = text;
  statusPill.classList.toggle('ready', !!state.renderer);
}

/* ---------------- controls ---------------- */

playBtn.addEventListener('click', () => {
  if (!state.renderer) return;
  if (state.playing) {
    stopPlayback();
  } else {
    if (!state.loop && state.index >= state.frameCount - 1) state.index = 0;
    startPlayback();
  }
});

scrubEl.addEventListener('input', () => {
  if (!state.renderer) return;
  stopPlayback();
  state.index = Number(scrubEl.value);
  state.renderer.render(ctx, state.index);
  updateTransport();
});

promptEl.addEventListener('input', () => {
  clearTimeout(state.parseTimer);
  state.parseTimer = setTimeout(renderChips, 220);
});

frameCountEl.addEventListener('input', () => {
  state.frameCount = Number(frameCountEl.value);
  frameValEl.textContent = String(state.frameCount);
});
frameCountEl.addEventListener('change', () => {
  if (state.renderer) {
    stopPlayback();
    state.index = 0;
    buildRenderer();
  }
});

fpsEl.addEventListener('change', () => {
  state.fps = Number(fpsEl.value);
  if (state.renderer) {
    updateTransport();
    if (state.playing) {
      stopPlayback();
      startPlayback();
    }
  }
});

resolutionEl.addEventListener('change', () => {
  if (state.renderer) {
    stopPlayback();
    buildRenderer();
  }
});

loopEl.addEventListener('change', () => {
  state.loop = loopEl.checked;
  if (state.renderer) {
    state.renderer.loop = state.loop;
    renderCurrent();
  }
});

generateBtn.addEventListener('click', () => generate(true));

document.addEventListener('keydown', (event) => {
  const tag = document.activeElement?.tagName;
  if (tag === 'TEXTAREA' || tag === 'INPUT' || tag === 'SELECT') return;
  if (event.code === 'Space') {
    event.preventDefault();
    playBtn.click();
  } else if (state.renderer && event.key === 'ArrowRight') {
    stopPlayback();
    state.index = Math.min(state.frameCount - 1, state.index + 1);
    state.renderer.render(ctx, state.index);
    updateTransport();
  } else if (state.renderer && event.key === 'ArrowLeft') {
    stopPlayback();
    state.index = Math.max(0, state.index - 1);
    state.renderer.render(ctx, state.index);
    updateTransport();
  }
});

/* ---------------- quick presets ---------------- */

for (const preset of QUICK_PRESETS) {
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.textContent = preset.label;
  btn.addEventListener('click', () => {
    promptEl.value = preset.text;
    renderChips();
  });
  quickEl.appendChild(btn);
}

/* ---------------- export ---------------- */

function timestamp() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
}

async function captureFrames(onProgress) {
  const frames = [];
  const total = state.frameCount;
  const saved = state.index;
  stopPlayback();
  for (let i = 0; i < total; i++) {
    state.renderer.render(ctx, i);
    frames.push(canvas.toDataURL('image/png'));
    if (onProgress) onProgress(i + 1, total);
    if (i % 3 === 0) await nextFrame();
  }
  state.index = saved;
  state.renderer.render(ctx, state.index);
  updateTransport();
  return frames;
}

function downloadBlob(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

async function exportSheet() {
  const { width: w, height: h, frameCount: n } = state;
  const cols = Math.ceil(Math.sqrt(n));
  const rows = Math.ceil(n / cols);
  const area = w * h * n;
  const scale = Math.min(1, Math.sqrt((64e6) / Math.max(1, area)));
  const cellW = Math.max(1, Math.round(w * scale));
  const cellH = Math.max(1, Math.round(h * scale));
  const sheet = document.createElement('canvas');
  sheet.width = cols * cellW;
  sheet.height = rows * cellH;
  const sctx = sheet.getContext('2d');
  sctx.imageSmoothingQuality = 'high';
  const saved = state.index;
  stopPlayback();
  for (let i = 0; i < n; i++) {
    state.renderer.render(ctx, i);
    const x = (i % cols) * cellW;
    const y = Math.floor(i / cols) * cellH;
    sctx.drawImage(canvas, 0, 0, w, h, x, y, cellW, cellH);
    setProgress(((i + 1) / n) * 100, `合成精灵图 ${i + 1}/${n}`);
    if (i % 4 === 0) await nextFrame();
  }
  state.index = saved;
  state.renderer.render(ctx, state.index);
  updateTransport();
  const blob = await new Promise((resolve) => sheet.toBlob(resolve, 'image/png'));
  downloadBlob(blob, `sprite-${timestamp()}.png`);
  setProgress(100, `已导出 ${cols}×${rows} 精灵图`);
  setTimeout(hideProgress, 1200);
}

async function exportToServer(format) {
  const frames = await captureFrames((done, total) => {
    setProgress((done / total) * 42, `渲染帧 ${done}/${total}`);
  });
  setProgress(46, '上传帧并编码…');
  const res = await fetch('/api/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      format,
      fps: state.fps,
      name: (promptEl.value || 'frames').slice(0, 24),
      frames,
    }),
  });
  if (!res.ok) {
    let message = `导出失败（HTTP ${res.status}）`;
    try {
      const data = await res.json();
      if (data.error) message = data.error;
    } catch { /* ignore */ }
    throw new Error(message);
  }
  const data = await res.json();
  setProgress(100, `已导出 ${(data.bytes / 1048576).toFixed(1)}MB · ${data.file}`);
  const a = document.createElement('a');
  a.href = data.url;
  a.download = data.file;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(hideProgress, 1400);
}

async function runExport(format) {
  if (!state.renderer || state.busy) return;
  state.busy = true;
  stopPlayback();
  exportBtns.forEach((b) => { b.disabled = true; });
  generateBtn.disabled = true;
  try {
    if (format === 'sheet') await exportSheet();
    else await exportToServer(format);
  } catch (err) {
    hideProgress();
    toast(err.message || '导出失败', true);
  } finally {
    state.busy = false;
    exportBtns.forEach((b) => { b.disabled = !state.renderer; });
    generateBtn.disabled = false;
  }
}

exportBtns.forEach((btn) => {
  btn.disabled = true;
  btn.addEventListener('click', () => runExport(btn.dataset.format));
});

/* ---------------- AI keyframes ---------------- */

const AI_KEY = 'frameStudio.aiConfig';

function loadAIConfig() {
  try {
    const cfg = JSON.parse(localStorage.getItem(AI_KEY) || '{}');
    if (cfg.provider) aiProvider.value = cfg.provider;
    if (cfg.baseUrl) aiBaseUrl.value = cfg.baseUrl;
    if (cfg.key) aiKey.value = cfg.key;
    if (cfg.model) aiModel.value = cfg.model;
    if (cfg.size) aiSize.value = cfg.size;
    if (cfg.count) aiCount.value = String(cfg.count);
  } catch { /* ignore */ }
}

function saveAIConfig() {
  localStorage.setItem(AI_KEY, JSON.stringify({
    provider: aiProvider.value,
    baseUrl: aiBaseUrl.value.trim(),
    key: aiKey.value.trim(),
    model: aiModel.value.trim(),
    size: aiSize.value.trim(),
    count: aiCount.value,
  }));
}

[aiProvider, aiBaseUrl, aiKey, aiModel, aiSize, aiCount].forEach((el) => {
  el.addEventListener('change', saveAIConfig);
});

function aiDetailsOpen() {
  aiDetails.open = true;
  aiDetails.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function loadImageElement(dataURL) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error('关键帧图片加载失败'));
    img.src = dataURL;
  });
}

async function runAI() {
  if (state.busy) return;
  if (!state.imageURL) {
    toast('请先上传至少一张参考图', true);
    return;
  }
  const baseUrl = aiBaseUrl.value.trim();
  if (!baseUrl) {
    toast('请填写 AI 接口 Base URL', true);
    aiDetailsOpen();
    return;
  }
  const count = Number(aiCount.value);
  const prompt = promptEl.value.trim();
  if (!prompt) {
    toast('请先写下提示词', true);
    return;
  }
  const config = {
    provider: aiProvider.value,
    baseUrl,
    apiKey: aiKey.value.trim(),
    model: aiModel.value.trim(),
    size: aiSize.value.trim() || undefined,
  };

  state.busy = true;
  stopPlayback();
  aiBtn.disabled = true;
  exportBtns.forEach((b) => { b.disabled = true; });
  generateBtn.disabled = true;
  let succeeded = false;

  try {
    const keyframes = [await loadImageElement(state.imageURL)];
    for (let i = 1; i < count; i++) {
      const progress = Math.round((i / (count - 1)) * 100);
      setProgress((i / count) * 100, `AI 关键帧 ${i + 1}/${count} · ${progress}%`);
      const framePrompt = [
        prompt,
        '',
        `这是同一段连续画面中的第 ${i + 1}/${count} 个关键帧，时间进度约 ${progress}%。`,
        '以参考图为基础，保持主体、构图、光线与风格一致，只推进动作、视角或镜头变化。',
        '不要添加文字、水印、边框或拼图。',
      ].join('\n');
      const res = await fetch('/api/ai/keyframes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ config, prompt: framePrompt, image: state.imageURL }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || `AI 接口返回 ${res.status}`);
      if (!Array.isArray(data.images) || !data.images.length) throw new Error('AI 接口未返回图片');
      keyframes.push(await loadImageElement(data.images[0]));
      setProgress(((i + 1) / count) * 100, `AI 关键帧 ${i + 1}/${count} 完成`);
    }
    state.keyframes = keyframes;
    state.mode = 'ai';
    state.index = 0;
    buildRenderer();
    succeeded = true;
    setProgress(100, `已生成 ${keyframes.length} 个关键帧，本地插值为 ${state.frameCount} 帧`);
    setTimeout(hideProgress, 1800);
    toast('AI 关键帧已生成');
  } catch (err) {
    hideProgress();
    toast(err.message || 'AI 生成失败', true);
  } finally {
    state.busy = false;
    aiBtn.disabled = false;
    generateBtn.disabled = false;
    exportBtns.forEach((b) => { b.disabled = !state.renderer; });
  }
  if (succeeded) startPlayback();
}

loadAIConfig();
aiBtn.addEventListener('click', runAI);

/* ---------------- help ---------------- */

const helpDialog = $('#helpDialog');
$('#helpBtn').addEventListener('click', () => helpDialog.showModal());
$('#closeHelp').addEventListener('click', () => helpDialog.close());
helpDialog.addEventListener('click', (event) => {
  if (event.target === helpDialog) helpDialog.close();
});

/* ---------------- init ---------------- */

renderChips();
updateTransport();
updateStatus('未载入素材');
