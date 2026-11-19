// 라인아트 뮤직비디오 HTML을 헤드리스 크롬으로 프레임 단위 캡처해 mp4로 만든다.
//
// 페이지 규약: window.__ready (Promise, 폰트 로딩 완료), window.__render(t) (t초 화면을 #c 캔버스에 그림)
//
// 사용법:
//   node capture.mjs stills <page.html> <outDir> 1,10,33.5          -> PNG 스틸
//   node capture.mjs video  <page.html> <song.mp3> <out.mp4> [fps=30] [t0=0] [t1=오디오 길이]
//
// Google Fonts 요청은 curl로 받아 넘겨준다 (프록시 CA를 따르기 위해, TLS 검증을 끄지 않음).
import { createRequire } from 'node:module';
import { execFileSync, spawn } from 'node:child_process';
import { mkdirSync, existsSync, readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';

const require = createRequire(import.meta.url);
function loadPlaywright() {
  const tries = ['playwright', '/opt/node-tools/node_modules/playwright/index.js'];
  try { tries.push(path.join(execFileSync('npm', ['root', '-g']).toString().trim(), 'playwright')); } catch {}
  for (const p of tries) { try { return require(p); } catch {} }
  throw new Error('playwright를 찾을 수 없습니다. npm i -g playwright 후 다시 실행하세요.');
}
const { chromium } = loadPlaywright();

const cacheDir = path.join(process.env.HOME || '/tmp', '.cache', 'lineart-mv-fonts');
mkdirSync(cacheDir, { recursive: true });
function curl(url) {
  const f = path.join(cacheDir, createHash('md5').update(url).digest('hex'));
  if (!existsSync(f)) execFileSync('curl', ['-sS', '-L', '-o', f, '-A', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36', url]);
  return readFileSync(f);
}
const audioLen = f => +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]).toString().trim();

const [mode, page, ...rest] = process.argv.slice(2);
if (!mode || !page) { console.error('사용법은 파일 상단 주석 참고'); process.exit(1); }

const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const tab = await browser.newPage({ viewport: { width: 1280, height: 1280 }, deviceScaleFactor: 1 });
await tab.route(/fonts\.(googleapis|gstatic)\.com/, async route => {
  const url = route.request().url();
  await route.fulfill({ status: 200, body: curl(url), headers: { 'content-type': url.includes('googleapis') ? 'text/css' : 'font/woff2', 'access-control-allow-origin': '*' } });
});
tab.on('pageerror', e => console.error('[pageerror]', e.message));
tab.on('console', m => { if (m.type() === 'error') console.error('[page]', m.text()); });
await tab.goto('file://' + path.resolve(page));
await tab.evaluate(() => window.__ready);
await tab.waitForTimeout(300);

const frame = (t, type = 'png', q = 0.92) => tab.evaluate(([t, type, q]) => {
  window.__render(t);
  return document.getElementById('c').toDataURL(type === 'png' ? 'image/png' : 'image/jpeg', q).split(',')[1];
}, [t, type, q]);

if (mode === 'stills') {
  const [outDir, times] = rest; mkdirSync(outDir, { recursive: true });
  for (const s of times.split(',')) writeFileSync(path.join(outDir, `t${(+s).toFixed(2).padStart(7, '0')}.png`), Buffer.from(await frame(+s), 'base64'));
} else if (mode === 'video') {
  const [audio, out, fpsA, t0A, t1A] = rest;
  const fps = +(fpsA || 30), t0 = +(t0A || 0), t1 = +(t1A || audioLen(audio));
  const n = Math.round((t1 - t0) * fps);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    '-ss', String(t0), '-t', String(t1 - t0), '-i', audio,
    '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-tune', 'animation', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  const st = Date.now();
  for (let i = 0; i < n; i++) {
    const buf = Buffer.from(await frame(t0 + i / fps, 'jpeg', 0.93), 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 300 === 0) console.log(`frame ${i}/${n}  ${((Date.now() - st) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
} else { console.error('mode는 stills 또는 video'); process.exitCode = 1; }
await browser.close();
