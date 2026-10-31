MEMORY
{
  RAMHELPER (rwx) : ORIGIN = 0x20001a00, LENGTH = 0x700
}

SECTIONS
{
  .vectors ORIGIN(RAMHELPER) : ALIGN(128) { KEEP(*(.vectors)) } > RAMHELPER
  .text : { *(.text.start) *(.text*) *(.rodata*) } > RAMHELPER
  /DISCARD/ : { *(.ARM.attributes) *(.comment) *(.eh_frame*) }
}

ASSERT(SIZEOF(.vectors) + SIZEOF(.text) <= LENGTH(RAMHELPER), "mutation helper exceeds reserved code window")
