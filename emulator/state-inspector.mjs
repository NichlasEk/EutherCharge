// Read-only explanation of tested firmware routines, not a second controller.
const rules={
  2:'R4D.bit0 och R4E.bit0 måste båda vara satta: läge 0–2 går till 4, läge 3 går till 3.',
  4:'Två färdiga ADC4-mätfönster (R4D.bit1) leder till 5. Händelseflaggan förbrukas vid varje anrop.',
  5:'Återkoppling under referensen i 5 mätfönster leder till 6 om räknare R27:R26 ≥ 60, annars 7. Värde < 20 leder direkt till 7 vid nytt mätfönster. Timeout kan välja 8 men skrivas över till 7 i samma anrop.',
  7:'Återkoppling över referensen i 5 mätfönster leder till 4. Räknare R25:R24 ≥ 7200 väljer 9; återstående kod körs ändå.',
  9:'Läge 2 och ADC3-baserat R31:R30 < 1301 leder till 1. Annars stannar denna rutin i 9.'
};
export function inspectState(cpu){
 const word=address=>cpu.r[address]|cpu.r[address+1]<<8;
 return {
  state:cpu.r[0x3e],
  rule:rules[cpu.r[0x3e]]??'Villkoren för detta tillstånd är ännu inte fullständigt verifierade.',
  signals:[
   ['ADC2 efter filter · R2D:R2C',word(0x2c)],
   ['ADC3 efter bearbetning · R31:R30',word(0x30)],
   ['ADC4 efter filter · R39:R38',word(0x38)],
   ['Referens · R35:R34',word(0x34)],
   ['Händelseräknare · R3F',cpu.r[0x3f]],
   ['Räknare · R25:R24',word(0x24)],
   ['Räknare · R27:R26',word(0x26)],
   ['Villkorsflagga · R4D.bit0',cpu.r[0x4d]&1],
   ['Nytt ADC4-fönster · R4D.bit1',(cpu.r[0x4d]>>1)&1],
   ['Villkorsflagga · R4E.bit0',cpu.r[0x4e]&1],
   ['ADC2-relaterad flagga · R4F.bit1',(cpu.r[0x4f]>>1)&1]
  ]
 };
}
export function paintState(root,cpu){
 const info=inspectState(cpu),doc=root.ownerDocument;
 root.querySelector('[data-state-rule]').textContent=info.rule;
 const chips=root.querySelector('[data-state-chips]');
 chips.replaceChildren(...Array.from({length:10},(_,state)=>{
  const chip=doc.createElement('span');chip.textContent=String(state);chip.className='state-chip'+(state===info.state?' active':'');
  if(state===info.state)chip.setAttribute('aria-current','true');return chip;
 }));
 const values=root.querySelector('[data-state-values]');values.replaceChildren();
 for(const [label,value]of info.signals){const term=doc.createElement('dt'),description=doc.createElement('dd');term.textContent=label;description.textContent=String(value);values.append(term,description);}
 root.querySelector('[data-cycle-count]').textContent=cpu.cycles.toLocaleString('sv-SE')+' modellerade instruktionscykler · '+cpu.interrupts+' avbrott';
}
