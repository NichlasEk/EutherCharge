import test from 'node:test';import assert from 'node:assert/strict';
import {NY8} from '../emulator/core.mjs';
const cpu=(...words)=>{const r=new Uint16Array(2048);r.set(words);return new NY8(r);};
test('Software INT clears GIE before pending hardware interrupt can steal its vector',()=>{
 for(const enabled of [false,true]){const c=cpu(0x210);c.gie=enabled;c.r[14]=1;c.r[15]=1;c.step();
 assert.equal(c.pc,1);assert.equal(c.gie,false);assert.deepEqual(c.stack,[1]);assert.equal(c.cycles,3);assert.equal(c.interrupts,0);}
});
test('RETIE from software interrupt restores GIE and permits pending hardware IRQ',()=>{
 const c=cpu(0x210,0x11);c.gie=true;c.r[14]=1;c.r[15]=1;c.step();c.step();
 assert.equal(c.pc,8);assert.deepEqual(c.stack,[1]);assert.equal(c.gie,false);assert.equal(c.interrupts,1);
});
test('INTF reads are masked by INTE but stored flags survive disabling',()=>{
 const c=cpu();c.r[15]=255;
 for(let mask=0;mask<256;mask++){c.r[14]=mask;assert.equal(c.read(15),mask);assert.equal(c.r[15],255);}
 c.r[14]=0;c.r[4]=15;assert.equal(c.read(0),0);c.r[14]=8;assert.equal(c.read(0),8);
 c.write(15,0);assert.equal(c.read(15),0);
});
test('Bit read-modify-write on INTF observes masked value; direct writes keep their value',()=>{
 const c=cpu(0x1c0f);c.r[14]=1;c.r[15]=255;c.step();assert.equal(c.r[15],0);
 c.a=255;c.rom[1]=0x008f;c.step();assert.equal(c.r[15],255);assert.equal(c.read(15),1);
});
