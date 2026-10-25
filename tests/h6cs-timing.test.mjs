import test from 'node:test';import assert from 'node:assert/strict';
import {NY8} from '../emulator/core.mjs';
const cpu=word=>{const rom=new Uint16Array(2048);rom[0]=word;const c=new NY8(rom);c.timerEnabled=true;c.timerMode='instruction';c.f[15]=1;return c;};
test('T0MD assignment clears prescaler after instruction; next full period is required',()=>{
 const c=cpu(3);c.a=3;c.t0md=3;c.timerPhase=15;c.r[1]=7;c.step();
 assert.equal(c.timerPhase,0);assert.equal(c.r[1],7);
 c.run(15);assert.equal(c.r[1],7);assert.equal(c.timerPhase,15);
 c.step();assert.equal(c.r[1],8);assert.equal(c.timerPhase,0);
});
test('T0MD changes divisor without converting old prescaler phase into many ticks',()=>{
 const c=cpu(3);c.a=0;c.t0md=7;c.timerPhase=200;c.r[1]=100;c.step();
 assert.equal(c.timerPhase,0);assert.equal(c.r[1],100);c.run(2);assert.equal(c.r[1],101);
});
test('Documented fixed instruction cycle costs advance enabled peripherals',()=>{
 const cases=[[0,1],[0x2101,1],[0x280a,2],[0x380a,2],[0x0212,2],[0x0213,2],[0x0211,2],[0x0010,2],[0x0011,2],[0x2003,2],[0x0210,3]];
 for(const [word,cycles]of cases){const c=cpu(word);c.t0md=8;c.stack=[20];c.step();assert.equal(c.halted,'');assert.equal(c.cycles,cycles,word.toString(16));assert.equal(c.r[1],cycles);}
});
test('Taken and untaken skips consume two and one cycles respectively',()=>{
 for(const [word,values]of [[0x0840,[0,1]],[0x0c40,[1,0]],[0x1640,[1,255]],[0x1740,[2,1]]]){
  for(let taken=0;taken<2;taken++){const c=cpu(word);c.r[64]=values[taken];c.t0md=8;c.step();assert.equal(c.cycles,taken+1);assert.equal(c.pc,taken+1);assert.equal(c.r[1],taken+1);}
 }
});
