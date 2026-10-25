import {GPIO} from './gpio.mjs';
import {Timer1} from './timer1.mjs';
import {ClockedADC} from './adc.mjs';
import {RULES} from './opcodes.mjs';
export const hex=(v,n=2)=>v.toString(16).toUpperCase().padStart(n,'0');
export function decode(w,pc=0){
 for(const [mask,value,name,ops] of RULES) if((w&mask)===value){
  let target=null;
  if(ops.includes('addr11'))target=w&2047;
  else if(ops.includes('addr9'))return {name,target:null,text:name+' PCHBUF[2:1]:0x'+hex(w&511,3)};
  else if(ops.includes('addr8'))return {name,target:null,text:name+' PCHBUF[2:0]:0x'+hex(w&255)};
  let arg=target!==null?'0x'+hex(target,3):ops.includes('imm8')?'0x'+hex(w&255):ops.includes('RReg')?'R'+hex(w&127)+(ops.includes('DestAR')?(w&128?',R':',A'):'')+(ops.includes('bs')?','+((w>>7)&7):''):ops.includes('FReg')?'F'+hex(w&15):ops.includes('SReg')?'S'+hex(w&31):'';
  return {name,target,text:name+' '+arg};
 }
 return {name:'UNKNOWN',text:'.word '+hex(w,4)};
}
export function parseROM(buffer){
 if(buffer.byteLength!==4096)throw Error('Förväntar 4096 byte: 2048 little-endian 14-bitarsord.');
 const v=new DataView(buffer),w=new Uint16Array(2048);
 for(let i=0;i<2048;i++){w[i]=v.getUint16(i*2,true);if(w[i]>0x3fff)throw Error('Fel ordformat vid '+hex(i,3));}
 return w;
}
export class LCD {
 constructor(){this.ram=new Uint8Array(32);this.commands=[];this.frames=[];this.bits=null;this.enabled=false;}
 edge(pa,pb,oldpa,oldpb){
  if((oldpa&1)&&!(pa&1))this.bits='';
  if(this.bits!==null&&!(pa&1)&&!(oldpb&32)&&(pb&32))this.bits+=String((pb>>4)&1);
  if(!(oldpa&1)&&(pa&1)&&this.bits!==null){this.consume(this.bits);this.bits=null;}
 }
 consume(bits){
  this.frames.push(bits);if(this.frames.length>80)this.frames.shift();
  if(bits.startsWith('100')&&(bits.length-3)%9===0){for(let i=3;i+9<=bits.length;i+=9){let cmd=parseInt(bits.slice(i,i+8),2);this.commands.push(cmd);if(this.commands.length>64)this.commands.shift();if(cmd===3)this.enabled=true;if(cmd===2)this.enabled=false;}}
  else if(bits.startsWith('101')&&bits.length>=13){let addr=parseInt(bits.slice(3,9),2);for(let i=9;i+4<=bits.length;i+=4){if(addr<32)this.ram[addr]=parseInt(bits.slice(i,i+4).split('').reverse().join(''),2);addr++;}}
 }
}
export class NY8 {
 constructor(rom){this.rom=rom;this.reset();}
 reset(){this.r=new Uint8Array(128);this.b1=new Uint8Array(32);this.f=new Uint8Array(16);this.s=new Uint8Array(32);this.s[2]=0x3f;this.timer1=new Timer1();this.gpio=new GPIO();// NY8B062D candidate reset values; unspecified X bits and RAM are seeded zero.
 this.f[5]=255;this.f[6]=63;this.f[9]=255;this.f[15]=0x1d;
 this.r[3]=24;this.r[8]=0x98;this.r[9]=63;this.r[11]=255;this.r[12]=63;this.r[16]=32;this.r[19]=3;this.r[20]=10;this.adcMode="instant";this.adcPeripheral=new ClockedADC();this.a=0;this.pc=0;this.stack=[];this.steps=0;this.gie=false;this.t0md=0x3f;this.cycles=0;this.timerMode="synthetic";this.timerOverflows=0;this.interrupts=0;this.timerPhase=0;this.timerDivider=32;this.timerEnabled=false;this.adc=[0,1500,2500,500,300];this.pressed=false;this.halted='';this.lcd=new LCD();this.trace=[];this.breakpoint=null;this.carryOps=0;}
 key(i){i&=127;if(i===0){i=this.r[4]&127;if(!i)return null;}return i;}
 read(i){i=this.key(i);if(i===null)return 0;if(i>=32&&i<64&&(this.r[3]&64))return this.b1[i-32];if(i===2)return this.pc&255;if(i===0x19)return (this.r[i]&207)|((this.timer1.count>>8&3)<<4);if((i===5||i===6)&&this.gpio.mode!=='legacy')return this.gpio.read(this,i===5?'a':'b');if(i===6){const level=this.timer1.level(this);return level===null?this.r[6]:(this.r[6]&247)|(level<<3);}if(i===5)return (this.r[5]&~32)|(this.pressed?0:32);return this.r[i];}
 write(i,v){i=this.key(i);if(i===null)return;v&=255;if(i>=32&&i<64&&(this.r[3]&64)){this.b1[i-32]=v;return;}
  const pa=this.r[5],pb=this.r[6];
  if(i===2)this.next=((this.r[10]&7)<<8)|v;
  if(this.adcMode==='clocked'&&i===18)return; // ADD is read-only.
  if(this.adcMode==='clocked'&&i===17){this.r[17]=(v&240)|(this.r[17]&15);return;}
  if(i===16&&this.adcMode==='clocked'){this.adcPeripheral.write(this,v);return;}
  if(i===16){const channel=v&15;this.r[i]=(v&~64)|32;if(v&64){const sample=this.adc[channel]??0;this.r[18]=sample>>4;this.r[17]=(this.r[17]&240)|(sample&15);}return;}
  this.r[i]=v;if((i===5||i===6)&&this.gpio.mode==='legacy')this.lcd.edge(this.r[5],this.r[6],pa,pb);
 }
 flag(bit,v){this.r[3]=(this.r[3]&~(1<<bit))|(v?1<<bit:0);}
 z(v){this.flag(2,(v&255)===0);}
 push(v){if(this.stack.length>=8)throw Error('Stack overflow (8 nivåer)');this.stack.push(v);}
 pop(){if(!this.stack.length)throw Error('Stack underflow');return this.stack.pop();}
 step(){
  if(this.halted)return false;
  const pc=this.pc,w=this.rom[pc],d=decode(w,pc),n=d.name,rr=w&127,bit=(w>>7)&7;
  this.next=(pc+1)&2047;let cachedOperand;
  const operand=()=>{if(cachedOperand===undefined){cachedOperand=this.read(rr);this.gpio.observeRead(this,this.key(rr),n,bit,this.a);}return cachedOperand;};
  const carry=this.r[3]&1;
  const dest=v=>{if(w&128)this.write(rr,v);else this.a=v&255;};
  const add=(x,y,c=0)=>{const v=x+y+c;this.flag(0,v>255);this.flag(1,(x&15)+(y&15)+c>15);this.z(v);return v&255;};
  const sub=(x,y,borrow=0)=>{const v=x-y-borrow;this.flag(0,v>=0);this.flag(1,(x&15)>=(y&15)+borrow);this.z(v);return v&255;};
  try{
   switch(n){
    case 'NOP':break;
    case 'CLRWDT':this.r[3]|=24;break; // WDT timebase is not yet modeled.
    case 'MOVIA':this.a=w&255;break;
    case 'MOVAR':this.write(rr,this.a);break;
    case 'MOVR':this.z(operand());dest(operand());break;
    case 'CLRA':this.a=0;this.z(0);break;
    case 'CLRR':this.write(rr,0);this.z(0);break;
    case 'BSR':this.write(rr,operand()|(1<<bit));break;
    case 'BCR':this.write(rr,operand()&~(1<<bit));break;
    case 'BTRSS':if(operand()&(1<<bit))this.next++;break;
    case 'BTRSC':if(!(operand()&(1<<bit)))this.next++;break;
    case 'INCR':this.z(operand()+1);dest(operand()+1);break;
    case 'DECR':this.z(operand()-1);dest(operand()-1);break;
    case 'INCRSZ':dest(operand()+1);if(((operand()+1)&255)===0)this.next++;break;
    case 'DECRSZ':dest(operand()-1);if(((operand()-1)&255)===0)this.next++;break;
    case 'ADDAR':dest(add(operand(),this.a));break;
    case 'SUBAR':dest(sub(operand(),this.a));break;
    case 'ADCAR':this.carryOps++;dest(add(operand(),this.a,carry));break;
    case 'SBCAR':this.carryOps++;dest(sub(operand(),this.a,1-carry));break;
    case 'ADDIA':this.a=add(w&255,this.a);break;
    case 'SUBIA':this.a=sub(w&255,this.a);break;
    case 'ADCIA':this.a=add(w&255,this.a,carry);break;
    case 'SBCIA':this.a=sub(w&255,this.a,1-carry);break;
    case 'CMPAR':this.flag(0,operand()>=this.a);this.z(operand()-this.a);break;
    case 'ANDAR':{let v=operand()&this.a;dest(v);this.z(v);break;}
    case 'IORAR':{let v=operand()|this.a;dest(v);this.z(v);break;}
    case 'XORAR':{let v=operand()^this.a;dest(v);this.z(v);break;}
    case 'ANDIA':this.a&=w&255;this.z(this.a);break;
    case 'IORIA':this.a|=w&255;this.z(this.a);break;
    case 'XORIA':this.a^=w&255;this.z(this.a);break;
    case 'COMR':dest(operand()^255);this.z(operand()^255);break;
    case 'SWAPR':dest(((operand()<<4)|(operand()>>4))&255);break;
    case 'RLR':this.flag(0,operand()&128);dest((operand()<<1)|carry);break;
    case 'RRR':this.flag(0,operand()&1);dest((operand()>>1)|(carry<<7));break;
    case 'LCALL':this.push(this.next);this.next=d.target;break;
    case 'CALL':this.push(this.next);this.next=((this.r[10]&7)<<8)|(w&255);break;
    case 'LGOTO':this.next=d.target;break;
    case 'GOTO':this.next=((this.r[10]&6)<<8)|(w&511);break;
    case 'CALLA':this.push(this.next);this.next=((this.s[7]&7)<<8)|this.a;break;
    case 'GOTOA':this.next=((this.s[7]&7)<<8)|this.a;break;
    case 'RETIA':this.a=w&255;this.next=this.pop();break;
    case 'RETIE':this.gie=true;this.next=this.pop();break;
    case 'RET':this.next=this.pop();break;
    case 'INT':this.push(this.next);this.next=1;break;
    case 'ENI':this.gie=true;break;
    case 'DISI':this.gie=false;break;
    case 'IOST':this.f[w&15]=this.a;break;
    case 'IOSTR':this.a=(w&15)===15?(this.f[15]&127)|(this.gie?128:0):this.f[w&15];break;
    case 'SFUN':this.timer1.write(this,w&31,this.a);break;
    case 'SFUNR':this.a=(w&31)===0?this.timer1.count&255:this.s[w&31];break;
    case 'T0MD':this.t0md=this.a;if(!(this.a&8))this.timerPhase=0;break;
    case 'T0MDR':this.a=this.t0md;break;
    case 'TABLEA':{let data=this.rom[((this.s[7]&7)<<8)|this.a];this.a=data&255;this.s[8]=(data>>8)&63;break;}
    case 'SLEEP':throw Error('SLEEP: wake-upmodell saknas');
    default:throw Error('Ej verifierad instruktion '+hex(w,4)+' vid '+hex(pc,3));
   }
   const branch=['LCALL','CALL','LGOTO','GOTO','CALLA','GOTOA','RETIA','RETIE','RET','TABLEA'].includes(n);
   const skipped=['BTRSS','BTRSC','INCRSZ','DECRSZ'].includes(n)&&this.next===pc+2;
   const elapsed=n==='INT'?3:branch||skipped?2:1;
   this.pc=this.next&2047;this.steps++;this.cycles+=elapsed;
   this.advanceTimer(elapsed);this.timer1.advance(this,elapsed);
   if(this.adcMode==='clocked')this.adcPeripheral.advance(this,elapsed);
   if(this.gie&&((this.r[14]&this.r[15]&9)||(this.adcMode==='clocked'&&(this.r[17]&192)===192))){this.gie=false;this.push(this.pc);this.pc=8;this.interrupts++;}
   this.gpio.syncLCD(this);this.trace.push({pc,w,text:d.text});if(this.trace.length>100)this.trace.shift();
   return true;
  }catch(e){this.halted=e.message;return false;}
 }
 // Instruction-clock Timer0 follows NY8B062D v1.8 sections 3.2 and 3.6.
 // External/low oscillator clocks and interrupt-entry latency remain unmodeled.
 advanceTimer(cycles){
  if(!this.timerEnabled||!(this.f[15]&1))return;
  const documented=this.timerMode==='instruction';
  if(documented&&(this.t0md&32))return;
  const divisor=documented?(this.t0md&8?1:2**((this.t0md&7)+1)):this.timerDivider;
  this.timerPhase+=documented?cycles:1;
  while(this.timerPhase>=divisor){
   this.timerPhase-=divisor;this.r[1]=(this.r[1]+1)&255;
   if(!this.r[1]){this.r[15]|=1;this.timerOverflows++;}
  }
 }
 run(count){let done=0;for(;done<count;done++){if(this.breakpoint!==null&&this.pc===this.breakpoint){this.halted='Brytpunkt '+hex(this.pc,3);break;}if(!this.step())break;}return done;}
 snapshot(){return {pc:this.pc,a:this.a,steps:this.steps,cycles:this.cycles,timerMode:this.timerMode,timerOverflows:this.timerOverflows,interrupts:this.interrupts,r:[...this.r],bank1:[...this.b1],f:[...this.f],s:[...this.s],stack:[...this.stack],adc:[...this.adc],adcMode:this.adcMode,adcConversions:this.adcPeripheral.conversions,lcd:{ram:[...this.lcd.ram],commands:[...this.lcd.commands]},carryOps:this.carryOps,timer1:this.timer1.snapshot(this),gpio:this.gpio.snapshot(this),timerEnabled:this.timerEnabled,timerDivider:this.timerDivider,halted:this.halted};}
}
export const PROFILES={ny8:{label:'Nyquest NY8 · originalkod',voltage:'5 V',execution:true},avr:{label:'AVR · portningsmodell',voltage:'5 V (modell)',execution:false},stm32:{label:'STM32 · portningsmodell',voltage:'3,3 V (nivåanpassning krävs)',execution:false}};
export class Plant {
 constructor(){this.voltage=12.2;this.temperature=22;this.target=14.4;this.currentLimit=3;this.connected=true;this.fault=false;this.fan=false;this.current=0;this.state='VILA';this.soc=50;}
 tick(dt){if(!this.connected){this.current=0;this.state='FRÅNKOPPLAD';}else if(this.fault||this.temperature>=50){this.current=0;this.state='STOPP';}else{this.current=Math.min(this.currentLimit,Math.max(0,(this.target-this.voltage)*2));this.state=this.current<0.15?'UNDERHÅLL':this.current>=this.currentLimit-.01?'KONSTANT STRÖM':'KONSTANT SPÄNNING';this.soc=Math.min(100,this.soc+this.current*dt/36);}
 this.fan=this.current>1||this.temperature>35;}
}
