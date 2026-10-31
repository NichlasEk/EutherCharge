#include <stdint.h>

#define REG32(address) (*(volatile uint32_t *)(address))
#ifndef KW_MAILBOX_BASE
#define KW_MAILBOX_BASE 0x20002000u
#endif
#ifndef KW_RESTORE_BUFFER
#define KW_RESTORE_BUFFER 0x20002100u
#endif
#ifndef KW_STACK_TOP
#define KW_STACK_TOP 0x20003f00u
#endif

#define MAILBOX_BASE KW_MAILBOX_BASE
#define RESTORE_BUFFER KW_RESTORE_BUFFER
#define STACK_TOP KW_STACK_TOP
#define GPIOA_BASE 0x48000000u
#define GPIOB_BASE 0x48000400u
#define SPI2_BASE 0x40003800u
#define WDT_BASE 0x40003000u
#define SCB_VTOR 0xe000ed08u
#define SCB_CFSR 0xe000ed28u
#define SCB_HFSR 0xe000ed2cu
#define PA8 0x00000100u

#ifndef KW_HELPER_MAGIC
#define KW_HELPER_MAGIC 0x4b575052u /* KWPR */
#endif
#ifndef KW_ARM_MAGIC
#define KW_ARM_MAGIC 0x41524d32u /* ARM2 */
#endif
#ifndef KW_BUFFER_CRC32
#define KW_BUFFER_CRC32 0xf5c23372u
#endif
#ifndef KW_EXPECTED_TARGET_CRC32
#define KW_EXPECTED_TARGET_CRC32 0x7985c2f6u
#endif
#ifndef KW_EXPECTED_FINAL_CRC32
#define KW_EXPECTED_FINAL_CRC32 0xf5c23372u
#endif

#define HELPER_MAGIC KW_HELPER_MAGIC
#define ARM_MAGIC KW_ARM_MAGIC
#define SECTOR_ADDRESS 0x00003000u
#define SECTOR_SIZE 4096u
#define ERASED_CRC32 0xf154670au

struct mailbox {
    volatile uint32_t magic;
    volatile uint32_t state;
    volatile uint32_t arm;
    volatile uint32_t jedec;
    volatile uint32_t status_before;
    volatile uint32_t block_protection;
    volatile uint32_t buffer_crc32;
    volatile uint32_t target_crc32_before;
    volatile uint32_t target_crc32_erased;
    volatile uint32_t target_crc32_after;
    volatile uint32_t pages_done;
    volatile uint32_t status_last;
    volatile uint32_t spi_error;
    volatile uint32_t cfsr;
    volatile uint32_t hfsr;
    volatile uint32_t raw_gpioa_cfgr;
    volatile uint32_t raw_gpioa_odt;
    volatile uint32_t raw_gpiob_cfgr;
    volatile uint32_t raw_spi2_ctrl1;
    volatile uint32_t raw_spi2_sts;
    volatile uint32_t status_cleared;
    volatile uint32_t status_restored;
    volatile uint32_t cleanup_attempted;
};

static volatile struct mailbox *const mb = (volatile struct mailbox *)MAILBOX_BASE;
static const uint8_t *const restore = (const uint8_t *)RESTORE_BUFFER;

__attribute__((noreturn)) void probe_start(void);
__attribute__((noreturn)) void probe_fault(void);

__attribute__((section(".vectors"), used, aligned(128)))
const uintptr_t probe_vectors[16] = {
    STACK_TOP,
    (uintptr_t)probe_start,
    (uintptr_t)probe_fault,
    (uintptr_t)probe_fault,
    (uintptr_t)probe_fault,
    (uintptr_t)probe_fault,
    (uintptr_t)probe_fault,
    0,
    0,
    0,
    0,
    (uintptr_t)probe_fault,
    (uintptr_t)probe_fault,
    0,
    (uintptr_t)probe_fault,
    (uintptr_t)probe_fault,
};

static inline void barrier(void) {
    __asm__ volatile("dsb sy\n\tisb sy" ::: "memory");
}

