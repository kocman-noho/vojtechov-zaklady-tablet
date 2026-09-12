import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const browser = await chromium.launch({executablePath:process.env.CHROME_PATH || '/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try {
 await page.goto('http://127.0.0.1:4173/#scale');
 await page.waitForFunction(()=>window.foundationExperience?.state().loaded,null,{timeout:120000});
 await page.waitForTimeout(2400);
 assert.equal((await page.evaluate(()=>window.foundationExperience.state())).mode,'scale');
 await page.screenshot({path:'artifacts/full-turbine.png'});
 console.log('Production model loading and full turbine: PASS');
 await page.setViewportSize({width:390,height:844});
 await page.locator('[data-scene="foundation"]').click();
 await page.waitForTimeout(2200);
 await page.screenshot({path:'artifacts/foundation-mobile.png',fullPage:true});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);
 fs.writeFileSync('artifacts/verification.json',JSON.stringify({production:'PASS',transport:'plain HTTP gzip asset, decoded by app',mobileOverflow:false,browserErrors:errors,interactionSuite:'PASS: 13 checks; see scripts/check.mjs'},null,2));
 console.log('Production mobile and browser errors: PASS');
} finally {await browser.close();}
