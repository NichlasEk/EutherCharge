import test from 'node:test';import assert from 'node:assert/strict';import {NY8} from '../emulator/core.mjs';
function cpu(action='interrupt'){const c=new NY8(new Uint16Array(2048));c.t0md=0;c.watchdog.configure({enabled:true,action,baseUs:3500,instructionHz:1000000});return c;}
test('Unconfigured watchdog makes no hidden clock/config assumption',()=>{const c=new NY8(new Uint16Array(2048));c.watchdog.advance(c,1e8);assert.equal(c.watchdog.timeouts,0);assert.equal(c.watchdog.snapshot(c).config,null);});
test('WDT boundary clears TO and latches flag while masked',()=>{const c=cpu();c.watchdog.advance(c,3499);assert.equal(c.watchdog.timeouts,0);c.watchdog.advance(c,1);assert.equal(c.watchdog.timeouts,1);assert.equal(c.r[3]&16,0);assert.equal(c.r[15]&64,64);assert.equal(c.read(15)&64,0);c.r[14]=64;c.gie=true;c.step();assert.equal(c.pc,8);assert.equal(c.interrupts,1);});
test('CLRWDT clears elapsed interval and assigned prescaler, not sticky WDTIF',()=>{const c=cpu();c.t0md=8;c.watchdog.advance(c,3500);assert.equal(c.watchdog.prescaler,1);c.r[15]=64;c.rom[0]=2;c.step();assert.equal(c.watchdog.credit,1e6);assert.equal(c.watchdog.prescaler,0);assert.equal(c.r[3]&24,24);assert.equal(c.r[15]&64,64);});
test('All watchdog prescalers distinguish reset and interrupt factors',()=>{for(const action of ['reset','interrupt'])for(let select=0;select<8;select++){const c=cpu(action);c.t0md=8|select;const period=3500*2**(select+(action==='interrupt'?1:0));c.watchdog.advance(c,period-1);assert.equal(c.watchdog.timeouts,0);c.watchdog.advance(c,1);assert.equal(c.watchdog.timeouts,1);assert.equal(c.watchdog.resetRequested,action==='reset');}});
test('Runtime gate and fuse-disable prevent timeout; invalid assumptions rejected',()=>{const c=cpu();c.r[8]&=~128;c.watchdog.advance(c,100000);assert.equal(c.watchdog.credit,0);c.r[8]|=128;c.watchdog.configure({enabled:false,action:'reset',baseUs:15000,instructionHz:1000000});c.watchdog.advance(c,100000);assert.equal(c.watchdog.timeouts,0);assert.throws(()=>c.watchdog.configure({}));});
test('Reset timeout stops explicitly instead of pretending a cold-reset sequence',()=>{const c=cpu('reset');c.watchdog.advance(c,3499);c.step();assert.match(c.halted,/reset/);assert.equal(c.watchdog.resetRequested,true);assert.equal(c.step(),false);});
test('All base periods use rational instruction time without rounding milliseconds',()=>{
 for(const baseUs of [3500,15000,60000,250000]){const c=cpu();c.watchdog.configure({enabled:true,action:'interrupt',baseUs,instructionHz:3000000});c.watchdog.advance(c,baseUs*3-1);assert.equal(c.watchdog.timeouts,0);c.watchdog.advance(c,1);assert.equal(c.watchdog.timeouts,1);assert.equal(c.watchdog.credit,0);}
});
test('T0MD assignment clears shared prescale history without clearing watchdog base interval',()=>{
 const c=cpu();c.t0md=8;c.watchdog.advance(c,3600);assert.equal(c.watchdog.prescaler,1);const credit=c.watchdog.credit;c.a=0;c.rom[0]=3;c.step();assert.equal(c.watchdog.prescaler,0);assert.equal(c.watchdog.credit,credit+1000000);
});
import {restartWatchdogExperiment,watchdogStatus} from '../emulator/watchdog-experiment.mjs';
test('Reset request cannot be bypassed by clearing the debug halt message',()=>{
 const c=cpu('reset');c.watchdog.advance(c,3500);const pc=c.pc;c.halted='';assert.equal(c.step(),false);assert.equal(c.pc,pc);assert.match(c.halted,/reset/);
});
test('Experiment restart validates first and only explicit restart changes configuration',()=>{
 const c=cpu();c.run(10);const steps=c.steps;assert.throws(()=>restartWatchdogExperiment(c,{enabled:true}));assert.equal(c.steps,steps);
 const config={enabled:true,action:'reset',baseUs:15000,instructionHz:2000000};restartWatchdogExperiment(c,config);assert.equal(c.steps,0);assert.deepEqual(c.watchdog.config,config);assert.match(watchdogStatus(c),/TESTANTAGANDE/);
 restartWatchdogExperiment(c,null);assert.equal(c.watchdog.config,null);assert.match(watchdogStatus(c),/Ej konfigurerad/);
});
