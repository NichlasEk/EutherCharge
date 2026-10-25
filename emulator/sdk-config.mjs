// First nine 16-bit words of a KNOWN SDK config block, not a program ROM.
// Raw field values only: no identity, checksum, polarity or physical-address claim.
export function readSdkConfigWindow(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==18)throw Error('Expected exactly18bytes from an independently identified SDK config block');
 return {wdtReg:bytes[1]&1,wdtEventReg:(bytes[1]>>1)&1,wdtTimeBaseReg:(bytes[12]>>4)&3,rdPortTypeReg:(bytes[17]>>2)&1,instClockReg:(bytes[0]>>6)&1,instructionClockReg:(bytes[0]>>7)&1};
}

// Explicit SDK representation/version; never auto-detect from an MCU ROM.
export function decodeNy8B062dSdkConfig(bytes,configVersion){
 if(configVersion!==3)throw Error('Only SDK config version3 has been independently exercised');
 if(!(bytes instanceof Uint8Array)||bytes.length!==32)throw Error('Expected a separately identified32-byte NY8B062D SDK config block');
 const raw=readSdkConfigWindow(bytes.subarray(0,18));
 return {deviceProfile:'NY8B062D',configVersion,watchdogEnabled:!!raw.wdtReg,
  watchdogEvent:raw.wdtEventReg?'reset':'interrupt',watchdogBaseUs:[250000,60000,3500,15000][raw.wdtTimeBaseReg],
  gpioReadSource:raw.rdPortTypeReg?'pad':'latch',raw};
}
