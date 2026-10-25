// NY8B062D §3.15. Explicit simulation assumptions; no inferred original config.
export class Watchdog {
 constructor(){this.config=null;this.credit=0;this.prescaler=0;this.timeouts=0;this.clears=0;this.resetRequested=false;}
 configure(config){
  if(!config||typeof config.enabled!=='boolean'||!['interrupt','reset'].includes(config.action)||![3500,15000,60000,250000].includes(config.baseUs)||!Number.isSafeInteger(config.instructionHz)||config.instructionHz<1||config.instructionHz>20000000)throw Error('Explicit WDT enabled/action/baseUs/instructionHz required');
  this.config={...config};this.credit=0;this.prescaler=0;this.timeouts=0;this.clears=0;this.resetRequested=false;
 }
 clear(cpu){this.credit=0;if(cpu.t0md&8)this.prescaler=0;this.clears++;}
 assignPrescaler(cpu){if(!(cpu.t0md&8))this.prescaler=0;}
 divisor(cpu){return cpu.t0md&8?2**((cpu.t0md&7)+(this.config?.action==='interrupt'?1:0)):1;}
 advance(cpu,cycles){
  if(!this.config?.enabled||!(cpu.r[8]&128)||this.resetRequested)return;
  // Integer rational time: cycles * 1e6 / instructionHz microseconds.
  this.credit+=cycles*1000000;const threshold=this.config.baseUs*this.config.instructionHz;
  while(this.credit>=threshold){
   this.credit-=threshold;if(++this.prescaler<this.divisor(cpu))continue;
   this.prescaler=0;this.timeouts++;cpu.r[3]&=~16;
   if(this.config.action==='interrupt')cpu.r[15]|=64;
   else {this.resetRequested=true;cpu.halted='WDT-timeout: reset begärd; resetförloppet är ännu inte modellerat';break;}
  }
 }
 snapshot(cpu){return {config:this.config?{...this.config}:null,credit:this.credit,prescaler:this.prescaler,divisor:this.divisor(cpu),timeouts:this.timeouts,clears:this.clears,resetRequested:this.resetRequested,scope:'Assumed clock/config; instruction-boundary timing; reset sequence and sleep unmodeled'};}
}
