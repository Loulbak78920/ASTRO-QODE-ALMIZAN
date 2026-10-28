#!/usr/bin/env node
// Emulation.setDeviceMetricsOverride contourne le rognage de --window-size (largeur mini 500, cadre -16 px).
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [dirArg, url, ...widthArgs] = process.argv.slice(2);
if (!dirArg || !url || widthArgs.length === 0) {
  console.error('usage: node capturer_cdp.mjs DOSSIER_SORTIE URL LARGEUR [LARGEUR...]');
  process.exit(64);
}
const dir = path.resolve(dirArg);
fs.mkdirSync(dir, { recursive: true });
const widths = widthArgs.map(Number);
if (widths.some((w) => !Number.isInteger(w) || w < 200)) {
  console.error('largeurs invalides: ' + widthArgs.join(' '));
  process.exit(64);
}
const prefix = process.env.CAPTURE_PREFIX || 'capture';
const chrome = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const profile = path.join(dir, 'prof-cdp');
fs.rmSync(profile, { recursive: true, force: true, maxRetries: 10, retryDelay: 200 });
const child = spawn(chrome, [
  '--headless=new', '--disable-gpu', '--no-first-run',
  '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank'
], { stdio: 'ignore' });
child.on('error', (e) => { console.error('CHROME_SPAWN_FAILED ' + e.message); process.exit(2); });

const cleanup = async () => {
  try { ws?.close(); } catch {}
  child.kill();
  for (let i = 0; i < 20; i++) {
    try { fs.rmSync(profile, { recursive: true, force: true }); break; }
    catch { await sleep(250); }
  }
};

const portFile = path.join(profile, 'DevToolsActivePort');
let port = 0;
for (let i = 0; i < 200 && !port; i++) {
  if (fs.existsSync(portFile)) {
    const first = fs.readFileSync(portFile, 'utf8').trim().split(/\r?\n/)[0];
    if (first) port = Number(first);
  }
  if (!port) await sleep(100);
}
if (!port) { console.error('NO_DEVTOOLS_PORT'); await cleanup(); process.exit(2); }

let ws;
try {
  const version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
  ws = new WebSocket(version.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });

  let id = 0;
  const pending = new Map();
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (d.id && pending.has(d.id)) {
      const { res, rej } = pending.get(d.id);
      pending.delete(d.id);
      d.error ? rej(new Error(JSON.stringify(d.error))) : res(d.result);
    }
  };
  const send = (method, params = {}, sessionId) => new Promise((res, rej) => {
    const mid = ++id;
    pending.set(mid, { res, rej });
    ws.send(JSON.stringify({ id: mid, method, params, ...(sessionId ? { sessionId } : {}) }));
  });

  const { targetId } = await send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await send('Target.attachToTarget', { targetId, flatten: true });
  const S = (m, p) => send(m, p, sessionId);
  await S('Page.enable');
  await S('Runtime.enable');

  const evaluate = async (expression) => {
    const r = await S('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };

  for (const width of widths) {
    const mobile = width <= 500;
    await S('Emulation.setDeviceMetricsOverride', {
      width, height: 900, deviceScaleFactor: 1, mobile, screenWidth: width, screenHeight: 900
    });
    await S('Page.navigate', { url });
    let state = null;
    for (let i = 0; i < 100; i++) {
      await sleep(150);
      try {
        state = await evaluate(`(async () => {
          if (document.readyState !== 'complete') return null;
          await document.fonts.ready;
          return { w: innerWidth, h: innerHeight, sh: document.documentElement.scrollHeight, sw: document.documentElement.scrollWidth };
        })()`);
      } catch { state = null; }
      if (state && state.w === width) break;
    }
    if (!state || state.w !== width) {
      console.error(`WIDTH_MISMATCH asked=${width} got=${JSON.stringify(state)}`);
      await cleanup();
      process.exit(3);
    }

    const height = Math.max(state.sh, 900);
    await S('Emulation.setDeviceMetricsOverride', {
      width, height, deviceScaleFactor: 1, mobile, screenWidth: width, screenHeight: height
    });
    await sleep(300);
    const shot = await S('Page.captureScreenshot', {
      format: 'png', captureBeyondViewport: true,
      clip: { x: 0, y: 0, width, height: state.sh, scale: 1 }
    });
    const file = path.join(dir, `${prefix}-${width}.png`);
    fs.writeFileSync(file, Buffer.from(shot.data, 'base64'));
    console.log(JSON.stringify({ width, innerWidth: state.w, innerHeight: state.h, scrollHeight: state.sh, scrollWidth: state.sw, mobile, file, bytes: fs.statSync(file).size }));
  }

  try { await send('Browser.close'); } catch {}
} catch (e) {
  console.error('CAPTURE_FAILED ' + e.message);
  await cleanup();
  process.exit(4);
}
await cleanup();
console.log('DONE');
