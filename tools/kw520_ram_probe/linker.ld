MEMORY
{
  RAMPROBE (rwx) : ORIGIN = 0x20001000, LENGTH = 0x700
}

SECTIONS
{
  .vectors ORIGIN(RAMPROBE) :
  {
    KEEP(*(.vectors))
  } > RAMPROBE

  .text :
  {
    *(.text.start)
    *(.text*)
    *(.rodata*)
  } > RAMPROBE

  /DISCARD/ :
  {
    *(.ARM.attributes)
    *(.comment)
  }
}

ASSERT(SIZEOF(.vectors) + SIZEOF(.text) <= LENGTH(RAMPROBE), "RAM probe exceeds reserved code window")
