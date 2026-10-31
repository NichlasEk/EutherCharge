CROSS ?= arm-none-eabi-
BUILD_DIR ?= ../../build/kw520-spi-patch
CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size
ELFS := $(BUILD_DIR)/format_probe.elf $(BUILD_DIR)/restore_sector.elf \
	$(BUILD_DIR)/pointer_probe.elf $(BUILD_DIR)/pointer_restore.elf \
	$(BUILD_DIR)/protection_roundtrip.elf \
	$(BUILD_DIR)/status_roundtrip.elf
BINS := $(BUILD_DIR)/format_probe.bin $(BUILD_DIR)/restore_sector.bin \
	$(BUILD_DIR)/pointer_probe.bin $(BUILD_DIR)/pointer_restore.bin \
	$(BUILD_DIR)/protection_roundtrip.bin \
	$(BUILD_DIR)/status_roundtrip.bin

CFLAGS := -mcpu=cortex-m4 -mthumb -Os -ffreestanding -fno-builtin \
	-ffunction-sections -fdata-sections -Wall -Wextra -Werror
LDFLAGS := -nostdlib -Wl,-T,linker.ld -Wl,--build-id=none \
	-Wl,--gc-sections

.PHONY: all inspect clean
all: $(BINS)
$(BUILD_DIR):
	mkdir -p $@
$(BUILD_DIR)/restore_sector.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/restore_sector.map -o $@ $<
$(BUILD_DIR)/pointer_probe.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b575044u -DKW_ARM_MAGIC=0x41524d35u \
		-DKW_BUFFER_CRC32=0x14b0524bu \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0x14b0524bu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/pointer_probe.map -o $@ $<
$(BUILD_DIR)/pointer_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b57524fu -DKW_ARM_MAGIC=0x41524d36u \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0x14b0524bu \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/pointer_restore.map -o $@ $<
$(BUILD_DIR)/format_probe.elf: format_probe.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_MAILBOX_BASE=0x20002100 \
		-DKW_STACK_TOP=0x20002300 -nostdlib -Wl,-T,linker_mutation.ld \
		-Wl,--build-id=none -Wl,--gc-sections \
		-Wl,-Map,$(BUILD_DIR)/format_probe.map -o $@ $<
$(BUILD_DIR)/protection_roundtrip.elf: protection_roundtrip.c linker_restore.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -nostdlib -Wl,-T,linker_restore.ld \
		-Wl,--build-id=none -Wl,--gc-sections \
		-Wl,-Map,$(BUILD_DIR)/protection_roundtrip.map -o $@ $<
$(BUILD_DIR)/status_roundtrip.elf: status_roundtrip.c linker_restore.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -nostdlib -Wl,-T,linker_restore.ld \
		-Wl,--build-id=none -Wl,--gc-sections \
		-Wl,-Map,$(BUILD_DIR)/status_roundtrip.map -o $@ $<
$(BUILD_DIR)/%.elf: %.c linker.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(LDFLAGS) -Wl,-Map,$(BUILD_DIR)/$*.map -o $@ $<
$(BUILD_DIR)/%.bin: $(BUILD_DIR)/%.elf
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<
	sha256sum $@
inspect: $(ELFS)
	$(OBJDUMP) -h -d $(BUILD_DIR)/format_probe.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/restore_sector.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/pointer_probe.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/pointer_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/protection_roundtrip.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/status_roundtrip.elf
clean:
	rm -f $(ELFS) $(BINS) $(BUILD_DIR)/format_probe.map \
		$(BUILD_DIR)/restore_sector.map $(BUILD_DIR)/pointer_probe.map \
		$(BUILD_DIR)/pointer_restore.map \
		$(BUILD_DIR)/protection_roundtrip.map \
		$(BUILD_DIR)/status_roundtrip.map
