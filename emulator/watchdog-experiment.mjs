import {Watchdog} from './watchdog.mjs';
// Validate before resetting; invalid form input must preserve the running experiment.
export function restartWatchdogExperiment(cpu,config){
 const watchdog=new Watchdog();if(config!==null)watchdog.configure(config);
 cpu.reset();cpu.watchdog=watchdog;
}
export function watchdogStatus(cpu){
 const w=cpu.watchdog.snapshot(cpu),c=w.config;
 if(!c)return 'Ej konfigurerad — originalets watchdoginställningar är okända.';
 return `TESTANTAGANDE · ${c.instructionHz.toLocaleString('sv-SE')} instruktioner/s · bas ${c.baseUs/1000} ms · ${c.action==='reset'?'reset':'avbrott'} · ${w.clears} nollställningar · ${w.timeouts} timeout${w.resetRequested?' · RESET BEGÄRD: simuleringen måste startas om':''}`;
}
