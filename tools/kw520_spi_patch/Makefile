CROSS ?= arm-none-eabi-
BUILD_DIR ?= ../../build/kw520-spi-patch
CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size
ELFS := $(BUILD_DIR)/format_probe.elf $(BUILD_DIR)/restore_sector.elf \
	$(BUILD_DIR)/length_probe.elf $(BUILD_DIR)/length_restore.elf \
	$(BUILD_DIR)/boundary_baseline.elf $(BUILD_DIR)/boundary_extend.elf \
	$(BUILD_DIR)/boundary_restore.elf \
	$(BUILD_DIR)/pointer_probe.elf $(BUILD_DIR)/pointer_restore.elf \
	$(BUILD_DIR)/crossbank_probe.elf $(BUILD_DIR)/crossbank_restore.elf \
	$(BUILD_DIR)/protection_roundtrip.elf \
	$(BUILD_DIR)/status_roundtrip.elf
BINS := $(BUILD_DIR)/format_probe.bin $(BUILD_DIR)/restore_sector.bin \
	$(BUILD_DIR)/length_probe.bin $(BUILD_DIR)/length_restore.bin \
	$(BUILD_DIR)/boundary_baseline.bin $(BUILD_DIR)/boundary_extend.bin \
	$(BUILD_DIR)/boundary_restore.bin \
	$(BUILD_DIR)/pointer_probe.bin $(BUILD_DIR)/pointer_restore.bin \
	$(BUILD_DIR)/crossbank_probe.bin $(BUILD_DIR)/crossbank_restore.bin \
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
$(BUILD_DIR)/crossbank_probe.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574342u -DKW_ARM_MAGIC=0x41524d37u \
		-DKW_BUFFER_CRC32=0xb29ee7d1u \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0xb29ee7d1u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/crossbank_probe.map -o $@ $<
$(BUILD_DIR)/crossbank_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574352u -DKW_ARM_MAGIC=0x41524d38u \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0xb29ee7d1u \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/crossbank_restore.map -o $@ $<
$(BUILD_DIR)/format_probe.elf: format_probe.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_MAILBOX_BASE=0x20002100 \
		-DKW_STACK_TOP=0x20002300 -nostdlib -Wl,-T,linker_mutation.ld \
		-Wl,--build-id=none -Wl,--gc-sections \
		-Wl,-Map,$(BUILD_DIR)/format_probe.map -o $@ $<
$(BUILD_DIR)/length_probe.elf: format_probe.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_MAILBOX_BASE=0x20002100 \
		-DKW_STACK_TOP=0x20002300 -DKW_HELPER_MAGIC=0x4b574c4eu \
		-DKW_ARM_MAGIC=0x41524d39u -DKW_PATCH_ADDRESS=0x00003892u \
		-DKW_EXPECTED_BEFORE=0x00000a00u -DKW_EXPECTED_AFTER=0x00000800u \
		-DKW_ORIGINAL_CRC32=0xf5c23372u -DKW_PATCHED_CRC32=0x5e1e3b15u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/length_probe.map -o $@ $<
$(BUILD_DIR)/length_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574c52u -DKW_ARM_MAGIC=0x41524d41u \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0x5e1e3b15u \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/length_restore.map -o $@ $<
$(BUILD_DIR)/boundary_baseline.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574253u -DKW_ARM_MAGIC=0x41524d42u \
		-DKW_BUFFER_CRC32=0xb461d992u \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0xb461d992u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_baseline.map -o $@ $<
$(BUILD_DIR)/boundary_extend.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574558u -DKW_ARM_MAGIC=0x41524d43u \
		-DKW_BUFFER_CRC32=0xe4e92a7bu \
		-DKW_EXPECTED_TARGET_CRC32=0xb461d992u \
		-DKW_EXPECTED_FINAL_CRC32=0xe4e92a7bu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_extend.map -o $@ $<
$(BUILD_DIR)/boundary_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574252u -DKW_ARM_MAGIC=0x41524d44u \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0xe4e92a7bu \
		-DKW_EXPECTED_TARGET_CRC32_ALT=0xb461d992u \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_restore.map -o $@ $<
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
	$(OBJDUMP) -h -d $(BUILD_DIR)/length_probe.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/length_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_baseline.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_extend.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/restore_sector.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/pointer_probe.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/pointer_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/crossbank_probe.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/crossbank_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/protection_roundtrip.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/status_roundtrip.elf
clean:
	rm -f $(ELFS) $(BINS) $(BUILD_DIR)/format_probe.map \
		$(BUILD_DIR)/length_probe.map $(BUILD_DIR)/length_restore.map \
		$(BUILD_DIR)/boundary_baseline.map $(BUILD_DIR)/boundary_extend.map \
		$(BUILD_DIR)/boundary_restore.map \
		$(BUILD_DIR)/restore_sector.map $(BUILD_DIR)/pointer_probe.map \
		$(BUILD_DIR)/pointer_restore.map \
		$(BUILD_DIR)/crossbank_probe.map $(BUILD_DIR)/crossbank_restore.map \
		$(BUILD_DIR)/protection_roundtrip.map \
		$(BUILD_DIR)/status_roundtrip.map
