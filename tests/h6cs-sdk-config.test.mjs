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
