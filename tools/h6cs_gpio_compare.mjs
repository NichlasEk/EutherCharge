#!/usr/bin/env node
// Compare offline reports, not physical measurements or full instruction traces.
import fs from 'node:fs';import assert from 'node:assert/strict';
const paths=process.argv.slice(2);assert.equal(paths.length,4,'Supply four reports: latch/pad × zero/one');
const reports=paths.map(p=>JSON.parse(fs.readFileSync(p,'utf8'))),base=reports[0],b=base.experimental;
const combinations=new Set();
const fields=['steps','cycles','timerMode','t0md','interrupts','overflows','carryOps','adc','adcMode','adcConversions','firstRamWrite','events','finalState','lcdRam','timer1'];
for(const report of reports){
 const e=report.experimental;assert.equal(report.romSha256,base.romSha256);assert.equal(report.physicalCaptureSha256,base.physicalCaptureSha256);
 assert.deepEqual(report.scenario,base.scenario);assert.equal(report.comparison.matches,true);
 assert.equal(e.halted,'');assert.equal(e.steps,e.budget);assert.equal(e.budget,b.budget);
 assert.ok(e.events.length<e.eventLimit,'Event list truncated: cannot claim complete event comparison');
 for(const field of fields)assert.deepEqual(e[field],b[field],`Divergence in ${field}: ${e.gpio.mode}/${e.gpio.unknownFill}`);
 combinations.add(e.gpio.mode+':'+e.gpio.unknownFill);
}
assert.deepEqual([...combinations].sort(),['latch:0','latch:255','pad:0','pad:255']);
console.log(JSON.stringify({result:'equal-within-compared-scope',romSha256:base.romSha256,steps:b.steps,cycles:b.cycles,fields,
 scope:'Events, final LCD RAM and bounded final PWM edge window; not full execution/pad/LCD traces or arbitrary unknown-bit patterns',
 states:b.events.filter(e=>e.name==='state').map(e=>e.to),modes:b.events.filter(e=>e.name==='mode').map(e=>e.to),
 reads:reports.map(r=>({mode:r.experimental.gpio.mode,fill:r.experimental.gpio.unknownFill,...r.experimental.gpio.readEvidence}))},null,2));
