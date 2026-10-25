// NY8B062D v1.8, sections 3.1.15–19 and 3.14.3.
// Injected raw samples, not an electrical ADC/NTC model.
export function adcDuration(adr, adcr) {
 const bits=[8,10,12,12][adcr&3];
 const sampling=2**((adcr>>2)&3);
 const divider=[16,8,1,2][(adr>>4)&3];
 return (sampling+bits+2)*divider;
}
export class ClockedADC {
 constructor(){this.pending=null;this.conversions=0;}
 write(cpu,value){
  const oldEoc=cpu.r[16]&32;
  cpu.r[16]=(value&~96)|oldEoc;
  if(!(value&128)){
   this.pending=null;cpu.r[16]|=32;return;
  }
  if(!(value&64))return;
  if(!(value&16))throw Error('ADC: START med GCHS=0 saknar elektrisk modell');
  if((cpu.r[20]&3)<2)throw Error('ADC: endast 12-bitars resultatformat är modellerat');
  const channel=value&15,sample=cpu.adc[channel];
  if(!Number.isInteger(sample)||sample<0||sample>4095)throw Error('ADC: kanal '+channel+' saknar giltigt råvärde');
  if(this.pending)throw Error('ADC: ny START under pågående konvertering saknar verifierad semantik');
  cpu.r[16]&=~32;
  this.pending={remaining:adcDuration(cpu.r[17],cpu.r[20]),sample};
 }
 advance(cpu,cycles){
  if(!this.pending)return;
  this.pending.remaining-=cycles;
  if(this.pending.remaining>0)return;
  const sample=this.pending.sample;
  cpu.r[18]=sample>>4;cpu.r[17]=(cpu.r[17]&240)|(sample&15)|128;
  cpu.r[16]|=32;this.pending=null;this.conversions++;
 }
}
