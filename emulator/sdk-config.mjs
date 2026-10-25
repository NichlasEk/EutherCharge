// First nine 16-bit words of a KNOWN SDK config block, not a program ROM.
// Raw field values only: no identity, checksum, polarity or physical-address claim.
export function readSdkConfigWindow(bytes){
 if(!(bytes instanceof Uint8Array)||bytes.length!==18)throw Error('Expected exactly18bytes from an independently identified SDK config block');
 return {wdtReg:bytes[1]&1,wdtEventReg:(bytes[1]>>1)&1,wdtTimeBaseReg:(bytes[12]>>4)&3,rdPortTypeReg:(bytes[17]>>2)&1,instClockReg:(bytes[0]>>6)&1,instructionClockReg:(bytes[0]>>7)&1};
}
