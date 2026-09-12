import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome',
  headless: true, args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const context = await browser.newContext({ viewport: { width: 1024, height: 768 }, hasTouch: true,
  isMobile: true, deviceScaleFactor: 1, reducedMotion: 'reduce' });
const page = await context.newPage();
page.setDefaultTimeout(120000);
const errors = [], requests = [];
page.on('pageerror', e => errors.push(e.message));
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('request', r => requests.push(r.url()));
const url = process.env.PREVIEW_URL || 'http://127.0.0.1:4175';
fs.mkdirSync('artifacts', { recursive: true });

async function checkLayout() {
  const result = await page.evaluate(() => {
    const rect = selector => {
      const r = document.querySelector(selector).getBoundingClientRect();
      return { x: r.x, y: r.y, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
    };
    const visible = el => el.getClientRects().length && getComputedStyle(el).visibility !== 'hidden';
    const targets = [...document.querySelectorAll('button,input[type=range]')].filter(visible).map(el => ({
      name: el.id || el.textContent.trim(), width: el.getBoundingClientRect().width, height: el.getBoundingClientRect().height,
    }));
    return { width: innerWidth, height: innerHeight, scrollWidth: document.documentElement.scrollWidth,
      scrollHeight: document.documentElement.scrollHeight, viewport: rect('#viewport'), header: rect('.header'),
      compare: rect('.compare-panel'), dock: rect('.explore-dock'), targets,
      lang: document.documentElement.lang, sidebars: document.querySelectorAll('.intro,footer').length,
      allControlsInBars: [...document.querySelectorAll('button,input[type=range]')].filter(visible).every(el => el.closest('.header,.explore-dock')) };
  });
  assert.ok(result.scrollWidth <= result.width, 'No horizontal overflow');
  assert.ok(result.scrollHeight <= result.height + 1, 'Tablet controls fit without page scrolling');
  assert.ok(result.viewport.height >= 280, 'Useful model area');
  assert.equal(result.lang, 'cs');
  assert.equal(result.sidebars, 0, 'Sidebar copy and extra footer removed');
  assert.equal(result.allControlsInBars, true, 'Controls live only in the two floating bars');
  assert.equal(result.viewport.width, result.width, '3D fills screen width');
  assert.equal(result.viewport.height, result.height, '3D fills screen height');
  assert.ok(result.dock.y > result.header.bottom + result.height * .45, 'Generous clear model area between bars');
  for (const target of result.targets) {
    assert.ok(target.width >= 44 && target.height >= 44, `${target.name} has a 44 px touch target (${target.width} × ${target.height})`);
  }
  console.log(`PASS layout ${result.width} × ${result.height}; canvas ${Math.round(result.viewport.width)} × ${Math.round(result.viewport.height)}`);
}

try {
  // Direct navigation to full picture must not download any comparison models.
  await page.goto(url + '/#scale');
  await page.waitForFunction(() => window.foundationExperience?.state().loaded);
  assert.equal(requests.some(u => /comparisons\/.*\.glb/.test(u)), false);
  assert.deepEqual(Object.values(await page.evaluate(() => window.foundationExperience.state().objects)), [false, false, false, false]);
  assert.equal(await page.locator('.compare-panel').isVisible(), false);
  assert.equal(await page.locator('.dock-content').isVisible(), false);
  await checkLayout();
  await page.screenshot({ path: 'artifacts/ipad-full-turbine.png' });
  await page.locator('[data-scene="foundation"]').tap();
  await page.waitForFunction(() => ['man', 'woman', 'car'].every(k => window.foundationExperience.state().comparisons[k] === 'ready'));
  await checkLayout();
  await page.screenshot({ path: 'artifacts/ipad-landscape.png' });
  assert.match(await page.locator('#viewport').getAttribute('aria-label'), /Jedním prstem/);
  assert.ok(await page.locator('.model-label:not([data-hidden="true"])').count() > 0, 'Model tags are retained');
  assert.match(await page.locator('#labels').textContent(), /26,6 m/);
  await page.locator('[data-object="man"]').tap();
  let releaseHouse, notifyHouse;
  const houseStarted = new Promise(resolve => { notifyHouse = resolve; });
  await page.route('**/comparisons/house.glb', async route => {
    await new Promise(resolve => { releaseHouse = resolve; notifyHouse(); });
    await route.continue();
  });
  await page.locator('[data-object="house"]').tap();
  await houseStarted;
  const selections = await page.evaluate(() => window.foundationExperience.state().objects);
  await page.locator('[data-scene="scale"]').tap();
  releaseHouse();
  await page.waitForFunction(() => window.foundationExperience.state().comparisons.house === 'ready');
  assert.equal(selections.house, true);
  assert.ok(Math.abs((await page.evaluate(() => window.foundationExperience.bounds())).comparisons.house[1] - 9.08017) < .002);
  assert.ok(Object.values(await page.evaluate(() => window.foundationExperience.state().objects)).every(v => !v));
  for (const button of await page.locator('[data-object]').all()) assert.equal(await button.getAttribute('aria-pressed'), 'false');
  await page.locator('[data-scene="foundation"]').tap();
  assert.deepEqual(await page.evaluate(() => window.foundationExperience.state().objects), selections, 'Selections restored after full picture');
  assert.equal(requests.filter(u => u.endsWith('/comparisons/house.glb')).length, 1, 'House cache preserved');

  await page.locator('[data-scene="deconstruct"]').tap();
  await page.waitForFunction(() => window.foundationExperience.state().explosion > .65);
  await checkLayout();
  const slider = await page.locator('#explode').boundingBox();
  await page.touchscreen.tap(slider.x + slider.width * .75, slider.y + slider.height / 2);
  assert.ok((await page.evaluate(() => window.foundationExperience.state().targetExplosion)) > .65, 'Touch scrubbing changes separation');
  await page.locator('[data-layer="steel"]').tap();
  assert.equal(await page.evaluate(() => window.foundationExperience.state().layers.steel), false);
  await page.locator('[data-layer="steel"]').tap();
  await page.locator('#reset').tap();
  assert.equal(await page.evaluate(() => window.foundationExperience.state().targetExplosion), 0);
  await page.locator('[data-scene="foundation"]').tap();

  const cdp = await context.newCDPSession(page);
  const canvas = await page.locator('canvas').boundingBox();
  const x = canvas.x + canvas.width / 2, y = canvas.y + canvas.height / 2;
  const beforeOrbit = await page.evaluate(() => window.foundationExperience.view());
  const layersBeforeGesture = await page.evaluate(() => window.foundationExperience.state().layers);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x, y, id: 1 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x + 80, y: y + 20, id: 1 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  assert.notDeepEqual((await page.evaluate(() => window.foundationExperience.view())).position, beforeOrbit.position, 'One-finger drag orbits');
  const beforePinch = await page.evaluate(() => window.foundationExperience.view().distance);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: x - 35, y, id: 1 }, { x: x + 35, y, id: 2 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: x - 65, y, id: 1 }, { x: x + 65, y, id: 2 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  assert.ok((await page.evaluate(() => window.foundationExperience.view().distance)) < beforePinch, 'Pinch zooms closer');
  assert.deepEqual(await page.evaluate(() => window.foundationExperience.state().layers), layersBeforeGesture, 'Orbit/pinch do not toggle a component');
  await page.locator('#reset').tap();

  for (const [width, height] of [[768, 1024], [1194, 834], [834, 1194], [1366, 1024], [1024, 1366], [744, 1133], [1133, 744]]) {
    await page.setViewportSize({ width, height });
    await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
    await checkLayout();
    if (width === 768) await page.screenshot({ path: 'artifacts/ipad-portrait.png' });
  }
  await page.locator('#about-button').tap();
  assert.equal(await page.locator('dialog').isVisible(), true);
  await page.locator('#close-about').tap();
  assert.equal(await page.locator('dialog').isVisible(), false);
  assert.deepEqual(errors, []);
  console.log('PASS: full-picture isolation and restoration, direct-link loading, cached house, touch controls, eight iPad viewports, modal, no browser errors.');
} catch (error) {
  await page.screenshot({ path: 'artifacts/ipad-error.png' });
  console.log('Browser errors:', errors);
  throw error;
} finally { await browser.close(); }
