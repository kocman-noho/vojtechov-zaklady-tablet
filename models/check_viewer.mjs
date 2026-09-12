// Smoke-test the actual offline viewer in a running headless Chrome CDP session.
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
const [profile, screenshot] = process.argv.slice(2);
const port = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0];
const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
const target = targets.find(t => t.type === 'page');
const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve => socket.addEventListener('open', resolve, {once: true}));
let id = 0;
const pending = new Map(), errors = [];
socket.addEventListener('message', event => {
  const m = JSON.parse(event.data);
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params);
  if (pending.has(m.id)) {
    const {resolve, reject} = pending.get(m.id);
    pending.delete(m.id);
    m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
  }
});
function send(method, params = {}) {
  const key = ++id;
  return new Promise((resolve, reject) => {
    pending.set(key, {resolve, reject});
    socket.send(JSON.stringify({id: key, method, params}));
  });
}
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', {expression, returnByValue: true});
  if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
await send('Runtime.enable');
await send('Page.enable');
await send('Page.navigate', {url: pathToFileURL(path.resolve('models/output/preview.html')).href});
let ready = false;
for (let i = 0; i < 120; i++) {
  ready = await evaluate('Boolean(window.foundationViewer)');
  if (ready) break;
  await new Promise(resolve => setTimeout(resolve, 250));
}
if (!ready) throw Error('Viewer did not initialize');
const checks = [];
for (const mode of ['closed', 'cutaway', 'reference']) {
  const state = await evaluate(`document.querySelector('[data-mode="${mode}"]').click(); window.foundationViewer.state()`);
  if (state.mode !== mode) throw Error('Tab failed: ' + mode);
  checks.push(state);
}
const hidden = await evaluate(`document.querySelector('#upper').click(); window.foundationViewer.state()`);
if (hidden.showUpper !== false) throw Error('Upper reinforcement toggle failed');
await evaluate(`document.querySelector('#upper').click(); document.querySelector('#explode').value=.4; document.querySelector('#explode').dispatchEvent(new Event('input'));`);
if ((await evaluate('window.foundationViewer.state()')).explosion !== .4) throw Error('Explode control failed');
await evaluate(`document.querySelector('#reset').click(); document.querySelector('[data-mode="reference"]').click()`);
await new Promise(resolve => setTimeout(resolve, 500));
const capture = await send('Page.captureScreenshot', {format: 'png'});
fs.writeFileSync(screenshot, Buffer.from(capture.data, 'base64'));
if (errors.length) throw Error(JSON.stringify(errors));
console.log(JSON.stringify({tabs: checks.map(s => s.mode), upper_toggle: 'PASS', explode: 'PASS', js_errors: errors.length}));
await send('Browser.close');
socket.close();
