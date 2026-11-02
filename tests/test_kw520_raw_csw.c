/* Host-only response injection: no USB calls. */
#define jaylink_swd_io mock_swd_io
#define main probe_main
#include "../firmware/kw520-probe/raw-csw-systemonly.c"
#undef main
#undef jaylink_swd_io

static unsigned calls, mock_ack=1, bad_parity;
static uint32_t mock_data;
static int mock_error=JAYLINK_OK;
static unsigned last_cmd;

int mock_swd_io(struct jaylink_device_handle *h, const uint8_t *dir,
               const uint8_t *out, uint8_t *in, uint16_t len) {
 (void)h;
 calls++;
 assert(len==110 && dir[0]==255);
 last_cmd=out[0];
 if(mock_error!=JAYLINK_OK)return mock_error;
 memset(in,0,(len+7)/8);
 for(unsigned i=0;i<3;i++)in[(8+i)/8]|=((mock_ack>>i)&1u)<<((8+i)%8);
 for(unsigned i=0;i<32;i++)in[(11+i)/8]|=((mock_data>>i)&1u)<<((11+i)%8);
 in[43/8]|=((unsigned)__builtin_parity(mock_data)^bad_parity)<<(43%8);
 return JAYLINK_OK;
}

int main(void) {
 uint32_t answer=0;
 mock_data=0x12345678;
 assert(transfer(NULL,1,1,0,0,&answer)==JAYLINK_OK);
 assert(answer==mock_data && last_cmd==0x87);
 assert(transfer(NULL,0,1,12,0,&answer)==JAYLINK_OK && last_cmd==0xbd);
 assert(transfer(NULL,1,0,0,2,&answer)==JAYLINK_OK && last_cmd==0xa3);
 for(unsigned ack=0;ack<=7;ack++) {
   if(ack==1)continue;
   link_healthy=1;mock_ack=ack;answer=0xdeadbeef;
   assert(transfer(NULL,1,1,0,0,&answer)!=JAYLINK_OK);
   assert(answer==0xdeadbeef && !link_healthy);
   unsigned before=calls;
   assert(restore_csw(NULL,0)!=JAYLINK_OK);
   assert(transfer(NULL,0,1,4,0,&answer)!=JAYLINK_OK);
   assert(calls==before); /* No cleanup write or retry after a bad ACK. */
 }
 link_healthy=1;mock_ack=1;bad_parity=1;answer=0xdeadbeef;
 assert(transfer(NULL,1,1,0,0,&answer)!=JAYLINK_OK);
 assert(answer==0xdeadbeef && !link_healthy);
 link_healthy=1;bad_parity=0;mock_error=JAYLINK_ERR;
 assert(transfer(NULL,1,1,0,0,&answer)!=JAYLINK_OK && !link_healthy);
 link_healthy=1;mock_error=JAYLINK_OK;mock_data=0;
 unsigned before=calls;
 assert(restore_csw(NULL,0)==JAYLINK_OK && calls==before+3);
 mock_data=2;
 assert(restore_csw(NULL,0)!=JAYLINK_OK);
 puts("PASS: OK/posted read commands, bad ACK, parity, transport failure, restore guards");
 return 0;
}
