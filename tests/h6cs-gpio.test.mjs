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
test('Read evidence ignores immediate operands and writes; counts INDF once',()=>{
 const c=cpu();c.rom.set([0x2105,0x0085,0x0285,0x0100]);c.r[4]=6;c.run(3);
 assert.equal(c.gpio.readSummary().reads,0);c.step();const s=c.gpio.readSummary();
 assert.equal(s.reads,1);assert.equal(s.sites[0].address,6);assert.equal(s.unknownReads,1);
});
test('Read evidence tracks consumed bits rather than all unknown port pins',()=>{
 const c=cpu();c.rom.set([0x0a85,0x1805,0x1005,0x1105]);
 c.step();assert.equal(c.gpio.readSummary().unknownReads,0); // known PA5 button
 c.pc=1;c.step();assert.equal(c.gpio.readSummary().unknownReads,1); // BSR preserves other bits
 c.a=32;c.step();assert.equal(c.gpio.readSummary().unknownReads,1); // AND masks unknown bits
 c.a=223;c.step();assert.equal(c.gpio.readSummary().unknownReads,1); // OR forces unknown bits
});
test('Unknown fill sensitivity changes uncertain branch, not latch output reads',()=>{
 for(const fill of [0,255]){const c=cpu();c.gpio.unknownFill=fill;c.rom[0]=0x0806;c.step();
 assert.equal(c.pc,fill?2:1);assert.equal(c.gpio.readSummary().sites[0].kind,'direct-bit-branch');
 c.gpio.mode='latch';c.f[6]=0;c.r[6]=0;assert.equal(c.read(6),0);}
});
test('GPIO reset registers match documented wake and external edge defaults',()=>{
 const c=cpu();assert.equal(c.r[21],255);assert.equal(c.r[9],63);assert.equal(c.r[24],5);
});
test('Port-change flags latch while masked; only selected input transitions count',()=>{
 const c=cpu();c.r[21]=32;c.r[9]=0;c.step();c.pressed=true;c.step();
 assert.equal(c.r[15]&2,2);assert.equal(c.interrupts,0);assert.equal(c.gpio.irqEdges.pab,1);
 c.r[15]&=~2;c.step();assert.equal(c.r[15]&2,0);
 c.r[21]=0;c.pressed=false;c.step();assert.equal(c.r[15]&2,0);
 c.f[5]=0;c.r[21]=1;c.r[5]=0;c.step();c.r[5]=1;c.step();assert.equal(c.r[15]&2,0);
});
test('Pending port flag dispatches with GIE and enable; firmware clears sticky flag',()=>{
 const c=cpu();c.r[21]=32;c.step();c.pressed=true;c.step();c.r[14]=2;c.gie=true;
 const returnPC=c.pc+1;c.step();assert.equal(c.pc,8);assert.deepEqual(c.stack,[returnPC]);assert.equal(c.gie,false);assert.equal(c.r[15]&2,2);
 c.write(15,0);assert.equal(c.r[15]&2,0);
});
test('External edges select polarity and suppress PB0/1 port-change flags',()=>{
 for(const bit of [0,1])for(const mode of [1,2,3]){
  const c=cpu();c.r[21]=0;c.r[9]=1<<bit;c.f[6]=0; // EIS must override GPIO output direction.
  c.r[24]=(16<<bit)|(mode<<(bit*2));c.gpio.external.b[bit]=0;c.step();
  c.gpio.external.b[bit]=1;c.step();const flag=bit?128:4;
  assert.equal(c.r[15]&flag,mode&1?flag:0);assert.equal(c.r[15]&2,0);
  c.r[15]=0;c.gpio.external.b[bit]=0;c.step();assert.equal(c.r[15]&flag,mode&2?flag:0);assert.equal(c.r[15]&2,0);
 }
});
test('Unknown levels, arming and GPIO mode changes do not fabricate IRQ edges',()=>{
 const c=cpu();c.r[21]=0;c.r[9]=0;c.gpio.external.b[0]=0;c.step();
 c.r[24]=19;c.gpio.external.b[0]=1;c.step();assert.equal(c.r[15]&4,0);
 c.gpio.external.b[0]=null;c.step();c.gpio.external.b[0]=0;c.step();assert.equal(c.r[15]&4,0);
 c.gpio.mode='legacy';c.step();c.gpio.external.b[0]=1;c.gpio.mode='pad';c.step();assert.equal(c.r[15]&4,0);
});
test('PWM output override cannot generate an input-change interrupt',()=>{
 const c=cpu();c.r[21]=0;c.r[9]=8;c.s[1]=128;c.timer1.count=2;c.timer1.duty=1;c.step();
 assert.equal(c.gpio.port(c,'b').pins[3].input,false);
 c.timer1.count=0;c.step();assert.equal(c.r[15]&2,0);
});
test('External interrupt dispatch uses PB1 flag and firmware-controlled masking',()=>{
 const c=cpu();c.r[21]=0;c.r[9]=0;c.r[24]=36;c.gpio.external.b[1]=0;c.step();
 c.r[14]=128;c.gie=true;c.gpio.external.b[1]=1;const next=c.pc+1;c.step();
 assert.equal(c.pc,8);assert.deepEqual(c.stack,[next]);assert.equal(c.r[15]&128,128);
 assert.equal(c.gpio.irqEnabledSeen,128);
});
