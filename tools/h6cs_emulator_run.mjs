#!/usr/bin/env node
// Offline only: no USB, network, firmware writes, or ROM bytes in the report.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {NY8,parseROM} from '../emulator/core.mjs';
const [romPath,capturePath,budgetText='4000000',adcMode='clocked']=process.argv.slice(2);
if(!['instant','clocked'].includes(adcMode))throw Error('ADC mode must be instant or clocked');
if(!romPath||!capturePath)throw Error('Usage: node tools/h6cs_emulator_run.mjs ROM.bin LCD-capture.json [instruction-budget] [clocked|instant]');
const budget=Number(budgetText);
if(!Number.isSafeInteger(budget)||budget<1||budget>100000000)throw Error('Budget must be 1..100000000');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(romPath),captureBytes=fs.readFileSync(capturePath);
const capture=JSON.parse(captureBytes);
const reference=capture.frames.filter(f=>f.complete_end&&!f.trigger_boundary&&f.decode==='command_frame_candidate').map(f=>f.bits);
if(!reference.length)throw Error('No complete physical command frames to compare');
const rom=parseROM(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));
const strict=new NY8(rom);strict.run(20000);
const generated=strict.lcd.frames.slice(0,reference.length);
const matches=reference.length===generated.length&&reference.every((b,i)=>b===generated[i]);
const cpu=new NY8(rom);cpu.experimental=true;cpu.timerEnabled=true;cpu.timerMode='instruction';cpu.adcMode=adcMode;
const events=[];let oldState=cpu.r[0x3e],oldMode=cpu.r[0x4b],oldDuty=cpu.s[3],firstRamWrite=null;
for(let i=0;i<budget;i++){
 const pc=cpu.pc;
 if(!cpu.step())break;
 if(firstRamWrite===null&&cpu.lcd.frames.some(f=>f.startsWith('101')))firstRamWrite={steps:cpu.steps,cycles:cpu.cycles,pc};
 for(const [name,prev,value] of [['state',oldState,cpu.r[0x3e]],['mode',oldMode,cpu.r[0x4b]],['pwm1Duty',oldDuty,cpu.s[3]]]){
  if(prev!==value&&events.length<1000)events.push({steps:cpu.steps,cycles:cpu.cycles,pc,name,from:prev,to:value});
 }
 oldState=cpu.r[0x3e];oldMode=cpu.r[0x4b];oldDuty=cpu.s[3];
}
console.log(JSON.stringify({schema:1,romSha256:hash(bytes),physicalCaptureSha256:hash(captureBytes),
 identity:'Unidentified NY8 ADC-bearing part; NY8B062D peripheral model is a hypothesis',
 comparison:{scope:'Complete startup command bits only; not timing or full charger behavior',reference,generated,matches},
 strict:{steps:strict.steps,pc:strict.pc,halted:strict.halted},
 experimental:{budget,steps:cpu.steps,cycles:cpu.cycles,halted:cpu.halted,timerMode:cpu.timerMode,t0md:cpu.t0md,interrupts:cpu.interrupts,overflows:cpu.timerOverflows,assumedOps:cpu.assumedOps,adc:cpu.adc,adcMode,adcConversions:cpu.adcPeripheral.conversions,firstRamWrite,events,eventLimit:1000,finalState:cpu.r[0x3e],lcdRam:[...cpu.lcd.ram]},
 limitations:['ADCAR/SBCAR encodings inferred',adcMode==='instant'?'Instant ADC':'ADC sample latched at START; no analog settling or 256us bias model','Reset X values seeded zero','No interrupt-entry latency','No external Timer0 clock','No battery physics','No hardware accessed']},null,2));
if(!matches||cpu.halted)process.exitCode=1;
