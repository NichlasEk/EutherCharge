// NY8B062D v1.8 §§3.1.6/7,3.3,3.5. RD_OPT is not known for the board.
// Digital resolution only: no voltage, current, RC or analog threshold model.
export class GPIO {
 constructor(){this.mode='legacy';this.external={a:Array(8).fill(null),b:Array(6).fill(null)};this.previous=null;}
 pin(cpu,port,bit){
  const mask=1<<bit,a=port==='a',latch=cpu.r[a?5:6],input=!!(cpu.f[a?5:6]&mask);
  const analog=a?bit<5&&!!(cpu.r[0x16]&mask):bit<3?!!(cpu.r[0x16]&(1<<(bit+5))):!!(cpu.r[0x13]&(1<<(bit+1)));
  let drive=input?null:Number(!!(latch&mask)),source=input?'input':'gpio';
  if(!a&&bit===3&&cpu.timer1.level(cpu)!==null){drive=cpu.timer1.level(cpu);source='pwm1';}
  const unsupported=!a&&((bit===3&&!!(cpu.s[15]&64))||(bit===3&&source!=='pwm1'&&!!(cpu.s[5]&128))||(bit===2&&!!(cpu.s[10]&128))||(bit===1&&!!(cpu.s[6]&128)));
  const openDrain=a?bit===5:!!(cpu.f[12]&mask);
  if(openDrain&&drive===1)drive=null;
  // The known MODE stimulus models a switch to ground and an external pull-up.
  const external=a&&bit===5&&cpu.pressed?0:this.external[port][bit];
  const up=a?(bit===5?!(cpu.r[8]&16):!(cpu.f[9]&mask)):!(cpu.r[12]&mask);
  const down=a?(bit===5?!(cpu.f[9]&32):bit<4&&!(cpu.r[11]&mask)):bit<4&&!(cpu.r[11]&(mask<<4));
  const strong=[drive,external].filter(x=>x!==null);
  let level=null,reason='floating';
  if(unsupported)reason='unsupported-mux';
  else if(analog)reason='analog-digital-disabled';
  else if(strong.length&&strong.some(x=>x!==strong[0]))reason='contention';
  else if(strong.length){level=strong[0];reason=source;}
  else if((up||(a&&bit===5))&&down)reason='opposed-pulls';
  else if(up||(a&&bit===5)){level=1;reason='pull-up';}
  else if(down){level=0;reason='pull-down';}
  return {level,reason,input,source,latch:Number(!!(latch&mask))};
 }
 port(cpu,port){
  const width=port==='a'?8:6;let value=port==='a'?0:cpu.r[6]&192,unknown=0;const pins=[];
  for(let bit=0;bit<width;bit++){const pin=this.pin(cpu,port,bit);pins.push(pin);if(pin.level===null)unknown|=1<<bit;else value|=pin.level<<bit;}
  return {value,unknown,pins};
 }
 read(cpu,port){
  const resolved=this.port(cpu,port);let value=resolved.value;
  if(this.mode==='latch')for(let bit=0;bit<resolved.pins.length;bit++)if(!resolved.pins[bit].input)value=(value&~(1<<bit))|(resolved.pins[bit].latch<<bit);
  // Unresolved input reads seed zero; the uncertainty mask stays in diagnostics.
  return value;
 }
 syncLCD(cpu){
  if(this.mode==='legacy')return;
  const a=this.port(cpu,'a'),b=this.port(cpu,'b');
  const valid=!(a.unknown&1)&&!(b.unknown&48);
  if(valid&&this.previous)cpu.lcd.edge(a.value,b.value,this.previous.a,this.previous.b);
  else if(!valid)cpu.lcd.bits=null; // Never manufacture serial bits from floating pins.
  this.previous=valid?{a:a.value,b:b.value}:null;
 }
 snapshot(cpu){return {mode:this.mode,external:{a:[...this.external.a],b:[...this.external.b]},unresolvedReadConvention:'zero; not an electrical prediction',a:this.port(cpu,'a'),b:this.port(cpu,'b')};}
}
