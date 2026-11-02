import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readFile, writeFile, mkdir, rm } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import crypto from 'node:crypto';

const exec = promisify(execFile);
const ROOT = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC = path.join(ROOT, 'public');
const OUT = path.join(ROOT, 'renders');
const PORT = Number(process.env.PORT) || 4321;
const MAX_BODY = 500 * 1024 * 1024;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.png': 'image/png',
  '.zip': 'application/zip',
  '.gif': 'image/gif',
  '.webm': 'video/webm',
  '.mp4': 'video/mp4',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
};

function send(res, status, body, headers = {}) {
  res.writeHead(status, {
    'Cache-Control': 'no-store',
    ...headers,
  });
  res.end(body);
}

function sendJSON(res, status, data) {
  send(res, status, JSON.stringify(data), { 'Content-Type': 'application/json; charset=utf-8' });
}

async function readBody(req, limit = MAX_BODY) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw Object.assign(new Error('请求体过大'), { status: 413 });
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

async function readJSON(req) {
  const buf = await readBody(req);
  try {
    return JSON.parse(buf.toString('utf8'));
  } catch {
    throw Object.assign(new Error('请求体不是合法 JSON'), { status: 400 });
  }
}

function dataURLToBuffer(dataURL) {
  const m = /^data:(image\/[a-z0-9.+-]+);base64,(.+)$/i.exec(dataURL || '');
  if (!m) throw Object.assign(new Error('帧数据格式不正确'), { status: 400 });
  return { mime: m[1], buffer: Buffer.from(m[2], 'base64') };
}

function pngSize(buffer) {
  if (buffer.length < 24 || buffer.toString('ascii', 1, 4) !== 'PNG') return null;
  return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
}

async function rmSafe(dir) {
  try {
    await rm(dir, { recursive: true, force: true });
  } catch {
    /* ignore */
  }
}

const FORMATS = {
  zip: { ext: 'zip', label: 'PNG 帧序列' },
  gif: { ext: 'gif', label: 'GIF 动图' },
  webm: { ext: 'webm', label: 'WebM 视频' },
  mp4: { ext: 'mp4', label: 'MP4 视频' },
};

