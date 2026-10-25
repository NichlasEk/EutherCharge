// NY8B062D v1.8 sections3.4.1–4 and3.7, figures17/18.
// Instruction-clock model. No electrical pad or oscillator-frequency claim.
export class Timer1 {
 constructor(){this.count=0;this.reload=0;this.frameTop=0;this.duty=0;this.pendingDuty=0;this.phase=0;this.done=false;this.underflows=0;this.edges=[];this.lastLevel=null;}
 write(cpu,index,value){
  const old=cpu.s[index];cpu.s[index]=value;
  if(index===0){
   this.reload=((cpu.r[0x19]>>4&3)<<8)|value;
   if(!(cpu.s[1]&1)){this.count=this.reload;this.frameTop=this.reload;this.done=false;}
  }
  if(index===1&&!(old&1)&&(value&1))this.done=false;
  if(index===2)this.phase=0; // Phase after reconfiguration is a model convention.
  if(index===3)this.pendingDuty=((cpu.r[0x19]&3)<<8)|value;
  this.observe(cpu,cpu.cycles);
 }
 level(cpu){
  if(!(cpu.s[1]&128))return null;
  // Figure18 comparator plus XOR polarity; duty0 is never active.
  return Number(this.count<this.duty)^Number(!!(cpu.s[1]&64));
 }
 observe(cpu,cycle){
  const level=this.level(cpu);
  if(level===this.lastLevel)return;
  this.edges.push({cycle,level});if(this.edges.length>256)this.edges.shift();this.lastLevel=level;
 }
 advance(cpu,cycles){
  if(!(cpu.s[1]&1)||this.done||(cpu.s[2]&32))return;
  const divisor=cpu.s[2]&8?1:2**((cpu.s[2]&7)+1);
  for(let n=1;n<=cycles;n++){
   if(++this.phase<divisor)continue;
   this.phase=0;
   if(this.count===0){
    this.underflows++;cpu.r[15]|=8;this.duty=this.pendingDuty;
    if(cpu.s[1]&4){this.count=1023;this.frameTop=1023;this.done=true;}
    else {this.count=cpu.s[1]&2?this.reload:1023;this.frameTop=this.count;}
   }else this.count--;
   this.observe(cpu,cpu.cycles-cycles+n);
   if(this.done)break;
  }
 }
 snapshot(cpu){return {count:this.count,reload:this.reload,activeDuty:this.duty,pendingDuty:this.pendingDuty,frameTicks:this.frameTop+1,prescaler:cpu.s[2]&8?1:2**((cpu.s[2]&7)+1),externalClock:!!(cpu.s[2]&32),enabled:!!(cpu.s[1]&1),outputEnabled:!!(cpu.s[1]&128),activeLow:!!(cpu.s[1]&64),stopped:this.done,level:this.level(cpu),underflows:this.underflows,edges:[...this.edges]};}
}
