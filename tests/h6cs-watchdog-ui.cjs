const {firefox}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{const browser=await firefox.launch({headless:true,...(process.env.FIREFOX_EXECUTABLE?{executablePath:process.env.FIREFOX_EXECUTABLE}:{})});try{
 const page=await browser.newPage({viewport:{width:1440,height:1100}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8766');await page.locator('#lab').click();await page.waitForFunction(()=>document.querySelector('#rom').textContent.includes('SHA256'));
 assert.match(await page.locator('#watchdogStatus').textContent(),/Ej konfigurerad/);
 await page.locator('#wdtMode').selectOption('reset');await page.locator('#wdtHz').fill('1000');assert.match(await page.locator('#watchdogStatus').textContent(),/Ej konfigurerad/);
 await page.locator('#wdtApply').click();await page.locator('#burst').click();assert.match(await page.locator('#watchdogStatus').textContent(),/RESET BEGÄRD/);assert.equal(await page.locator('#run').isDisabled(),true);assert.equal(await page.locator('#step').isDisabled(),true);assert.equal(await page.locator('#burst').isDisabled(),true);
 const stoppedSteps=await page.locator('#steps').textContent();await page.locator('#wdtHz').fill('2000000');assert.equal(await page.locator('#steps').textContent(),stoppedSteps);assert.match(await page.locator('#watchdogStatus').textContent(),/RESET BEGÄRD/);
 const download=page.waitForEvent('download');await page.locator('#export').click();await(await download).saveAs('artifacts/h6cs-emulator/watchdog-ui-state.json');
 const state=require('node:fs').readFileSync('artifacts/h6cs-emulator/watchdog-ui-state.json','utf8');const snapshot=JSON.parse(state);assert.equal(snapshot.cpu.watchdog.config.instructionHz,1000);assert.equal(snapshot.cpu.watchdog.resetRequested,true);
 await page.screenshot({path:'artifacts/h6cs-emulator/watchdog-timeout.png',fullPage:true});
 await page.locator('#wdtApply').click();assert.equal(await page.locator('#steps').textContent(),'0');assert.equal(await page.locator('#run').isDisabled(),false);await page.locator('#burst').click();assert.doesNotMatch(await page.locator('#watchdogStatus').textContent(),/RESET BEGÄRD/);
 const steps=await page.locator('#steps').textContent();await page.locator('#wdtHz').fill('1.5');await page.locator('#wdtApply').click();assert.equal(await page.locator('#steps').textContent(),steps);assert.match(await page.locator('#notice').textContent(),/Explicit WDT/);
 await page.locator('#reset').click();assert.match(await page.locator('#watchdogStatus').textContent(),/TESTANTAGANDE/);assert.equal(await page.locator('#steps').textContent(),'0');
 await page.locator('#wdtMode').selectOption('unconfigured');await page.locator('#wdtApply').click();assert.match(await page.locator('#watchdogStatus').textContent(),/Ej konfigurerad/);
 await page.locator('#profile').selectOption('avr');assert.equal(await page.locator('#watchdogInspector').isVisible(),false);assert.deepEqual(errors,[]);
 console.log('PASS Firefox watchdog: explicit apply, timeout interlock, exported active settings, invalid-input preservation, reset and profile visibility');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1)});
