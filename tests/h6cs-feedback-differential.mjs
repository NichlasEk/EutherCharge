// Compare portable C++ filters against execution of the private original ROM.
import fs from 'node:fs';import assert from 'node:assert/strict';import{spawnSync}from'node:child_process';
import{NY8,parseROM}from'../emulator/core.mjs';
const path='dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin';
if(!fs.existsSync(path))throw Error('Private ROM required for differential verification');
fs.mkdirSync('build/h6cs-reference',{recursive:true});
const executable='build/h6cs-reference/feedback-test';
const build=spawnSync('c++',['-std=c++17','-Wall','-Wextra','-Werror','-O2','tests/h6cs_feedback_driver.cpp','-o',executable],{encoding:'utf8'});
assert.equal(build.status,0,build.stderr);
const b=fs.readFileSync(path),rom=parseROM(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));
const cpu=new NY8(rom),q=new NY8(rom),input=[],expected=[];
function routine(c,pc){c.pc=pc;c.stack=[0x7fd];let budget=1000;while(c.pc!==0x7fd&&budget--){assert.equal(c.step(),true,c.halted);}assert.equal(c.pc,0x7fd);}
function word(c,a,v){c.r[a]=v&255;c.r[a+1]=v>>8;}const read=(c,a)=>c.r[a]|c.r[a+1]<<8;
let seed=0x12345678;function random(){seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed&4095;}
for(let i=0;i<10000;i++){
 const values=i<1000?[4095,4095,4095]:[random(),random(),random()];input.push('F '+values.join(' '));
 word(cpu,0x2a,values[0]);word(cpu,0x2e,values[1]);word(cpu,0x36,Math.min(values[2]>>1,500));cpu.r[0x4d]&=~6;
 routine(cpu,0x3f4);routine(cpu,0x57a);
 expected.push(['F',cpu.r[0x4d]>>2&1,cpu.r[0x4d]>>1&1,read(cpu,0x2c),read(cpu,0x30),read(cpu,0x38),cpu.b1[5],cpu.b1[6],read(cpu,0x7a),read(cpu,0x7c),read(cpu,0x7e)].join(' '));
}
const sequence=[0,0,...Array(20).fill(35),...Array(4).fill(35),34,0,35,0,0,...Array(20).fill(1)];
for(let i=0;i<10000;i++)sequence.push([0,0,10,11,34,35,100,65535][random()>>9]);
for(const value of sequence){input.push('Q '+value);word(q,0x30,value);routine(q,0x35a);expected.push(['Q',read(q,0x30),q.r[0x4e]&1,q.r[0x4f]&1,q.b1[8],q.b1[9],q.b1[10]].join(' '));}
const run=spawnSync(executable,[],{input:input.join('\n')+'\n',encoding:'utf8',maxBuffer:8*1024*1024});assert.equal(run.status,0,run.stderr);
const actual=run.stdout.trim().split('\n');assert.equal(actual.length,expected.length);
for(let i=0;i<expected.length;i++)assert.equal(actual[i],expected[i],`sample ${i}: ${input[i]}`);
console.log(`PASS: ${expected.length} C++ filter/condition updates match original-ROM execution, including internal counters and accumulators`);
