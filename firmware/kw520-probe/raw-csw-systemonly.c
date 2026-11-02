/* System-only AP CSW write/readback test. No target-memory access, debug
 * power, reset, flash or core register writes. Default dry run. Adapted from
 * the locally tested raw SWD harness; capture layout checked against OpenOCD.
 */
#include <libjaylink/libjaylink.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <assert.h>
static uint8_t direction[32], output[32], input[32];
static unsigned n;
/* Fixed-length batches are qualified for OK replies only. After any error,
 * do not issue cleanup AP writes on a possibly faulted/desynchronized link. */
static int link_healthy = 1;
static void bit(int drive, int value) {
 assert(n<256); direction[n/8]|=(drive&1)<<(n%8);
 output[n/8]|=(value&1)<<(n%8); n++;
}
static uint32_t get(unsigned start,unsigned count) {
 uint32_t v=0; for(unsigned i=0;i<count;i++)v|=((input[(start+i)/8]>>((start+i)%8))&1u)<<i;return v;
}
static int transfer(struct jaylink_device_handle *h, unsigned ap, unsigned read, unsigned addr, uint32_t value, uint32_t *answer) {
 if(!link_healthy){puts("TRANSFER_SKIPPED=link-unqualified");return JAYLINK_ERR;}
 unsigned fields=ap | (read<<1) | ((addr&12));
 unsigned cmd=0x81 | (ap<<1) | (read<<2) | ((addr&12)<<1) | (__builtin_parity(fields)<<5);
 n=0;memset(direction,0,sizeof direction);memset(output,0,sizeof output);memset(input,0,sizeof input);
 for(unsigned i=0;i<8;i++)bit(1,(cmd>>i)&1);
 if(read){for(unsigned i=0;i<38;i++)bit(0,0);}
 else {for(unsigned i=0;i<5;i++)bit(0,0);for(unsigned i=0;i<32;i++)bit(1,(value>>i)&1);bit(1,__builtin_parity(value));}
 for(unsigned i=0;i<64;i++)bit(1,0);
 int rc=jaylink_swd_io(h,direction,output,input,n);
 if(rc!=JAYLINK_OK){link_healthy=0;return rc;}
 unsigned ack=get(8,3);printf("%s %s addr=%x cmd=%02x ACK=%u",ap?"AP":"DP",read?"read":"write",addr,cmd,ack);
 if(read && ack==1){uint32_t data=get(11,32);unsigned p=get(43,1);printf(" data=%08x parity=%u",data,p);if(p!=(unsigned)__builtin_parity(data)){puts(" BAD PARITY");link_healthy=0;return JAYLINK_ERR;} *answer=data;}
 if(!read)printf(" value=%08x",value);
 puts("");
 if(ack!=1){
   printf("TRANSFER_ERROR=%s NO_MORE_TRANSFERS=1\n",ack==2?"WAIT":ack==4?"FAULT":"INVALID_ACK");
   link_healthy=0;return JAYLINK_ERR;
 }
 return JAYLINK_OK;
}

static int restore_csw(struct jaylink_device_handle *h, uint32_t original) {
 if(!link_healthy){puts("CSW_RESTORE_SKIPPED=link-unqualified COLD_START_REQUIRED=1");return JAYLINK_ERR;}
 uint32_t back=0;
 int rc=transfer(h,1,0,0,original,&back);
 if(rc==JAYLINK_OK)rc=transfer(h,1,1,0,0,&back);
 if(rc==JAYLINK_OK)rc=transfer(h,0,1,12,0,&back);
 if(rc!=JAYLINK_OK){puts("CSW_RESTORE_READBACK=unavailable RESTORE_MATCH=0");return rc;}
 printf("CSW_RESTORE_READBACK=%08x RESTORE_MATCH=%d\n",back,back==original);
 return back==original?JAYLINK_OK:JAYLINK_ERR;
}

