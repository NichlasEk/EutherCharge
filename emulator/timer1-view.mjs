export function paintTimer1(root,cpu){
 const s=cpu.timer1.snapshot(cpu);
 const divisor=s.prescaler,period=s.frameTicks*divisor;
 root.querySelector('[data-pwm-summary]').textContent=`Aktiv pulsbredd ${s.activeDuty} / ${s.frameTicks} timertick · väntande ${s.pendingDuty} · räknare ${s.count}`;
 root.querySelector('[data-pwm-clock]').textContent=s.externalClock?'Extern klocka: inga flanker injiceras.':`Period ${period} instruktionscykler · ${s.underflows} underflöden · ${s.activeLow?'aktiv låg':'aktiv hög'} · ${s.enabled&&!s.stopped?'räknar':'stoppad'}`;
 const end=cpu.cycles,window=Math.min(8192,Math.max(256,period*2));
 const start=Math.max(0,end-window,s.edges[0]?.cycle??end);
 let level=null;for(const e of s.edges){if(e.cycle<=start)level=e.level;else break;}
 const x=cycle=>10+(cycle-start)/Math.max(1,end-start)*580,y=level=>level?18:66;
 let path=level===null?'':`M10 ${y(level)}`;
 for(const e of s.edges){
  if(e.cycle<=start||e.cycle>end)continue;
  if(level!==null)path+=` H${x(e.cycle)}`;
  if(e.level!==null)path+=level===null?` M${x(e.cycle)} ${y(e.level)}`:` V${y(e.level)}`;
  level=e.level;
 }
 if(level!==null)path+=' H590';
 root.querySelector('[data-pwm-path]').setAttribute('d',path);
 root.querySelector('[data-pwm-window]').textContent=`Visar cykel ${start}–${end}. ${s.outputEnabled?'PWM väljer PB3.':'PWM-utgång av; PB3 är GPIO i denna modell.'} Modellerad logik, ingen uppmätt fysisk vågform.`;
}
