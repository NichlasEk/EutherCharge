#!/usr/bin/env node
// Offline instruction/timing usage inventory. No private ROM words in output.
import fs from 'node:fs';import crypto from 'node:crypto';
import {NY8,parseROM,decode} from '../emulator/core.mjs';
import {validateScenario,applyStimulus} from '../emulator/scenario.mjs';
const [path,budgetText='4000000',scenarioPath]=process.argv.slice(2),budget=Number(budgetText);
if(!path||!Number.isSafeInteger(budget)||budget<1||budget>100000000)throw Error('Usage: ROM instruction-budget [scenario.json]');
const bytes=fs.readFileSync(path),cpu=new NY8(parseROM(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength)));
cpu.timerEnabled=true;cpu.timerMode='instruction';cpu.adcMode='clocked';cpu.gpio.mode='pad';
const actions=validateScenario(scenarioPath?JSON.parse(fs.readFileSync(scenarioPath,'utf8')):[],budget);let index=0,timerWriteCount=0;
const opcodes={},pclSites={},timerWrites=[],wdtConfigs=new Set();
const watchdog={clears:0,firstClearCycle:null,lastClearCycle:null,maxSteadyGapCycles:0,maxSteadyGapAtStep:null};
const write=cpu.write.bind(cpu);cpu.write=(address,value)=>{if(cpu.key(address)===2)pclSites[cpu.pc]=(pclSites[cpu.pc]??0)+1;return write(address,value);};
for(let i=0;i<budget;i++){
 while(index<actions.length&&actions[index].atStep===cpu.steps)applyStimulus(cpu,actions[index++]);
 const pc=cpu.pc,name=decode(cpu.rom[pc],pc).name,before=cpu.cycles,phase=cpu.timerPhase;
 if(!cpu.step())break;
 const entry=opcodes[name]??={instructions:0,cycles:0};entry.instructions++;entry.cycles+=cpu.cycles-before;
 if(name==='CLRWDT'){
  watchdog.clears++;if(watchdog.firstClearCycle===null)watchdog.firstClearCycle=cpu.cycles;
  if(watchdog.lastClearCycle!==null&&cpu.cycles-watchdog.lastClearCycle>watchdog.maxSteadyGapCycles){watchdog.maxSteadyGapCycles=cpu.cycles-watchdog.lastClearCycle;watchdog.maxSteadyGapAtStep=cpu.steps;}
  watchdog.lastClearCycle=cpu.cycles;
 }
 if(name==='T0MD')timerWriteCount++;
 if(name==='T0MD'&&timerWrites.length<256)timerWrites.push({pc,step:cpu.steps,t0md:cpu.t0md,phaseBefore:phase,phaseAfter:cpu.timerPhase,timerEnabled:cpu.timerEnabled&&!!(cpu.f[15]&1)});
 wdtConfigs.add(cpu.r[8]&128);
}
console.log(JSON.stringify({romSha256:crypto.createHash('sha256').update(bytes).digest('hex'),budget,steps:cpu.steps,cycles:cpu.cycles,halted:cpu.halted,actions,opcodes,pclSites,timerWriteCount,timerWrites,timerWriteLimit:256,wdtEnableValues:[...wdtConfigs],watchdog,limitations:['Cycle counts are model outputs, not physical timing','Configuration words and watchdog timebase remain unknown','No hardware accessed']},null,2));
if(cpu.halted||cpu.steps!==budget)process.exitCode=1;
