import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
import{NY8,LCD,Plant,parseROM,decode}from'../emulator/core.mjs';
function program(...w){const rom=new Uint16Array(2048);rom.set(w);return new NY8(rom);}
test('ROM rejects truncation and words above14bits',()=>{assert.throws(()=>parseROM(new ArrayBuffer(4)));let b=new ArrayBuffer(4096);new DataView(b).setUint16(0,0xffff,true);assert.throws(()=>parseROM(b));});
test('Arithmetic carry, borrow, destination and zero',()=>{let c=program(0x21ff,0x2501,0x00c0,0x2101,0x0440);c.run(5);assert.equal(c.a,255);assert.equal(c.r[64],0);assert.equal(c.r[3]&1,0);});
test('RAM banking shared high RAM, INDF and computed PCL',()=>{let c=program();c.r[3]=0;c.write(32,7);c.r[3]=64;c.write(32,9);assert.equal(c.read(32),9);c.r[4]=0xa0;c.write(0,11);assert.equal(c.b1[0],11);c.r[3]=0;assert.equal(c.read(32),7);c.r[10]=3;c.write(2,0x45);assert.equal(c.next,0x345);});
test('Unknown opcodes stop with unchanged PC',()=>{let c=program(0x3600);assert.equal(c.step(),false);assert.equal(c.pc,0);assert.match(c.halted,/Ej verifierad/);});
test('LCD MSB commands and LSB RAM nibbles',()=>{let l=new LCD();l.consume('100000000110');assert.equal(l.enabled,true);l.consume('1010000101001');assert.equal(l.ram[2],9);});
test('ADC packs12bits; preserves clock configuration; clears START',()=>{let c=program();c.r[17]=0xa0;c.adc[2]=0xabc;c.write(16,0xd2);assert.equal(c.r[18],0xab);assert.equal(c.r[17],0xac);assert.equal(c.r[16]&64,0);assert.equal(c.r[16]&32,32);});
test('Stack overflow and timer IRQ',()=>{let c=program(0x2800);c.run(10);assert.match(c.halted,/Stack overflow/);c=program(0);c.timerEnabled=true;c.timerDivider=1;c.f[15]=1;c.r[1]=255;c.r[14]=1;c.gie=true;c.step();assert.equal(c.pc,8);assert.deepEqual(c.stack,[1]);assert.equal(c.gie,false);});
test('Plant fault and battery removal suppress charge',()=>{let p=new Plant();p.tick(1);assert.ok(p.current>0);p.fault=true;p.tick(1);assert.equal(p.current,0);p.fault=false;p.connected=false;p.tick(1);assert.equal(p.current,0);});
const path='dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin';let rom=null;if(fs.existsSync(path)){let b=fs.readFileSync(path);rom=parseROM(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));}
test('Private original: boot LCD matches physical capture and verified carry instructions continue',{skip:!rom},()=>{let c=new NY8(rom);c.run(20000);assert.deepEqual(c.lcd.commands,[1,24,40,3]);assert.ok(c.carryOps>0);assert.equal(c.steps,20000);assert.equal(c.halted,'');});
test('Private original: one million steps, modeled interrupts',{skip:!rom},()=>{let c=new NY8(rom);c.timerEnabled=true;c.run(1e6);assert.equal(c.halted,'');assert.equal(c.steps,1e6);assert.ok(c.carryOps>0);assert.deepEqual(c.lcd.commands.slice(0,4),[1,24,40,3]);});
function routine(c,pc){c.pc=pc;c.stack=[0x7fd];for(let k=0;k<5000;k++){if(c.pc===0x7fd)return;c.step();assert.equal(c.halted,'');}throw Error('routine budget');}
test('Private original: conversion table searched correctly for every8bit input',{skip:!rom},()=>{let table=[...rom.slice(0x47c,0x4bd)].map(w=>w&255);assert.equal(table.length,65);for(let x=0;x<256;x++){let c=new NY8(rom);c.a=x;routine(c,0x71c);let expected=Math.max(0,table.findLastIndex(v=>v<=x));assert.equal(c.a,expected,'input '+x);}});
test('Private original: mode setup constants via actual instructions',{skip:!rom},()=>{let expected=[[281,100,4],[256,100,4],[143,65,4],[256,45,3]];for(let mode=0;mode<4;mode++){let c=new NY8(rom);c.r[75]=mode;routine(c,0x444);assert.deepEqual([c.r[58]|c.r[59]<<8,c.r[52]|c.r[53]<<8,c.r[62]],expected[mode]);}});
import {glassState,displayText,DIGIT_CODES,SEGMENT_BITS,indicatorMode} from '../emulator/display.mjs';
test('Seven-segment digit mapping and decimal independence',()=>{let l=new LCD();l.enabled=true;for(let n=0;n<10;n++){for(let a of [16,14,12]){l.ram[a]=DIGIT_CODES[n]&15;l.ram[a+1]=DIGIT_CODES[n]>>4;}l.ram[14]|=1;assert.equal(displayText(glassState(l)),`${n}${n}.${n}`);}assert.equal(SEGMENT_BITS.g,2);});
test('Private original: photo reference28.0 and four indicator modes from GPIO',{skip:!rom},()=>{let c=new NY8(rom);c.r[5]=1;c.r[6]=32;c.lcd.enabled=true;c.r[0x3e]=4;c.r[0x32]=2800&255;c.r[0x33]=2800>>8;c.r[0x4e]=5;c.r[0x4c]=5;c.b1[12]=5;routine(c,0x13);let gs=glassState(c.lcd);assert.equal(displayText(gs),'28.0');assert.equal(gs.celsius,true);assert.equal(gs.summer,true);assert.equal(c.lcd.frames.length,5);for(let mode=0;mode<4;mode++){let t=new NY8(rom);t.r[75]=mode;t.b1[2]=4;routine(t,0x4bd);assert.equal(indicatorMode(t),mode);}});
test('Private original: accelerated lab timer produces RAM writes through main loop',{skip:!rom},()=>{let c=new NY8(rom);c.timerEnabled=true;c.timerDivider=1;c.run(400000);assert.equal(c.halted,'');assert.ok(c.lcd.frames.some(f=>f.startsWith('101')));assert.ok([...c.lcd.ram].some(Boolean));});
test('Private original:65temperature points pass through100-sample ADC conversion',{skip:!rom},()=>{for(let temp=-15;temp<=49;temp++){let c=new NY8(rom);c.adc[1]=(rom[0x47c+temp+15]&255)*16;for(let j=0;j<100;j++)routine(c,0x28c);assert.equal((c.r[50]|c.r[51]<<8),temp*100&65535,'temperature '+temp);}});
test('CMPAR preserves DC and all non-Z/C flags across every byte pair',()=>{
 const c=program(0x36c0);
 for(let x=0;x<256;x++)for(let y=0;y<256;y++)for(const dc of [0,2]){
  c.pc=0;c.a=y;c.r[64]=x;c.r[3]=0xf8|dc;c.step();
  assert.equal(c.a,y);assert.equal(c.r[64],x);
  assert.equal(c.r[3],0xf8|dc|(x>=y?1:0)|(x===y?4:0));
 }
});
test('CLRWDT restores TO/PD without changing arithmetic flags or timer prescaler',()=>{
 const c=program(2);c.r[3]=0xc7;c.timerPhase=7;c.step();assert.equal(c.r[3],0xdf);assert.equal(c.timerPhase,7);
});
test('PCON1 read reflects ENI/DISI and cannot set GIE with IOST',()=>{
 const c=program(4,0x1f,0x13,0x1f,0x21ff,0x0f,0x1f);
 c.f[15]=0x1d;c.run(2);assert.equal(c.a,0x9d);c.run(2);assert.equal(c.a,0x1d);
 c.run(3);assert.equal(c.gie,false);assert.equal(c.a,0x7f);
});
test('Instruction Timer0 counts branch/skip cycles, prescaling and masked overflows',()=>{
 const c=program(0,0x3800);c.timerMode='instruction';c.timerEnabled=true;c.f[15]=1;c.t0md=0;
 c.run(2);assert.equal(c.cycles,3);assert.equal(c.r[1],1);assert.equal(c.timerPhase,1);
 c.r[1]=255;c.step();assert.equal(c.r[1],0);assert.equal(c.r[15]&1,1);assert.equal(c.interrupts,0);
 const s=program(0x0c40,0,0);s.timerMode='instruction';s.timerEnabled=true;s.f[15]=1;s.t0md=8;s.step();
 assert.equal(s.pc,2);assert.equal(s.cycles,2);assert.equal(s.r[1],2);
});
test('Timer0 source and enable gate clocks; T0MD clears assigned prescaler',()=>{
 const c=program(3);c.timerMode='instruction';c.timerEnabled=true;c.f[15]=1;
 c.t0md=32;c.advanceTimer(100);assert.equal(c.r[1],0);
 c.t0md=3;c.advanceTimer(31);assert.equal(c.r[1],1);assert.equal(c.timerPhase,15);
 c.f[15]=0;c.advanceTimer(100);assert.equal(c.timerPhase,15);
 c.a=3;c.step();assert.equal(c.timerPhase,0);
});
test('Private original: instruction-clock Timer0 drives LCD from reset without RAM injection',{skip:!rom},()=>{
 const c=new NY8(rom);c.timerEnabled=true;c.timerMode='instruction';c.run(4000000);
 assert.equal(c.halted,'');assert.equal(c.t0md,3);assert.ok(c.interrupts>=500);
 assert.ok(c.lcd.frames.some(f=>f.startsWith('101')));assert.ok([...c.lcd.ram].some(Boolean));
});
test('Candidate reset initializes documented control bits, not arbitrary zero controls',()=>{
 const c=program();assert.equal(c.r[8],0x98);assert.equal(c.r[11],255);assert.equal(c.f[6],63);assert.equal(c.f[15],0x1d);assert.equal(c.t0md,0x3f);
});
test('NY8 short CALL/GOTO use PCHBUF, not executing instruction page',()=>{
 const c=program(0x3155);c.r[10]=6;c.step();assert.equal(c.pc,0x655);assert.deepEqual(c.stack,[1]);
 const g=program(0x3355);g.r[10]=4;g.step();assert.equal(g.pc,0x555);
 assert.equal(decode(0x3155,0).target,null);
});
import {adcDuration} from '../emulator/adc.mjs';
test('ADC conversion periods reproduce manufacturer table31 examples',()=>{
 assert.equal(adcDuration(0,14),352); // 22 ADCLK, FINST/16
 assert.equal(adcDuration(32,2),15);assert.equal(adcDuration(32,1),13);assert.equal(adcDuration(32,0),11);
});
test('Clocked ADC waits, completes, sets interrupt flag and captures raw stimulus',()=>{
 const c=program();c.adcMode='clocked';c.r[17]=32;c.r[20]=2;c.adc[2]=0xabc;c.write(16,0xd2);
 assert.equal(c.r[16]&96,0);c.adc[2]=123;c.adcPeripheral.advance(c,14);assert.equal(c.r[16]&32,0);
 c.adcPeripheral.advance(c,1);assert.equal(c.r[16]&32,32);assert.equal(c.r[18],0xab);assert.equal(c.r[17],0xac);
 assert.equal(c.adcPeripheral.conversions,1);
});
test('Clocked ADC rejects unsupported input modes and dispatches enabled completion IRQ',()=>{
 const c=program();c.adcMode='clocked';assert.throws(()=>c.write(16,0xc1),/GCHS/);
 c.r[17]=0x60;c.r[20]=2;c.write(16,0xd1);c.gie=true;c.run(15);
 assert.equal(c.pc,8);assert.equal(c.interrupts,1);assert.equal(c.gie,false);
});
test('Private original: clocked ADC and instruction Timer0 run from reset',{skip:!rom},()=>{
 const c=new NY8(rom);c.timerEnabled=true;c.timerMode='instruction';c.adcMode='clocked';c.run(4000000);
 assert.equal(c.halted,'');assert.ok(c.adcPeripheral.conversions>1000);assert.ok(c.lcd.frames.some(f=>f.startsWith('101')));
});
test('Clocked ADC data buffers resist firmware writes while controls remain writable',()=>{
 const c=program();c.adcMode='clocked';c.r[17]=0x0b;c.r[18]=0xac;
 c.write(17,0x70);c.write(18,0);assert.equal(c.r[17],0x7b);assert.equal(c.r[18],0xac);
});
test('Private original: MODE debouncing and hold suppression run through timer/main-loop polling',{skip:!rom},()=>{
 const c=new NY8(rom);c.timerEnabled=true;c.timerMode='instruction';c.adcMode='clocked';
 c.run(50000);assert.equal(c.r[75],0);
 for(const mode of [1,2,3,0]){
  c.pressed=true;c.run(150000);assert.equal(c.r[75],mode);assert.equal(c.halted,'');
  c.run(100000);assert.equal(c.r[75],mode,'held key must not repeat');
  c.pressed=false;c.run(50000);
 }
});
import{validateScenario,applyStimulus}from'../emulator/scenario.mjs';
test('External-input scenarios reject invalid ranges, time order and hidden RAM edits',()=>{
 for(const actions of [[{atStep:10}],[{atStep:2},{atStep:1}],[{atStep:0,ram:4}],[{atStep:0,adc:{1:4096}}],[{atStep:0,pressed:1}]])assert.throws(()=>validateScenario(actions,10));
 const c=program(),action=validateScenario([{atStep:0,pressed:true,adc:{1:2176}}],10)[0];applyStimulus(c,action);
 assert.equal(c.pressed,true);assert.equal(c.adc[1],2176);assert.equal(c.r[75],0);
});
test('384 manufacturer-assembled carry encodings decode with correct operand and destination',()=>{
 const fixture=JSON.parse(fs.readFileSync(new URL('./fixtures/h6cs/nyasm-carry.json',import.meta.url)));
 assert.equal(fixture.cases.length,384);
 for(const entry of fixture.cases){
  const c=program(entry.word);c.a=2;c.r[entry.register]=5;c.r[3]=1;
  assert.equal(decode(entry.word).name,entry.name);assert.equal(c.step(),true);
  const expected=entry.name==='ADCAR'?8:3;
  assert.equal(entry.destination?c.r[entry.register]:c.a,expected);
  assert.equal(entry.destination?c.a:c.r[entry.register],entry.destination?2:5);
 }
});
test('Verified ADCAR/SBCAR arithmetic and flags for every pair and carry input',()=>{
 for(const [word,name]of [[0x3440,'ADCAR'],[0x3540,'SBCAR']]){
  const c=program(word);
  for(let x=0;x<256;x++)for(let y=0;y<256;y++)for(let carry=0;carry<2;carry++){
   c.pc=0;c.r[64]=x;c.a=y;c.r[3]=0xd8|carry;c.step();
   const sum=name==='ADCAR'?x+y+carry:x+(255-y)+carry;
   const low=name==='ADCAR'?(x&15)+(y&15)+carry:(x&15)+(15-(y&15))+carry;
   assert.equal(c.a,sum&255);assert.equal(c.r[3],0xd8|(sum>255?1:0)|(low>15?2:0)|((sum&255)===0?4:0));
  }
 }
});
test('Private original: external feedback scenario reaches state5 without RAM injection',{skip:!rom},()=>{
 const c=new NY8(rom);c.timerEnabled=true;c.timerMode='instruction';c.adcMode='clocked';
 const actions=validateScenario(JSON.parse(fs.readFileSync(new URL('./fixtures/h6cs/feedback-state5.json',import.meta.url))),4000000);
 applyStimulus(c,actions[0]);c.run(4000000);assert.equal(c.halted,'');assert.equal(c.r[62],5);
});
test('Private original:50-sample ADC2/3 accumulation clamps1300 and divides sum by32',{skip:!rom},()=>{
 for(const raw of [0,1,32,1299,1300,1301,4095]){
  const c=new NY8(rom);
  for(let n=0;n<50;n++){c.r[0x2a]=raw&255;c.r[0x2b]=raw>>8;c.r[0x2e]=raw&255;c.r[0x2f]=raw>>8;routine(c,0x3f4);}
  const expected=Math.floor(Math.min(raw,1300)*50/32);
  assert.equal(c.r[0x2c]|c.r[0x2d]<<8,expected);assert.equal(c.r[0x30]|c.r[0x31]<<8,expected);assert.equal(c.r[0x4d]&4,4);
 }
});
test('Private original: high ADC2-derived value latches flag after20 qualifying windows',{skip:!rom},()=>{
 const c=new NY8(rom);
 c.r[0x2c]=1649&255;c.r[0x2d]=1649>>8;for(let n=0;n<30;n++)routine(c,0x613);assert.equal(c.r[0x4f]&2,0);
 c.r[0x2c]=1650&255;c.r[0x2d]=1650>>8;for(let n=0;n<19;n++)routine(c,0x613);assert.equal(c.r[0x4f]&2,0);
 routine(c,0x613);assert.equal(c.r[0x4f]&2,2);c.r[0x2c]=c.r[0x2d]=0;routine(c,0x613);assert.equal(c.r[0x4f]&2,2);
});
test('Private original: eligibility flag thresholds and1000-poll release delay',{skip:!rom},()=>{
 for(const [feedback,feedback4,set]of [[1359,19,0],[1360,19,1],[1359,20,1]]){
  const c=new NY8(rom);c.r[0x2c]=feedback&255;c.r[0x2d]=feedback>>8;c.r[0x38]=feedback4;
  routine(c,0x532);assert.equal(c.r[0x4d]&1,set);
 }
 const c=new NY8(rom);c.r[0x4d]=1;for(let n=0;n<999;n++)routine(c,0x532);assert.equal(c.r[0x4d]&1,1);
 routine(c,0x532);assert.equal(c.r[0x4d]&1,0);
});
test('Private original: state2 gating and state4 consumes two averaging-ready events',{skip:!rom},()=>{
 for(let flags=0;flags<4;flags++)for(let mode=0;mode<4;mode++){
  const c=new NY8(rom);c.r[0x3e]=2;c.r[0x4b]=mode;c.r[0x4d]=flags&1;c.r[0x4e]=(flags>>1)&1;
  routine(c,0x439);assert.equal(c.r[0x3e],flags===3?(mode===3?3:4):2);
 }
 const c=new NY8(rom);c.r[0x3e]=4;c.r[0x4d]=2;routine(c,0x63c);assert.equal(c.r[0x3e],4);assert.equal(c.r[0x4d]&2,0);
 routine(c,0x63c);assert.equal(c.r[0x3e],4);c.r[0x4d]|=2;routine(c,0x63c);assert.equal(c.r[0x3e],5);
});
