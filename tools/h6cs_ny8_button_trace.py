#!/usr/bin/env python3
"""Offline execution of button handler only; no cycle timing or peripheral emulation."""
import json,struct,argparse
from pathlib import Path
from h6cs_ny8_analyze import decode,rules_from_sleigh
class CPU:
    def __init__(self,words,rules):self.words=words;self.rules=rules;self.r=[0]*128;self.bank1=[0]*32;self.a=0
    def read(self,i):return self.bank1[i-32] if 32<=i<64 and self.r[3]&64 else self.r[i]
    def write(self,i,v):
        if 32<=i<64 and self.r[3]&64:self.bank1[i-32]=v&255
        else:self.r[i]=v&255
    def flag(self,n,v):self.r[3]=(self.r[3]&~(1<<n))|(bool(v)<<n)
    def run(self,pressed):
        self.r[5]=(self.r[5]&~32)|(0 if pressed else 32)
        pc=0x5dc;stack=[]
        for _ in range(500):
            w=self.words[pc];d=decode(w,pc,self.rules);n=d['name'];rr=w&127;bit=(w>>7)&7;nxt=pc+1
            if n=='MOVIA':self.a=w&255
            elif n=='MOVAR':self.write(rr,self.a)
            elif n=='MOVR':
                v=self.read(rr);self.flag(2,v==0)
                if not w&128:self.a=v
            elif n=='BSR':self.write(rr,self.read(rr)|(1<<bit))
            elif n=='BCR':self.write(rr,self.read(rr)&~(1<<bit))
            elif n in ('BTRSS','BTRSC'):nxt+=bool(self.read(rr)&(1<<bit))==(n=='BTRSS')
            elif n=='CLRR':self.write(rr,0);self.flag(2,True)
            elif n=='XORIA':self.a^=w&255;self.flag(2,self.a==0)
            elif n=='INCR':
                v=(self.read(rr)+1)&255;self.flag(2,v==0)
                if w&128:self.write(rr,v)
                else:self.a=v
            elif n=='SUBAR':
                old=self.read(rr);v=(old-self.a)&255;self.flag(0,old>=self.a);self.flag(1,(old&15)>=(self.a&15));self.flag(2,v==0)
                if w&128:self.write(rr,v)
                else:self.a=v
            elif n=='LCALL':stack.append(nxt);nxt=d['target']
            elif n=='LGOTO':nxt=d['target']
            elif n=='RET':
                if not stack:return
                nxt=stack.pop()
            else:raise RuntimeError((pc,n))
            pc=nxt
        raise RuntimeError('Instruction budget exceeded')

def main():
    p=argparse.ArgumentParser();p.add_argument('dump',type=Path);p.add_argument('--sleigh',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    words=struct.unpack('<2048H',a.dump.read_bytes());rules=rules_from_sleigh(a.sleigh.read_text());cases=[]
    for mode in range(4):
        c=CPU(words,rules);c.r[0x4b]=mode;c.r[0x3e]=3
        c.run(False)
        for _ in range(20):c.run(True)
        assert c.r[0x4b]==mode
        c.run(True);assert c.r[0x4b]==(mode+1)%4
        assert c.r[0x3e]==1
        for _ in range(400):c.run(True)
        assert c.r[0x4b]==(mode+1)%4
        assert c.bank1[3]==250
        c.run(False);assert c.bank1[3]==0
        cases.append(dict(initial_mode=mode,mode_after_21_pressed_polls=c.r[0x4b],no_repeat_after_400_more_polls=True,released_counter=0,new_state=c.r[0x3e]))
    c=CPU(words,rules)
    for _ in range(100):
        for _ in range(10):c.run(True)
        c.run(False)
    assert c.r[0x4b]==0
    report=dict(handler='0x5DC',pin='candidate PA5/SOP16 pin4',active_low=True,first_event_pressed_poll=21,continuous_hold_repeats=False,short_bounce_test_passed=True,cases=cases,limitation='Poll count verified, milliseconds depend on unverified clock/config; synthetic caller state only')
    with a.output.open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
