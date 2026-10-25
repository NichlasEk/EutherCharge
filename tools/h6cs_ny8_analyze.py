#!/usr/bin/env python3
"""Offline structural analysis using externally supplied NY8 SLEIGH opcode patterns.
Opcode source: jamesw343/Ghidra_NY8A054E (MIT). No hardware access.
No claim that NY8A054E register semantics identify the unknown target.
"""
import argparse,collections,hashlib,json,re,struct
from pathlib import Path

def rules_from_sleigh(text):
    fields={name:(int(lo),int(hi)) for name,lo,hi in re.findall(r'^\s*(\w+)\s*=\s*\((\d+),(\d+)\)',text,re.M)}
    rules=[]
    for name,operands,cond in re.findall(r'^:(\w+)\s+([^\n]*?)\s+is\s+([^\n{]+)',text,re.M):
        mask=value=0
        for field,number in re.findall(r'(\w+)=(\d+)',cond):
            lo,hi=fields[field];m=((1<<(hi-lo+1))-1)<<lo
            mask|=m;value|=int(number)<<lo
        rules.append((mask,value,name,operands.strip()))
    return sorted(rules,key=lambda r:r[0].bit_count(),reverse=True)

def decode(w,pc,rules):
    for mask,val,name,ops in rules:
        if w&mask!=val:continue
        args=[];target=None
        if 'addr11' in ops:target=w&2047
        elif 'addr9' in ops:args=[f'PCHBUF[2:1]:0x{w&511:03X}']
        elif 'addr8' in ops:args=[f'PCHBUF[2:0]:0x{w&255:02X}']
        if target is not None:args=[f'0x{target:03X}']
        elif 'imm8' in ops:args=[f'0x{w&255:02X}']
        elif 'RReg' in ops:
            args=[f'R[0x{w&127:02X}]']
            if 'DestAR' in ops:args+=['R' if w&128 else 'ACC']
            if 'bs' in ops:args+=[str((w>>7)&7)]
        elif 'FReg' in ops:args=[f'F[0x{w&15:X}]']
        elif 'SReg' in ops:args=[f'S[0x{w&31:X}]']
        return dict(name=name,args=args,target=target,text=name+(' '+', '.join(args) if args else ''))
    return dict(name='UNKNOWN',args=[],target=None,text=f'.word 0x{w:04X}')

def analyze(raw,rules):
    words=list(struct.unpack('<'+'H'*(len(raw)//2),raw))
    ins=[decode(w,i,rules) for i,w in enumerate(words)]
    runs=[];start=None
    for i,w in enumerate(words+[1]):
        if not w and start is None:start=i
        if w and start is not None:runs.append(dict(start=start,end=i-1,length=i-start));start=None
    branches=[dict(address=i,kind=x['name'],target=x['target']) for i,x in enumerate(ins) if x['target'] is not None]
    seen=set();todo=[0,8];dynamic=[]
    while todo:
        pc=todo.pop()
        if pc in seen or not 0<=pc<len(ins):continue
        seen.add(pc);x=ins[pc];n=x['name']
        if n in ('UNKNOWN','RET','RETIA','RETIE'):continue
        if n in ('GOTO','CALL'):
            dynamic.append(pc)
            if n=='GOTO':continue
        if n=='LGOTO':todo.append(x['target']);continue
        if n=='LCALL':todo.append(x['target'])
        if n in ('GOTOA','CALLA') or (n=='MOVAR' and (words[pc]&127)==2):
            dynamic.append(pc)
            if n!='CALLA':continue
        if n in ('BTRSC','BTRSS','INCRSZ','DECRSZ'):todo.append(pc+2)
        todo.append(pc+1)
    report=dict(sha256=hashlib.sha256(raw).hexdigest(),word_count=len(words),zero_words=words.count(0),nonzero_words=len(words)-words.count(0),unique_words=len(set(words)),zero_runs=sorted(runs,key=lambda r:-r['length']),recognized_words=sum(x['name']!='UNKNOWN' for x in ins),unknown=[dict(address=i,word=words[i]) for i,x in enumerate(ins) if x['name']=='UNKNOWN'],instruction_counts=dict(collections.Counter(x['name'] for x in ins)),direct_branches=branches,statically_reachable_words=len(seen),reachable_unknown=[p for p in sorted(seen) if ins[p]['name']=='UNKNOWN'],unresolved_dynamic_branches=sorted(dynamic),reset=ins[0],interrupt_vector_8=ins[8],limitations=['Opcode model from related NY8A054E; no exact MCU ID','Reachability is an overapproximation of conditionals and incomplete at computed branches','Recognized opcodes alone do not prove code: tables may also decode'])
    return words,ins,seen,report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('dump',type=Path);p.add_argument('--sleigh',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=a.dump.read_bytes();rules=rules_from_sleigh(a.sleigh.read_text());words,ins,seen,r=analyze(raw,rules)
    a.output.mkdir(exist_ok=False)
    r['opcode_source_sha256']=hashlib.sha256(a.sleigh.read_bytes()).hexdigest()
    (a.output/'analysis.json').write_text(json.dumps(r,indent=2)+'\n')
    (a.output/'disassembly.txt').write_text('NY8 family candidate decoding; word addresses, R/F/S register pages unresolved by model.\n'+''.join(f'{i:04X}  {w:04X}  {ins[i]["text"]:<26}'+(' ; reachable' if i in seen else '')+'\n' for i,w in enumerate(words)))
    print(json.dumps({k:r[k] for k in ('word_count','zero_words','nonzero_words','unique_words','recognized_words','unknown','statically_reachable_words','reachable_unknown','reset','interrupt_vector_8','zero_runs')},indent=2))
if __name__=='__main__':main()
