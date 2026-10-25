#!/usr/bin/env python3
"""Bounded offline execution of identified LCD initializer only (not full MCU emulation)."""
import argparse,json,struct
from pathlib import Path
from h6cs_ny8_analyze import decode,rules_from_sleigh

def trace(words,rules,carry=0,fill=0):
    r=[fill]*128;acc=fill;pc=0x751;stack=[];frames=[];bits=None
    for step in range(2000):
        w=words[pc];d=decode(w,pc,rules);name=d['name'];nxt=pc+1;reg=w&127;bit=(w>>7)&7
        oldpa,oldpb=r[5],r[6]
        if name=='MOVIA':acc=w&255
        elif name=='MOVAR':r[reg]=acc
        elif name=='MOVR':
            if not w&128:acc=r[reg]
        elif name=='BSR':r[reg]|=1<<bit
        elif name=='BCR':r[reg]&=~(1<<bit)
        elif name=='BTRSS':nxt+=bool(r[reg]&(1<<bit))
        elif name=='RLR':
            val=((r[reg]<<1)|carry)&255;carry=r[reg]>>7
            if w&128:r[reg]=val
            else:acc=val
        elif name=='DECRSZ':
            val=(r[reg]-1)&255
            if w&128:r[reg]=val
            else:acc=val
            nxt+=val==0
        elif name=='LCALL':stack.append(nxt);nxt=d['target']
        elif name=='LGOTO':nxt=d['target']
        elif name=='RET':
            if not stack:return frames,step+1
            nxt=stack.pop()
        else:raise ValueError(f'Unsupported instruction at {pc:04X}: {name}')
        if oldpa&1 and not r[5]&1:bits=''
        if bits is not None and not oldpb&32 and r[6]&32:bits+=str((r[6]>>4)&1)
        if not oldpa&1 and r[5]&1 and bits is not None:
            frames.append(bits);bits=None
        pc=nxt
    raise RuntimeError('Execution bound exceeded')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dump',type=Path);p.add_argument('--sleigh',type=Path,required=True);p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=a.dump.read_bytes();words=struct.unpack('<2048H',raw);rules=rules_from_sleigh(a.sleigh.read_text())
    observed=[f['bits'] for f in json.loads(a.capture.read_text())['frames'] if f.get('decode')=='command_frame_candidate']
    variants=[]
    for carry in (0,1):
        for fill in (0,0x55,0xaa,0xff):
            frames,steps=trace(words,rules,carry,fill)
            assert frames==observed,(frames,observed)
            variants.append(dict(initial_carry=carry,initial_register_fill=fill,steps=steps,frames=frames))
    result=dict(entry_word_address='0x751',called_from_startup_word_address='0x17f',cs='R05 bit0 (candidate PA0)',wr='R06 bit5 (candidate PB5)',data='R06 bit4 (candidate PB4)',matches_observed_capture=True,observed_capture=str(a.capture),commands=[int(f[3:11],2) for f in observed],variants=variants,limitations='Offline initializer execution only, no full chip emulation or post-read live LCD validation')
    with a.output.open('x') as f:json.dump(result,f,indent=2)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