static inline void watchdog_refresh(void) {
    REG32(WDT_BASE) = 0x0000aaaau;
}

static inline void cs_low(void) {
    REG32(GPIOA_BASE + 0x28u) = PA8;
    barrier();
}

static inline void cs_high(void) {
    REG32(GPIOA_BASE + 0x18u) = PA8;
    barrier();
}

static int spi_xfer(uint8_t out, uint8_t *in) {
    uint32_t timeout = 0x40000u;
    while ((REG32(SPI2_BASE + 0x08u) & 2u) == 0u) {
        if (--timeout == 0u) {
            mb->spi_error = 1u;
            return 0;
        }
    }
    REG32(SPI2_BASE + 0x0cu) = out;
    timeout = 0x40000u;
    while ((REG32(SPI2_BASE + 0x08u) & 1u) == 0u) {
        if (--timeout == 0u) {
            mb->spi_error = 2u;
            return 0;
        }
    }
    *in = (uint8_t)REG32(SPI2_BASE + 0x0cu);
    return 1;
}

static int wait_spi_idle(void) {
    uint32_t timeout = 0x40000u;
    while ((REG32(SPI2_BASE + 0x08u) & 0x80u) != 0u) {
        if (--timeout == 0u) {
            mb->spi_error = 3u;
            return 0;
        }
    }
    return 1;
}

static void drain_receive(void) {
    if ((REG32(SPI2_BASE + 0x08u) & 1u) != 0u) {
        (void)REG32(SPI2_BASE + 0x0cu);
    }
}

static int instruction(uint8_t opcode) {
    uint8_t ignored;
    drain_receive();
    cs_low();
    int ok = spi_xfer(opcode, &ignored) && wait_spi_idle();
    cs_high();
    return ok;
}

static int read_status(uint8_t *status) {
    uint8_t ignored;
    drain_receive();
    cs_low();
    int ok = spi_xfer(0x05u, &ignored) && spi_xfer(0xffu, status) &&
             wait_spi_idle();
    cs_high();
    return ok;
}

static int write_status(uint8_t status) {
    uint8_t ignored;
    drain_receive();
    cs_low();
    int ok = spi_xfer(0x01u, &ignored) && spi_xfer(status, &ignored) &&
             wait_spi_idle();
    cs_high();
    return ok;
}

static int read_identification(uint32_t *jedec) {
    uint8_t ignored, id0, id1, id2;
    drain_receive();
    cs_low();
    int ok = spi_xfer(0x9fu, &ignored) && spi_xfer(0xffu, &id0) &&
             spi_xfer(0xffu, &id1) && spi_xfer(0xffu, &id2) &&
             wait_spi_idle();
    cs_high();
    if (ok) {
        *jedec = ((uint32_t)id0 << 16) | ((uint32_t)id1 << 8) | id2;
    }
    return ok;
}

static int read_block_protection(uint8_t *protection) {
    uint8_t ignored;
    drain_receive();
    cs_low();
    int ok = spi_xfer(0x3cu, &ignored) && spi_xfer(0x00u, &ignored) &&
             spi_xfer(0x30u, &ignored) && spi_xfer(0x00u, &ignored) &&
             spi_xfer(0xffu, protection) && wait_spi_idle();
    cs_high();
    return ok;
}

static uint32_t crc32_update(uint32_t crc, uint8_t byte) {
    crc ^= byte;
    for (uint32_t bit = 0; bit < 8u; ++bit) {
        crc = (crc >> 1) ^ ((crc & 1u) ? 0xedb88320u : 0u);
    }
    return crc;
}

static uint32_t buffer_crc32(void) {
    uint32_t crc = 0xffffffffu;
    for (uint32_t index = 0; index < SECTOR_SIZE; ++index) {
        crc = crc32_update(crc, restore[index]);
    }
    return ~crc;
}

