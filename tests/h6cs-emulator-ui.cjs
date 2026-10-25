const {firefox}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const b=await firefox.launch({headless:true,...(process.env.FIREFOX_EXECUTABLE ? {executablePath:process.env.FIREFOX_EXECUTABLE} : {})});
 try{
 const page=await b.newPage({viewport:{width:1440,height:1100}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8766');await page.locator('#lab').click();await page.waitForFunction(()=>document.querySelector('#rom').textContent.includes('SHA256'));
 await page.locator('#burst').click();await page.locator('#burst').click();assert.equal(await page.locator('#commands').textContent(),'01 18 28 03');assert.doesNotMatch(await page.locator('#status').textContent(),/Ej verifierad/);
 await page.locator('#state').fill('7');await page.locator('#setState').click();assert.match(await page.locator('#status').textContent(),/tillstånd 7/);
 await page.locator('#address').fill('40');await page.locator('#value').fill('AB');await page.locator('#write').click();assert.match(await page.locator('#events').textContent(),/40 ← AB/);
 await page.locator('#timer').check();await page.locator('#reset').click();await page.locator('#burst').click();await page.locator('#burst').click();assert.match(await page.locator('#status').textContent(),/carry-opkoder verifierade/);
 await page.locator('#timerMode').selectOption('instruction');await page.locator('#adcMode').selectOption('clocked');await page.locator('#reset').click();await page.locator('#burst').click();await page.locator('#burst').click();assert.doesNotMatch(await page.locator('#status').textContent(),/saknar|Ej verifierad/);
 await page.locator('#photoTest').click();assert.equal(await page.locator('#glassReading').textContent(),'28.0 °C');assert.equal(await page.locator('[data-icon="summer"]').getAttribute('class'),'glass-seg season lit');assert.equal(await page.locator('[data-mode="0"]').getAttribute('class'),'active');assert.ok(await page.locator('#glass .glass-seg.lit').count()>15);
 await page.screenshot({path:'artifacts/h6cs-emulator/original-desktop.png',fullPage:true});
 await page.locator('#sensorTemperature').evaluate(el=>{el.value='28';el.dispatchEvent(new Event('input',{bubbles:true}));});assert.equal(await page.locator('#adc1').inputValue(),'2176');
 await page.locator('#labRun').click();await page.waitForFunction(()=>document.querySelector('#lcdstatus').textContent.includes('80 sparade'));await page.locator('#run').click();assert.ok(await page.locator('#lcdgrid .on').count()>0);
 await page.locator('#profile').selectOption('avr');assert.equal(await page.locator('#plantControls').isVisible(),true);assert.equal(await page.locator('#adcControls').isVisible(),false);await page.locator('#fault').check();await page.locator('#step').click();assert.match(await page.locator('#plantState').textContent(),/STOPP.*0.00 A/);
 await page.locator('#profile').selectOption('stm32');assert.match(await page.locator('#notice').textContent(),/ingen STM32/);assert.match(await page.locator('#supply').textContent(),/nivåanpassning/);
 await page.setViewportSize({width:390,height:844});await page.screenshot({path:'artifacts/h6cs-emulator/model-mobile.png',fullPage:true});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),true);
 await page.locator('#profile').selectOption('ny8');await page.locator('#timer').uncheck();await page.locator('#reset').click();await page.locator('#breakpoint').fill('751');await page.locator('#setBreak').click();await page.locator('#burst').click();await page.locator('#burst').click();assert.match(await page.locator('#status').textContent(),/Brytpunkt 751/);
 const download=page.waitForEvent('download');await page.locator('#export').click();await(await download).saveAs('artifacts/h6cs-emulator/ui-state.json');
 assert.deepEqual(errors,[]);console.log('PASS Firefox: ROM loading, LCD boot, verified carry continuation, state/RAM edit, timer/ADC modes, AVR/STM32, fault, mobile layout, breakpoint, export; no JS errors');
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exit(1)});
