MEMORY
{
  ORACLE (rwx) : ORIGIN = 0x20001000, LENGTH = 0x400
}

SECTIONS
{
  .vectors ORIGIN(ORACLE) :
  {
    KEEP(*(.vectors))
  } > ORACLE

  .text :
  {
    *(.text.start)
    *(.text*)
    *(.rodata*)
  } > ORACLE

  /DISCARD/ :
  {
    *(.ARM.attributes)
    *(.comment)
  }
}

ASSERT(SIZEOF(.vectors) + SIZEOF(.text) <= LENGTH(ORACLE), "call oracle exceeds MPU-protected code region")
