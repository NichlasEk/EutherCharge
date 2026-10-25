import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {readSdkConfigWindow} from '../emulator/sdk-config.mjs';
const golden=JSON.parse(fs.readFileSync(new URL('./fixtures/h6cs/sdk-config-layout.json',import.meta.url)));
test('SDK window field extraction matches manufacturer one-hot probe',()=>{
 assert.equal(golden.oneHotChecks,3072);
 for(let bit=0;bit<144;bit++){
  const bytes=new Uint8Array(18);bytes[bit>>3]=1<<(bit&7);const actual=readSdkConfigWindow(bytes);
  for(const [name,hits]of Object.entries(golden.fields)){const hit=hits.find(h=>h.byte===(bit>>3)&&h.bit===(bit&7));assert.equal(actual[name],hit?.value??0,name+' bit'+bit);}
 }
});
test('Combined fields remain independent; ROM-sized input is rejected',()=>{
 assert.deepEqual(readSdkConfigWindow(new Uint8Array(18).fill(255)),{wdtReg:1,wdtEventReg:1,wdtTimeBaseReg:3,rdPortTypeReg:1,instClockReg:1,instructionClockReg:1});
 for(const size of [0,4,17,19,4096])assert.throws(()=>readSdkConfigWindow(new Uint8Array(size)));
 assert.throws(()=>readSdkConfigWindow(Array(18).fill(0)));
});
import {decodeNy8B062dSdkConfig} from '../emulator/sdk-config.mjs';
const decoded=JSON.parse(fs.readFileSync(new URL('./fixtures/h6cs/sdk-config-decoded.json',import.meta.url)));
test('32-byte profile decoder matches all32 manufacturer-reader combinations',()=>{
 assert.equal(decoded.cases.length,32);assert.equal(decoded.sizeWords,16);
 for(const c of decoded.cases){const bytes=new Uint8Array(32);bytes[1]=c.bits&3;bytes[12]=((c.bits>>2)&3)<<4;bytes[17]=((c.bits>>4)&1)<<2;
  const actual=decodeNy8B062dSdkConfig(bytes,decoded.configVersion);
  assert.equal(actual.watchdogEnabled,c.Wdt==='ENABLE');assert.equal(actual.watchdogEvent,c.WdtEvent.toLowerCase());
  assert.equal(actual.watchdogBaseUs,{Ms250:250000,Ms60:60000,Ms3_5:3500,Ms15:15000}[c.WdtTimeBase]);
  assert.equal(actual.gpioReadSource,c.ReadIoSource==='FromPin'?'pad':'latch');
 }
});
test('Decoder requires explicit verified version and separate full config block',()=>{
 for(const size of [0,4,18,31,33,4096])assert.throws(()=>decodeNy8B062dSdkConfig(new Uint8Array(size),3));
 for(const v of [undefined,0,1,2,4,'3'])assert.throws(()=>decodeNy8B062dSdkConfig(new Uint8Array(32),v));
});
