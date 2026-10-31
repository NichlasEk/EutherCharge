#include <stdint.h>

#define REG32(address) (*(volatile uint32_t *)(address))
#define MAILBOX_BASE 0x20002000u
#define STACK_TOP 0x20002300u
#define GPIOA_BASE 0x48000000u
#define GPIOB_BASE 0x48000400u
#define SPI2_BASE 0x40003800u
#define WDT_BASE 0x40003000u
#define SCB_VTOR 0xe000ed08u
#define SCB_CFSR 0xe000ed28u
#define SCB_HFSR 0xe000ed2cu
#define PA8 0x00000100u

#define HELPER_MAGIC 0x4b575354u /* KWST */
#define ARM_MAGIC 0x41524d34u    /* ARM4 */
#define SECTOR_SIZE 4096u
#define BASELINE_CRC32 0xf5c23372u

struct mailbox {
    volatile uint32_t magic;
    volatile uint32_t state;
    volatile uint32_t arm;
    volatile uint32_t jedec;
    volatile uint32_t status_before;
    volatile uint32_t crc_before;
    volatile uint32_t status_wren_clear;
    volatile uint32_t status_cleared;
    volatile uint32_t status_wren_restore;
    volatile uint32_t status_restored;
    volatile uint32_t crc_after;
    volatile uint32_t spi_error;
    volatile uint32_t cleanup_attempted;
    volatile uint32_t cfsr;
    volatile uint32_t hfsr;
};

static volatile struct mailbox *const mb = (volatile struct mailbox *)MAILBOX_BASE;

__attribute__((noreturn)) void probe_start(void);
__attribute__((noreturn)) void probe_fault(void);

__attribute__((section(".vectors"), used, aligned(128)))
const uintptr_t probe_vectors[16] = {
    STACK_TOP, (uintptr_t)probe_start, (uintptr_t)probe_fault,
    (uintptr_t)probe_fault, (uintptr_t)probe_fault, (uintptr_t)probe_fault,
    (uintptr_t)probe_fault, 0, 0, 0, 0, (uintptr_t)probe_fault,
    (uintptr_t)probe_fault, 0, (uintptr_t)probe_fault, (uintptr_t)probe_fault,
};

static inline void barrier(void) {
    __asm__ volatile("dsb sy\n\tisb sy" ::: "memory");
}

static inline void refresh_wdt(void) {
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
    mb->spi_error = 4u;
    return 0;
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

static uint32_t crc32_update(uint32_t crc, uint8_t byte) {
    crc ^= byte;
    for (uint32_t bit = 0; bit < 8u; ++bit) {
        crc = (crc >> 1) ^ ((crc & 1u) ? 0xedb88320u : 0u);
    }
    return crc;
}

static int sector_crc32(uint32_t *result) {
    uint8_t ignored, value;
    drain_receive();
    cs_low();
    int ok = spi_xfer(0x03u, &ignored) && spi_xfer(0x00u, &ignored) &&
             spi_xfer(0x30u, &ignored) && spi_xfer(0x00u, &ignored);
    uint32_t crc = 0xffffffffu;
    for (uint32_t index = 0; ok && index < SECTOR_SIZE; ++index) {
        ok = spi_xfer(0xffu, &value);
        if (ok) {
            crc = crc32_update(crc, value);
        }
    }
    ok = ok && wait_spi_idle();
    cs_high();
    if (ok) {
        *result = ~crc;
    }
    return ok;
}

static int live_configuration_matches(void) {
    uint32_t acfgr = REG32(GPIOA_BASE + 0x00u);
    uint32_t aodt = REG32(GPIOA_BASE + 0x14u);
    uint32_t bcfgr = REG32(GPIOB_BASE + 0x00u);
    uint32_t ctrl1 = REG32(SPI2_BASE + 0x00u);
    uint32_t sts = REG32(SPI2_BASE + 0x08u);
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
    mb->spi_error = 0u;
    mb->cleanup_attempted = 0u;
    REG32(SCB_VTOR) = (uint32_t)(uintptr_t)probe_vectors;
    barrier();
    refresh_wdt();

    if (!live_configuration_matches()) {
        stop(0xe1u);
    }
    if (arm != ARM_MAGIC) {
        stop(0xe2u);
    }
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
    if (!sector_crc32((uint32_t *)&mb->crc_before) ||
        mb->crc_before != BASELINE_CRC32) {
        stop(0xe6u);
    }
    refresh_wdt();

    mb->state = 0x20u;
    if (!instruction(0x06u) || !read_status(&status)) {
        best_effort_restore_status();
        stop(0xe7u);
    }
    mb->status_wren_clear = status;
    if (status != 0x1au || !write_status(0x00u) || !wait_ready(&status)) {
        best_effort_restore_status();
        stop(0xe8u);
    }
    mb->status_cleared = status;
    if (status != 0x00u) {
        best_effort_restore_status();
        stop(0xe9u);
    }

    mb->state = 0x30u;
    if (!instruction(0x06u) || !read_status(&status)) {
        best_effort_restore_status();
        stop(0xeau);
    }
    mb->status_wren_restore = status;
    if (status != 0x02u || !write_status(0x18u) || !wait_ready(&status)) {
        best_effort_restore_status();
        stop(0xebu);
    }
    mb->status_restored = status;
    (void)instruction(0x04u);
    if (status != 0x18u) {
        best_effort_restore_status();
        stop(0xecu);
    }
    refresh_wdt();
    if (!sector_crc32((uint32_t *)&mb->crc_after) ||
        mb->crc_after != BASELINE_CRC32) {
        best_effort_restore_status();
        stop(0xedu);
    }
    stop(0x44u);
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