function slugify(text) {
  const ascii = (text || '')
    .replace(/[^\w\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .slice(0, 40);
  return ascii || 'frames';
}

async function handleExport(req, res) {
  const body = await readJSON(req);
  const format = body.format;
  const fps = Math.min(60, Math.max(1, Number(body.fps) || 12));
  const frames = body.frames;
  if (!FORMATS[format]) throw Object.assign(new Error('不支持的导出格式'), { status: 400 });
  if (!Array.isArray(frames) || frames.length === 0) throw Object.assign(new Error('缺少帧数据'), { status: 400 });
  if (frames.length > 400) throw Object.assign(new Error('帧数过多（上限 400）'), { status: 400 });

  const id = crypto.randomUUID().slice(0, 8);
  const stamp = new Date().toISOString().replace(/[-:T]/g, '').slice(0, 14);
  const base = `${slugify(body.name)}-${stamp}-${id}`;
  const work = path.join(OUT, '.work', id);
  await mkdir(work, { recursive: true });
  await mkdir(OUT, { recursive: true });

  let width = 0;
  let height = 0;
  try {
    for (let i = 0; i < frames.length; i++) {
      const { buffer } = dataURLToBuffer(frames[i]);
      const size = pngSize(buffer);
      if (size) {
        width = Math.max(width, size.width);
        height = Math.max(height, size.height);
      }
      await writeFile(path.join(work, `frame_${String(i + 1).padStart(4, '0')}.png`), buffer);
    }
    if (!width || !height) throw Object.assign(new Error('无法识别帧尺寸'), { status: 400 });

    const files = new Array(frames.length)
      .fill(0)
      .map((_, i) => `frame_${String(i + 1).padStart(4, '0')}.png`);
    const outPath = path.join(OUT, `${base}.${FORMATS[format].ext}`);

    if (format === 'zip') {
      await exec('zip', ['-0', '-q', outPath, ...files], { cwd: work });
    } else if (format === 'gif') {
      const palette = path.join(work, 'palette.png');
      await exec('ffmpeg', ['-y', '-framerate', String(fps), '-i', 'frame_%04d.png',
        '-vf', 'palettegen=max_colors=256:stats_mode=diff', palette], { cwd: work });
      await exec('ffmpeg', ['-y', '-framerate', String(fps), '-i', 'frame_%04d.png',
        '-i', palette, '-lavfi', 'paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle',
        '-loop', '0', outPath], { cwd: work });
    } else if (format === 'webm') {
      await exec('ffmpeg', ['-y', '-framerate', String(fps), '-i', 'frame_%04d.png',
        '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '32', '-pix_fmt', 'yuv420p',
        '-row-mt', '1', outPath], { cwd: work, maxBuffer: 32 * 1024 * 1024 });
    } else if (format === 'mp4') {
      await exec('ffmpeg', ['-y', '-framerate', String(fps), '-i', 'frame_%04d.png',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart', outPath], { cwd: work, maxBuffer: 32 * 1024 * 1024 });
    }

    const stat = await import('node:fs/promises').then((fs) => fs.stat(outPath));
    sendJSON(res, 200, {
      url: `/files/${encodeURIComponent(path.basename(outPath))}`,
      file: path.basename(outPath),
      format,
      frames: frames.length,
      fps,
      width,
      height,
      bytes: stat.size,
    });
  } finally {
    await rmSafe(work);
  }
}

function bufferFromB64(b64) {
  return Buffer.from(b64, 'base64');
}

function imagesFromResponse(json) {
  const out = [];
  const push = (item) => {
    if (typeof item === 'string') {
      if (item.startsWith('data:image')) out.push(item);
      else if (/^https?:/.test(item)) out.push(item);
      return;
    }
    if (!item) return;
    if (item.b64_json) out.push(`data:image/png;base64,${item.b64_json}`);
    else if (item.image_base64) out.push(`data:image/png;base64,${item.image_base64}`);
    else if (item.url) out.push(item.url);
  };
  if (Array.isArray(json.data)) json.data.forEach(push);
  if (Array.isArray(json.images)) json.images.forEach(push);
  if (Array.isArray(json.output)) json.output.forEach(push);
  if (json.image) push(json.image);
  return out;
}

async function normalizeImages(images) {
  const result = [];
  for (const item of images) {
    if (item.startsWith('data:')) {
      result.push(item);
      continue;
    }
    const res = await fetch(item, { signal: AbortSignal.timeout(60_000) });
    if (!res.ok) throw new Error(`下载关键帧失败：HTTP ${res.status}`);
    const buf = Buffer.from(await res.arrayBuffer());
    const mime = res.headers.get('content-type') || 'image/png';
    result.push(`data:${mime};base64,${buf.toString('base64')}`);
  }
  return result;
}

async function handleAI(req, res) {
  const body = await readJSON(req);
  const cfg = body.config || {};
  const prompt = String(body.prompt || '').trim();
  const image = body.image;
  if (!prompt) throw Object.assign(new Error('缺少提示词'), { status: 400 });
  if (!image) throw Object.assign(new Error('缺少参考图'), { status: 400 });
  if (!cfg.baseUrl) throw Object.assign(new Error('未配置 API 地址'), { status: 400 });

  const baseUrl = String(cfg.baseUrl).replace(/\/+$/, '');
  const headers = { Authorization: `Bearer ${cfg.apiKey || ''}` };
  let response;

  if (cfg.provider === 'openai') {
    const { buffer, mime } = dataURLToBuffer(image);
    const form = new FormData();
    form.append('model', cfg.model || 'gpt-image-1');
    form.append('prompt', prompt);
    form.append('n', '1');
    if (cfg.size) form.append('size', cfg.size);
    form.append('image', new Blob([buffer], { type: mime }), 'reference.png');
    response = await fetch(`${baseUrl}/images/edits`, {
      method: 'POST',
      headers,
      body: form,
      signal: AbortSignal.timeout(180_000),
    });
  } else {
    const payload = {
      model: cfg.model,
      prompt,
      image,
      n: 1,
      size: cfg.size,
      response_format: 'b64_json',
      ...(cfg.extra && typeof cfg.extra === 'object' ? cfg.extra : {}),
    };
    response = await fetch(baseUrl, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(180_000),
    });
  }

  const text = await response.text();
  if (!response.ok) {
    throw Object.assign(new Error(`AI 接口返回 ${response.status}：${text.slice(0, 300)}`), { status: 502 });
  }
  let json;
  try {
    json = JSON.parse(text);
  } catch {
    throw Object.assign(new Error('AI 接口返回的不是 JSON'), { status: 502 });
  }
  const raw = imagesFromResponse(json);
  if (raw.length === 0) throw Object.assign(new Error('AI 接口未返回图片'), { status: 502 });
  const images = await normalizeImages(raw.slice(0, 8));
  sendJSON(res, 200, { images });
}

async function serveStatic(req, res, pathname) {
  let root = PUBLIC;
  let rel = pathname === '/' ? '/index.html' : pathname;
  if (pathname.startsWith('/files/')) {
    root = OUT;
    rel = pathname.slice('/files'.length);
  }
  const filePath = path.join(root, path.normalize(decodeURIComponent(rel)));
  if (!filePath.startsWith(root + path.sep) && filePath !== path.join(root, 'index.html')) {
    send(res, 403, 'Forbidden');
    return;
  }
  try {
    const data = await readFile(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const headers = { 'Content-Type': MIME[ext] || 'application/octet-stream' };
    if (pathname.startsWith('/files/')) {
      headers['Content-Disposition'] = `attachment; filename="${path.basename(filePath)}"`;
    }
    send(res, 200, data, headers);
  } catch {
    send(res, 404, 'Not found');
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  try {
    if (req.method === 'GET' && url.pathname === '/api/health') {
      sendJSON(res, 200, { ok: true, port: PORT });
      return;
    }
    if (req.method === 'POST' && url.pathname === '/api/export') {
      await handleExport(req, res);
      return;
    }
    if (req.method === 'POST' && url.pathname === '/api/ai/keyframes') {
      await handleAI(req, res);
      return;
    }
    if (req.method === 'GET' || req.method === 'HEAD') {
      await serveStatic(req, res, url.pathname);
      return;
    }
    sendJSON(res, 404, { error: 'Not found' });
  } catch (err) {
    sendJSON(res, err.status || 500, { error: err.message || '服务异常' });
  }
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Frame Studio running at http://localhost:${PORT}`);
});
