ENTRY(probe_start)
MEMORY { RAM (rwx) : ORIGIN = 0x20001a00, LENGTH = 0x700 }
SECTIONS {
  .text : { *(.text*) *(.rodata*) } > RAM
  /DISCARD/ : { *(.ARM.attributes) *(.comment) }
}
ASSERT(SIZEOF(.text) <= 0x700, "probe code exceeds reserved window")
