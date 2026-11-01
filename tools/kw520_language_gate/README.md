# KW520 language-directory gate

This probe changes only external-flash sector `0x003000`:

- declared language count `8 -> 9` at `0x003200`;
- erased slot 9 becomes a structurally valid duplicate of slot 8;
- the duplicate retains all 162 ordinary-string targets, the one DTC target,
  and the zero-length third class from the already validated Italian entry.

It does not claim an internal-flash read primitive. Its purpose is to determine
whether normally booted protected firmware consumes the directory count and a
new valid descriptor. The generator accepts only the qualified local 4 MiB
EutherCharge readback and emits exact original/probe sectors plus a manifest.

Never leave the probe installed after observation. Restore sector `0x003000`,
cold-start, and verify `Huvudmeny` and button response.

The first directory-only probe was intentionally discriminating: slot 9 and
the directory count were installed, but the separate active-ID list at
`0x003043` was unchanged. The physical menu correctly showed no ninth item.
The follow-up `run-list-install.sh` changes the list count at `0x003041`, inserts
ID 9 into that list, and installs the same valid descriptor. Its purpose is a
paired SRAM comparison, not the cosmetic extra language itself.