#define CHECK(call) do { int rc=(call); if(rc!=JAYLINK_OK){fprintf(stderr,"%s: %s\n",#call,jaylink_strerror(rc)); result=1;goto cleanup;} }while(0)
int main(int argc,char **argv){
 int execute=argc==2&&!strcmp(argv[1],"--execute");
 if(argc>1&&!execute){fprintf(stderr,"Usage: %s [--execute]\n",argv[0]);return 2;}
 for(unsigned i=0;i<56;i++)bit(1,1);
 for(unsigned i=0;i<16;i++)bit(1,(0xe79e>>i)&1);
 for(unsigned i=0;i<56;i++)bit(1,1);
 for(unsigned i=0;i<8;i++)bit(1,0);
 unsigned request=n;
 for(unsigned i=0;i<8;i++)bit(1,(0xa5>>i)&1); /* DP read address 0 */
 for(unsigned i=0;i<38;i++)bit(0,0); /* turnaround, ack, data, parity, turnaround */
 for(unsigned i=0;i<8;i++)bit(1,0);
 assert(request==136 && n==190);
 assert(output[17]==0xa5 && direction[17]==255);
 printf("Plan: 56 ones, E79E LSB-first, 56 ones, 8 idle, A5 DPIDR read, 38 input, 8 idle; %u clocks\n",n);
 printf("direction=");for(unsigned i=0;i<(n+7)/8;i++)printf("%02x",direction[i]);puts("");
 printf("output=");for(unsigned i=0;i<(n+7)/8;i++)printf("%02x",output[i]);puts("");
 if(!execute){puts("DRY RUN: require system-only power; AP0 CSW read; change SIZE to 32-bit only; readback twice; restore CSW and verify. No TAR/DRW or target-memory access.");return 0;}
 int result=0, restore_needed=0; uint32_t original_csw=0; struct jaylink_context *ctx=NULL; struct jaylink_device **devs=NULL;
 struct jaylink_device_handle *handle=NULL; size_t count=0;
 CHECK(jaylink_init(&ctx)); CHECK(jaylink_discovery_scan(ctx,JAYLINK_HIF_USB));
 CHECK(jaylink_get_devices(ctx,&devs,&count));
 for(size_t i=0;i<count;i++){uint32_t serial=0;
 if(jaylink_device_get_serial_number(devs[i],&serial)==JAYLINK_OK && serial==69401338){CHECK(jaylink_open(devs[i],&handle));break;}}
 if(!handle){fprintf(stderr,"Expected probe not found\n");result=1;goto cleanup;}
 struct jaylink_hardware_status status;
 CHECK(jaylink_get_hardware_status(handle,&status)); printf("VTref=%u mV\n",status.target_voltage);
 if(status.target_voltage<3000||status.target_voltage>3500){fprintf(stderr,"Unexpected VTref; stop\n");result=1;goto cleanup;}
 CHECK(jaylink_select_interface(handle,JAYLINK_TIF_SWD,NULL));
 CHECK(jaylink_set_speed(handle,50));
 CHECK(jaylink_swd_io(handle,direction,output,input,n));
 printf("capture=");for(unsigned i=0;i<(n+7)/8;i++)printf("%02x",input[i]);puts("");
 unsigned ack=get(request+8,3);uint32_t id=get(request+11,32);unsigned parity=get(request+43,1);
 printf("ACK=%u DPIDR=%08x parity=%u expected=%u\n",ack,id,parity,__builtin_parity(id));
 if(ack!=1 || id!=0x2ba01477 || parity!=(unsigned)__builtin_parity(id)){result=1;goto cleanup;}
 /* Exactly one additional DP read, address 0x4; no SELECT/CTRL writes. */
 n=0;memset(direction,0,sizeof direction);memset(output,0,sizeof output);memset(input,0,sizeof input);
 for(unsigned i=0;i<8;i++)bit(1,(0x8d>>i)&1);
 for(unsigned i=0;i<38;i++)bit(0,0);
 for(unsigned i=0;i<8;i++)bit(1,0);
 assert(n==54 && output[0]==0x8d && direction[0]==255);
 CHECK(jaylink_swd_io(handle,direction,output,input,n));
 ack=get(8,3);uint32_t statusword=get(11,32);parity=get(43,1);
 printf("DP_ADDR4 ACK=%u value=%08x parity=%u expected=%u\n",ack,statusword,parity,__builtin_parity(statusword));
 if(ack!=1 || parity!=(unsigned)__builtin_parity(statusword) || (statusword & ~0x40u)!=0xc0000000u){fprintf(stderr,"Expected existing system-only power state; stop\n");result=1;goto cleanup;}
 /* Existing system-only power state; no new power request. Select AP0 bank0. */
 uint32_t answer=0;
 CHECK(transfer(handle,0,0,8,0,&answer));
 CHECK(transfer(handle,1,1,0,0,&answer));
 CHECK(transfer(handle,0,1,12,0,&answer));
 original_csw=answer;
 printf("CSW_BEFORE=%08x\n",original_csw);
 CHECK(transfer(handle,0,1,4,0,&answer));
 if((answer & ~0x40u)!=0xc0000000u){result=1;goto cleanup;}
 uint32_t proposed=(original_csw & ~7u)|2u;
 /* Write only SIZE. ACK alone is not proof of AP completion. */
 restore_needed=1;
 CHECK(transfer(handle,1,0,0,proposed,&answer));
 CHECK(transfer(handle,0,1,4,0,&answer));
 printf("POST_WRITE_DP_STATUS=%08x\n",answer);
 if((answer & ~0x40u)!=0xc0000000u){
   puts("POST_WRITE_STATE_UNEXPECTED=1");link_healthy=0;result=1;goto cleanup;
 }
 for(unsigned pass=0;pass<2;pass++){
   CHECK(transfer(handle,1,1,0,0,&answer));
   CHECK(transfer(handle,0,1,12,0,&answer));
   printf("CSW_READBACK_%u=%08x SIZE_MATCH=%u\n",pass,answer,(answer&7u)==2u);
   if((answer&7u)!=2u)result=1;
 }
 CHECK(transfer(handle,0,1,4,0,&answer));
 printf("FINAL_DP_STATUS=%08x\n",answer);
 if((answer & ~0x40u)!=0xc0000000u){link_healthy=0;result=1;}

cleanup:
 if(handle && restore_needed){
   if(restore_csw(handle,original_csw)!=JAYLINK_OK)result=1;
 }
 if(handle)jaylink_close(handle);
 if(devs)jaylink_free_devices(devs,1);
 if(ctx)jaylink_exit(ctx);
 puts("USB closed; no automatic retry");return result;
}
