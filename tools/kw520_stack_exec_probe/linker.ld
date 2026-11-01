ENTRY(payload_entry)
SECTIONS
{
    . = 0x20003978;
    .text : { KEEP(*(.text)) }
    /DISCARD/ : { *(.comment) *(.ARM.attributes) *(.note*) }
}
