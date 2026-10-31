MEMORY
{
  RAMPROBE (rwx) : ORIGIN = 0x20001a00, LENGTH = 0x500
}

SECTIONS
{
  .vectors ORIGIN(RAMPROBE) : { KEEP(*(.vectors)) } > RAMPROBE
  .text : { *(.text.start) *(.text*) *(.rodata*) } > RAMPROBE
  /DISCARD/ : { *(.ARM.attributes) *(.comment) }
}

ASSERT(SIZEOF(.vectors) + SIZEOF(.text) <= LENGTH(RAMPROBE), "sector probe exceeds reserved code window")
