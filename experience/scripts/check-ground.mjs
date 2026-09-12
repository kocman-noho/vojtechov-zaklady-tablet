import {chromium} from 'playwright';
import assert from 'node:assert/strict';
const browser=await chromium.launch({executablePath:process.env.CHROME_PATH || '/usr/bin/google-chrome',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1440,height:1000}}), errors=[];
page.on('pageerror',e=>errors.push(e.message));
try {
 await page.goto('http://127.0.0.1:4173/#foundation');
 await page.waitForFunction(()=>window.foundationExperience?.state().loaded,null,{timeout:120000});
 await page.waitForTimeout(1800);
 const placement=await page.evaluate(()=>window.foundationExperience.placement());
 for(const y of Object.values(placement.objectBottoms)) assert.ok(Math.abs(y+.15)<1e-5,'Objects at finished ground');
 await page.screenshot({path:'artifacts/ground-cutaway-desktop.png'});
 console.log('PASS: ground-level comparison objects; desktop cutaway captured.');
 await page.locator('[data-scene="deconstruct"]').click();
 await page.locator('#explode').focus();await page.keyboard.press('End');
 await page.waitForFunction(()=>window.foundationExperience.state().explosion>.99,null,{timeout:30000});
 assert.ok((await page.evaluate(()=>window.foundationExperience.placement())).concreteBottom>-.15,'Exploded concrete clears ground');
 await page.screenshot({path:'artifacts/ground-cutaway-exploded.png'});
 await page.locator('[data-scene="foundation"]').click();
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(2000);
 await page.screenshot({path:'artifacts/ground-cutaway-mobile.png',fullPage:true});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 assert.deepEqual(errors,[]);
 console.log('PASS: exploded clearance, mobile layout, no browser errors.');
}finally{await browser.close();}