static int target_crc32(uint32_t *result) {
    uint8_t ignored, value;
    drain_receive();
    cs_low();
    if (!spi_xfer(0x03u, &ignored) || !spi_xfer(0x00u, &ignored) ||
        !spi_xfer(0x30u, &ignored) || !spi_xfer(0x00u, &ignored)) {
        cs_high();
        return 0;
    }
    uint32_t crc = 0xffffffffu;
    for (uint32_t index = 0; index < SECTOR_SIZE; ++index) {
        if (!spi_xfer(0xffu, &value)) {
            cs_high();
            return 0;
        }
        crc = crc32_update(crc, value);
    }
    if (!wait_spi_idle()) {
        cs_high();
        return 0;
    }
    cs_high();
    *result = ~crc;
    return 1;
}

static int write_enable_checked(uint8_t expected, uint8_t *status) {
    return instruction(0x06u) && read_status(status) && *status == expected;
}

static int wait_ready(uint8_t *status) {
    uint32_t polls = 2000000u;
    do {
        if (!read_status(status)) {
            return 0;
        }
        if ((*status & 1u) == 0u) {
            return 1;
        }
    } while (--polls != 0u);
    return 0;
}

static int erase_fixed_sector(void) {
    uint8_t ignored;
    drain_receive();
    cs_low();
    int ok = spi_xfer(0x20u, &ignored) && spi_xfer(0x00u, &ignored) &&
             spi_xfer(0x30u, &ignored) && spi_xfer(0x00u, &ignored);
    if (ok) {
        ok = wait_spi_idle();
    }
    cs_high();
    return ok;
}

static int program_page(uint32_t page) {
    uint8_t ignored;
    uint32_t address = SECTOR_ADDRESS + page * 256u;
    drain_receive();
    cs_low();
    int ok = spi_xfer(0x02u, &ignored) &&
             spi_xfer((uint8_t)(address >> 16), &ignored) &&
             spi_xfer((uint8_t)(address >> 8), &ignored) &&
             spi_xfer((uint8_t)address, &ignored);
    for (uint32_t index = 0; ok && index < 256u; ++index) {
        ok = spi_xfer(restore[page * 256u + index], &ignored);
    }
    if (ok) {
        ok = wait_spi_idle();
    }
    cs_high();
    return ok;
}

static int live_configuration_matches(void) {
    uint32_t acfgr = REG32(GPIOA_BASE + 0x00u);
    uint32_t aodt = REG32(GPIOA_BASE + 0x14u);
    uint32_t bcfgr = REG32(GPIOB_BASE + 0x00u);
    uint32_t ctrl1 = REG32(SPI2_BASE + 0x00u);
    uint32_t sts = REG32(SPI2_BASE + 0x08u);
    mb->raw_gpioa_cfgr = acfgr;
    mb->raw_gpioa_odt = aodt;
    mb->raw_gpiob_cfgr = bcfgr;
    mb->raw_spi2_ctrl1 = ctrl1;
    mb->raw_spi2_sts = sts;
    return ((acfgr >> 16) & 3u) == 1u && (aodt & PA8) != 0u &&
           ((bcfgr >> 26) & 3u) == 2u && ((bcfgr >> 28) & 3u) == 2u &&
           ((bcfgr >> 30) & 3u) == 2u && (ctrl1 & 0xffffu) == 0x0357u &&
           (sts & 2u) != 0u;
}

static void best_effort_restore_status(void) {
    uint8_t status;
    mb->cleanup_attempted = 1u;
    if (instruction(0x06u)) {
        (void)write_status(0x18u);
        (void)wait_ready(&status);
    }
    (void)instruction(0x04u);
}

__attribute__((noreturn)) static void stop(uint32_t state) {
    cs_high();
    mb->state = state;
    barrier();
    for (;;) {
        __asm__ volatile("nop");
    }
}

