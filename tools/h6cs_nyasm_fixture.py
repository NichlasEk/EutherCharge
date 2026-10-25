#!/usr/bin/env python3
"""Generate authored NY8 carry probes or verify a manufacturer assembler listing.
No ROM input, hardware access or executable invocation. SDK remains external.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
g=p.add_mutually_exclusive_group(required=True)
g.add_argument('--source',type=Path,help='write generated carry-gpr.asm')
g.add_argument('--listing',type=Path,help='verify carry-gpr.lst and print independent words')
a=p.parse_args()
if a.source:
    lines=['; EutherCharge authored encoding fixture: both destinations of every GPR.', '    org 0']
    for op in ('adcar','sbcar'):
        for register in range(32,128):
            for destination in (0,1):
                lines.append(f'    {op} 0x{register:02x},{destination}')
    a.source.write_text('\n'.join(lines+['    end'])+'\n')
else:
    raw=a.listing.read_bytes()
    rows=re.findall(r'^\s+([0-9A-F]{4}) ([0-9A-F]{4})\s+.*?\s+(adcar|sbcar) 0x([0-9a-f]+),([01])$',raw.decode(),re.M)
    expected=[(op,r,d) for op in ('adcar','sbcar') for r in range(32,128) for d in (0,1)]
    if len(rows)!=384:raise SystemExit('Expected384 assembled instructions')
    cases=[]
    for index,((pc,word,op,register,destination),operands) in enumerate(zip(rows,expected)):
        r,d=int(register,16),int(destination)
        if int(pc,16)!=index or (op,r,d)!=operands:raise SystemExit('Unexpected instruction ordering')
        cases.append(dict(name=op.upper(),register=r,destination=d,word=int(word,16)))
    print(json.dumps(dict(listingSha256=hashlib.sha256(raw).hexdigest(),cases=cases),indent=2))
