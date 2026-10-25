// Deterministic, instruction-indexed external inputs. No RAM writes or hardware I/O.
export function validateScenario(actions,budget){
 if(!Array.isArray(actions))throw Error('Scenario must be an array');
 let previous=-1;
 return actions.map(action=>{
  if(!action||typeof action!=='object'||Array.isArray(action))throw Error('Invalid scenario action');
  if(Object.keys(action).some(k=>!['atStep','pressed','adc'].includes(k)))throw Error('Unknown scenario field');
  if(!Number.isSafeInteger(action.atStep)||action.atStep<0||action.atStep>=budget||action.atStep<previous)throw Error('Scenario steps must be ordered and within budget');
  previous=action.atStep;
  const out={atStep:action.atStep};
  if('pressed' in action){if(typeof action.pressed!=='boolean')throw Error('pressed must be boolean');out.pressed=action.pressed;}
  if('adc' in action){
   if(!action.adc||typeof action.adc!=='object'||Array.isArray(action.adc))throw Error('adc must map channels to raw samples');
   out.adc={};
   for(const [channel,value]of Object.entries(action.adc)){
    if(!/^[1-4]$/.test(channel)||!Number.isInteger(value)||value<0||value>4095)throw Error('Invalid ADC channel/sample');
    out.adc[channel]=value;
   }
  }
  return out;
 });
}
export function applyStimulus(cpu,action){
 if('pressed' in action)cpu.pressed=action.pressed;
 for(const [channel,value]of Object.entries(action.adc??{}))cpu.adc[Number(channel)]=value;
}