__attribute__((section(".text.start"), noreturn)) void probe_start(void) {
    __asm__ volatile("cpsid i");
    uint32_t arm = mb->arm;
    mb->magic = HELPER_MAGIC;
    mb->state = 1u;
    mb->pages_done = 0u;
    mb->spi_error = 0u;
    mb->cleanup_attempted = 0u;
    REG32(SCB_VTOR) = (uint32_t)(uintptr_t)probe_vectors;
    barrier();

    if (!live_configuration_matches()) {
        stop(0xe1u);
    }
    if (arm != ARM_MAGIC) {
        stop(0xe2u);
    }
    watchdog_refresh();
    if (!read_identification((uint32_t *)&mb->jedec) || mb->jedec != 0x001c3016u) {
        stop(0xe3u);
    }
    uint8_t status;
    if (!read_status(&status)) {
        stop(0xe4u);
    }
    mb->status_before = status;
    if (status != 0x18u) {
        stop(0xe5u);
    }
    uint8_t protection;
    if (!read_block_protection(&protection)) {
        stop(0xe6u);
    }
    mb->block_protection = protection;
    if (protection != 0xffu) {
        stop(0xe7u);
    }
    mb->buffer_crc32 = buffer_crc32();
    watchdog_refresh();
    if (mb->buffer_crc32 != KW_BUFFER_CRC32) {
        stop(0xe8u);
    }
    if (!target_crc32((uint32_t *)&mb->target_crc32_before)) {
        stop(0xe9u);
    }
    watchdog_refresh();
    if (mb->target_crc32_before == KW_EXPECTED_FINAL_CRC32) {
        stop(0x42u);
    }
    if (mb->target_crc32_before != KW_EXPECTED_TARGET_CRC32) {
        stop(0xeau);
    }

    mb->state = 0x18u;
    if (!write_enable_checked(0x1au, &status) || !write_status(0x00u) ||
        !wait_ready(&status) || status != 0x00u) {
        best_effort_restore_status();
        stop(0xebu);
    }
    mb->status_cleared = status;

    mb->state = 0x20u;
    if (!write_enable_checked(0x02u, &status)) {
        best_effort_restore_status();
        stop(0xebu);
    }
    if (!erase_fixed_sector() || !wait_ready(&status)) {
        best_effort_restore_status();
        stop(0xecu);
    }
    if (status != 0x00u) {
        best_effort_restore_status();
        stop(0xecu);
    }
    watchdog_refresh();
    (void)instruction(0x04u);
    mb->status_last = status;
    if (!target_crc32((uint32_t *)&mb->target_crc32_erased) ||
        mb->target_crc32_erased != ERASED_CRC32) {
        best_effort_restore_status();
        stop(0xedu);
    }

    mb->state = 0x30u;
    for (uint32_t page = 0; page < 16u; ++page) {
        if (!write_enable_checked(0x02u, &status)) {
            best_effort_restore_status();
            stop(0xeeu);
        }
        if (!program_page(page) || !wait_ready(&status)) {
            best_effort_restore_status();
            stop(0xefu);
        }
        if (status != 0x00u) {
            best_effort_restore_status();
            stop(0xefu);
        }
        (void)instruction(0x04u);
        mb->pages_done = page + 1u;
        watchdog_refresh();
    }
    mb->status_last = status;
    if (!target_crc32((uint32_t *)&mb->target_crc32_after)) {
        best_effort_restore_status();
        stop(0xf1u);
    }
    if (mb->target_crc32_after != KW_EXPECTED_FINAL_CRC32) {
        best_effort_restore_status();
        stop(0xf2u);
    }
    if (!write_enable_checked(0x02u, &status) || !write_status(0x18u) ||
        !wait_ready(&status) || status != 0x18u) {
        best_effort_restore_status();
        stop(0xf3u);
    }
    mb->status_restored = status;
    (void)instruction(0x04u);
    stop(0x41u);
}

__attribute__((noreturn)) void probe_fault(void) {
    __asm__ volatile("cpsid i");
    cs_high();
    mb->magic = HELPER_MAGIC;
    mb->cfsr = REG32(SCB_CFSR);
    mb->hfsr = REG32(SCB_HFSR);
    mb->state = 0xf0u;
    barrier();
    for (;;) {
        __asm__ volatile("nop");
    }
}
