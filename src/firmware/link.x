ENTRY(Reset);

MEMORY
{
    SDRAM : ORIGIN = 0x00100000, LENGTH = 0x1FF00000
}

SECTIONS
{
    __text_start = .;
    .text :
    {
        KEEP(*(.text.exceptions));
        *(.text.boot);
        *(.text .text.*);
    } > SDRAM
    __text_end = .;

    __exidx_start = .;
    .ARM.exidx :
    {
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
    } > SDRAM
    __exidx_end = .;

    .ARM.extab :
    {
        * (.ARM.extab*)
    } > SDRAM
 
    .rodata : ALIGN(4)
    {
        *(.rodata .rodata.*);
    } > SDRAM
 
    .data : ALIGN(4)
    {
        *(.data .data.*);
    } > SDRAM
 
    .bss (NOLOAD) : ALIGN(4)
    {
        __bss_start = .;
        *(.bss .bss.*);
        . = ALIGN(4);
        __bss_end = .;
    } > SDRAM

    .heap (NOLOAD) : ALIGN(8)
    {
        __heap0_start = .;
        . += 0x8000000;
        __heap0_end = .;
    } > SDRAM

    .stack1 (NOLOAD) : ALIGN(8)
    {
        __stack1_end = .;
        . += 0x2000;
        __stack1_start = .;
    } > SDRAM

    .stack0 (NOLOAD) : ALIGN(8)
    {
        __stack0_end = .;
        . += 0x20000;
        __stack0_start = .;
    } > SDRAM

    .irq_stack1 (NOLOAD) : ALIGN(8)
    {
        __irq_stack1_end = .;
        . += 0x100;
        __irq_stack1_start = .;
    } > SDRAM

    .irq_stack0 (NOLOAD) : ALIGN(8)
    {
        __irq_stack0_end = .;
        . += 0x100;
        __irq_stack0_start = .;
    } > SDRAM
}
