import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import {NY8,parseROM} from '../emulator/core.mjs';
const cpu=()=>{const c=new NY8(new Uint16Array(2048));c.gpio.mode='pad';return c;};
test('Input reads external pin; output read option separates pin from latch',()=>{
 const c=cpu();c.r[5]=1;c.gpio.external.a[0]=0;
 assert.equal(c.read(5)&1,0);c.f[5]&=~1;
 assert.equal(c.gpio.port(c,'a').pins[0].reason,'contention');
 c.gpio.mode='latch';assert.equal(c.read(5)&1,1);
 c.gpio.external.a[0]=null;c.gpio.mode='pad';assert.equal(c.read(5)&1,1);
});
test('Pulls, floating inputs, open drain and PA5 switch resolve separately',()=>{
 const c=cpu();assert.equal(c.gpio.port(c,'b').unknown&1,1);
 c.r[12]&=~1;assert.equal(c.read(6)&1,1);
 c.r[11]&=~16;assert.equal(c.gpio.port(c,'b').pins[0].reason,'opposed-pulls');
 c.r[12]|=1;assert.equal(c.read(6)&1,0);
 c.f[6]&=~1;c.r[6]|=1;c.f[12]|=1;assert.equal(c.read(6)&1,0);
 c.f[12]&=~1;assert.equal(c.read(6)&1,1);
 c.f[5]&=~32;c.r[5]|=32;assert.equal(c.read(5)&32,32);
 c.pressed=true;assert.equal(c.read(5)&32,0);assert.notEqual(c.gpio.port(c,'a').pins[5].reason,'contention');
});
test('Analog-disabled and unsupported mux pins remain explicitly unknown',()=>{
 const c=cpu();c.gpio.external.a[1]=1;c.r[0x16]=2;
 assert.equal(c.gpio.port(c,'a').pins[1].reason,'analog-digital-disabled');
 c.s[15]=64;assert.equal(c.gpio.port(c,'b').pins[3].reason,'unsupported-mux');
});
test('PWM pin read and latch read differ, PB upper general bits are preserved',()=>{
 const c=cpu();c.s[1]=128;c.timer1.count=0;c.timer1.duty=1;c.r[6]=192;c.f[6]=0;
 assert.equal(c.read(6),200);c.gpio.mode='latch';assert.equal(c.read(6),192);
});
test('LCD does not receive writes to input latches; direction change exposes drive',()=>{
 const c=cpu();c.write(5,1);c.write(6,32);c.gpio.syncLCD(c);
 c.write(5,0);c.gpio.syncLCD(c);assert.equal(c.lcd.bits,null);
 c.f[5]=254;c.f[6]=15;c.write(5,1);c.gpio.syncLCD(c);
 c.write(5,0);c.gpio.syncLCD(c);assert.equal(c.lcd.bits,'');
 c.write(6,16);c.gpio.syncLCD(c);c.write(6,48);c.gpio.syncLCD(c);assert.equal(c.lcd.bits,'1');
});
const path='dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin';
test('Private original: both RD_OPT hypotheses reproduce measured LCD boot',{skip:!fs.existsSync(path)},()=>{
 const b=fs.readFileSync(path),rom=parseROM(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));
 for(const mode of ['latch','pad']){const c=new NY8(rom);c.gpio.mode=mode;c.run(20000);assert.equal(c.halted,'');assert.deepEqual(c.lcd.commands,[1,24,40,3]);assert.equal(c.gpio.port(c,'a').unknown&1,0);assert.equal(c.gpio.port(c,'b').unknown&48,0);}
});
