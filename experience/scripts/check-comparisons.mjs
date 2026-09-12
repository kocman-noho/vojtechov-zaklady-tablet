import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || '/usr/bin/google-chrome', headless: true,
  args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
});
// The main suite covers camera animations; asset lifecycle checks also exercise
// the reduced-motion preference and avoid unnecessary software-rendered flights.
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, reducedMotion: 'reduce' });
page.setDefaultTimeout(120000);
const errors = [], requests = [];
page.on('pageerror', error => errors.push(error.message));
page.on('console', message => { if (message.type() === 'error' && /Shader Error|VALIDATE_STATUS|shader.*compile/i.test(message.text())) errors.push(message.text()); });
page.on('request', request => requests.push(request.url()));
let houseAttempts = 0, releaseHouse;
let notifyHouseRetry;
const houseRetryStarted = new Promise(resolve => { notifyHouseRetry = resolve; });
await page.route('**/comparisons/house.glb', async route => {
  houseAttempts++;
  if (houseAttempts === 1) return route.fulfill({ status: 503, body: 'Simulated unavailable model' });
  await new Promise(resolve => { releaseHouse = resolve; notifyHouseRetry(); });
  return route.continue();
});
try {
  await page.goto(process.env.PREVIEW_URL || 'http://127.0.0.1:5173');
  await page.waitForFunction(() => window.foundationExperience?.state().loaded, null, { timeout: 120000 });
  assert.equal(await page.evaluate(() => window.foundationExperience.state().concreteTexture), 'ready');
  assert.equal(houseAttempts, 0, 'Hidden house is not downloaded at startup');
  for (const key of ['man', 'woman', 'car']) {
    assert.equal(await page.evaluate(key => window.foundationExperience.state().comparisons[key], key), 'ready');
    await page.locator(`[data-object="${key}"]`).click();
    assert.equal(await page.evaluate(key => window.foundationExperience.state().objects[key], key), false);
    await page.locator(`[data-object="${key}"]`).click();
    assert.equal(requests.filter(url => url.endsWith(`/comparisons/${key}.glb`)).length, 1, 'Loaded asset reused');
  }
  await page.locator('[data-object="house"]').click();
  await page.waitForFunction(() => window.foundationExperience.state().comparisons.house === 'error');
  assert.match(await page.locator('#comparison-status').textContent(), /Zkuste znovu klepnout/);
  assert.equal(await page.locator('#loading').evaluate(el => el.classList.contains('hidden')), true, 'Optional failure leaves experience usable');
  await page.locator('[data-object="house"]').click();
  await page.waitForFunction(() => document.querySelector('[data-object="house"]').getAttribute('aria-busy') === 'true');
  await page.locator('[data-object="house"]').click();
  // The delayed response must not undo a user's toggle-off while loading.
  await houseRetryStarted;
  assert.ok(releaseHouse, 'Retry request started');
  releaseHouse();
  await page.waitForFunction(() => window.foundationExperience.state().comparisons.house === 'ready');
  assert.equal(await page.evaluate(() => window.foundationExperience.state().objects.house), false);
  await page.locator('[data-object="house"]').click();
  assert.equal(houseAttempts, 2, 'Retry succeeds and subsequent toggles reuse the model');
  const placement = await page.evaluate(() => window.foundationExperience.placement());
  assert.deepEqual(Object.keys(placement.objectBottoms).sort(), ['car', 'house', 'man', 'woman']);
  for (const [key, bottom] of Object.entries(placement.objectBottoms)) {
    assert.ok(Math.abs(bottom - placement.groundLevel) < .00001, `${key} sits on the ground`);
  }
  await page.waitForTimeout(1800);
  fs.mkdirSync('artifacts', { recursive: true });
  await page.screenshot({ path: 'artifacts/comparisons-desktop.png' });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.waitForTimeout(500);
  for (const key of ['man', 'woman', 'car', 'house']) {
    const button = page.locator(`[data-object="${key}"]`);
    await button.click();
    assert.equal(await button.getAttribute('aria-pressed'), 'false');
    await button.click();
  }
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.screenshot({ path: 'artifacts/comparisons-mobile.png', fullPage: true });
  const report = JSON.parse(fs.readFileSync('public/models/comparisons/provenance.json'));
  const totalBytes = Object.values(report.assets).reduce((total, asset) => total + asset.bytes, 0);
  assert.ok(totalBytes < 5_000_000, 'Four models, including the detailed optional house, stay within a 5 MB download budget');
  assert.deepEqual(errors, []);
  console.log(JSON.stringify({ result: 'PASS', totalBytes, placement, checks: ['lazy loading', 'independent toggles', 'asset reuse', 'failure and retry', 'toggle during loading', 'ground contact', 'mobile controls', 'no browser exceptions'] }, null, 2));
} finally {
  releaseHouse?.();
  await browser.close();
}
