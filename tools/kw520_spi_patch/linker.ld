MEMORY
{
  RAMHELPER (rwx) : ORIGIN = 0x20001000, LENGTH = 0x1000
}

SECTIONS
{
  .vectors ORIGIN(RAMHELPER) : ALIGN(128) { KEEP(*(.vectors)) } > RAMHELPER
  .text : { *(.text.start) *(.text*) *(.rodata*) } > RAMHELPER
  /DISCARD/ : { *(.ARM.attributes) *(.comment) *(.eh_frame*) }
}

ASSERT(SIZEOF(.vectors) + SIZEOF(.text) <= LENGTH(RAMHELPER), "format probe exceeds reserved code window")
