CROSS ?= arm-none-eabi-
BUILD_DIR ?= ../../build/kw520-spi-patch
CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size
FRONTIER_ALLOCATIONS := 256 320 384 448 480 512
FRONTIER_CRC_256 := 0x28017863
FRONTIER_CRC_320 := 0x41b76a28
FRONTIER_CRC_384 := 0x52fdfc69
FRONTIER_CRC_448 := 0x7cfe1846
FRONTIER_CRC_480 := 0xebdaf776
FRONTIER_CRC_512 := 0x72628a3a
FRONTIER_ELFS := $(foreach allocation,$(FRONTIER_ALLOCATIONS),$(BUILD_DIR)/frontier$(allocation)_data_install.elf $(BUILD_DIR)/frontier$(allocation)_data_restore.elf)
FRONTIER_BINS := $(FRONTIER_ELFS:.elf=.bin)
ELFS := $(BUILD_DIR)/format_probe.elf $(BUILD_DIR)/restore_sector.elf \
	$(BUILD_DIR)/length_probe.elf $(BUILD_DIR)/length_restore.elf \
	$(BUILD_DIR)/boundary_baseline.elf $(BUILD_DIR)/boundary_extend.elf \
	$(BUILD_DIR)/boundary_restore.elf \
	$(BUILD_DIR)/maxrecord_probe.elf $(BUILD_DIR)/maxrecord_restore.elf \
	$(BUILD_DIR)/overmax_data_install.elf $(BUILD_DIR)/overmax_data_restore.elf \
	$(BUILD_DIR)/overmax_pointer_install.elf $(BUILD_DIR)/overmax_pointer_restore.elf \
	$(BUILD_DIR)/boundary128_data_install.elf $(BUILD_DIR)/boundary128_data_restore.elf \
	$(BUILD_DIR)/boundary128_pointer_restore_retry.elf \
	$(BUILD_DIR)/boundary160_data_install.elf $(BUILD_DIR)/boundary_pointer_install_retry.elf \
	$(BUILD_DIR)/boundary192_data_install.elf \
	$(BUILD_DIR)/boundary224_data_install.elf \
	$(BUILD_DIR)/boundary_data_audit.elf \
	$(BUILD_DIR)/boundary224_data_install_erased.elf \
	$(BUILD_DIR)/boundary240_data_install.elf \
	$(BUILD_DIR)/boundary240_data_restore.elf \
	$(BUILD_DIR)/boundary_pointer_audit.elf \
	$(BUILD_DIR)/boundary_pointer_bitbang_audit.elf \
	$(BUILD_DIR)/boundary_pointer_interrupted_audit.elf \
	$(BUILD_DIR)/boundary_pointer_interrupted_restore.elf \
	$(BUILD_DIR)/boundary_pointer_bitbang_restore.elf \
	$(BUILD_DIR)/frontier_pointer_bitbang_restore.elf \
	$(BUILD_DIR)/language9_install.elf $(BUILD_DIR)/language9_restore.elf \
	$(BUILD_DIR)/language9_list_install.elf $(BUILD_DIR)/language9_list_restore.elf \
	$(BUILD_DIR)/nulcopy_data_install.elf $(BUILD_DIR)/nulcopy_data_restore.elf \
	$(BUILD_DIR)/stack_exec_data_install.elf $(BUILD_DIR)/stack_exec_data_restore.elf \
	$(BUILD_DIR)/pointer_probe.elf $(BUILD_DIR)/pointer_restore.elf \
	$(BUILD_DIR)/crossbank_probe.elf $(BUILD_DIR)/crossbank_restore.elf \
	$(BUILD_DIR)/protection_roundtrip.elf \
	$(BUILD_DIR)/status_roundtrip.elf
BINS := $(BUILD_DIR)/format_probe.bin $(BUILD_DIR)/restore_sector.bin \
	$(BUILD_DIR)/length_probe.bin $(BUILD_DIR)/length_restore.bin \
	$(BUILD_DIR)/boundary_baseline.bin $(BUILD_DIR)/boundary_extend.bin \
	$(BUILD_DIR)/boundary_restore.bin \
	$(BUILD_DIR)/maxrecord_probe.bin $(BUILD_DIR)/maxrecord_restore.bin \
	$(BUILD_DIR)/overmax_data_install.bin $(BUILD_DIR)/overmax_data_restore.bin \
	$(BUILD_DIR)/overmax_pointer_install.bin $(BUILD_DIR)/overmax_pointer_restore.bin \
	$(BUILD_DIR)/boundary128_data_install.bin $(BUILD_DIR)/boundary128_data_restore.bin \
	$(BUILD_DIR)/boundary128_pointer_restore_retry.bin \
	$(BUILD_DIR)/boundary160_data_install.bin $(BUILD_DIR)/boundary_pointer_install_retry.bin \
	$(BUILD_DIR)/boundary192_data_install.bin \
	$(BUILD_DIR)/boundary224_data_install.bin \
	$(BUILD_DIR)/boundary_data_audit.bin \
	$(BUILD_DIR)/boundary224_data_install_erased.bin \
	$(BUILD_DIR)/boundary240_data_install.bin \
	$(BUILD_DIR)/boundary240_data_restore.bin \
	$(BUILD_DIR)/boundary_pointer_audit.bin \
	$(BUILD_DIR)/boundary_pointer_bitbang_audit.bin \
	$(BUILD_DIR)/boundary_pointer_interrupted_audit.bin \
	$(BUILD_DIR)/boundary_pointer_interrupted_restore.bin \
	$(BUILD_DIR)/boundary_pointer_bitbang_restore.bin \
	$(BUILD_DIR)/frontier_pointer_bitbang_restore.bin \
	$(BUILD_DIR)/language9_install.bin $(BUILD_DIR)/language9_restore.bin \
	$(BUILD_DIR)/language9_list_install.bin $(BUILD_DIR)/language9_list_restore.bin \
	$(BUILD_DIR)/nulcopy_data_install.bin $(BUILD_DIR)/nulcopy_data_restore.bin \
	$(BUILD_DIR)/stack_exec_data_install.bin $(BUILD_DIR)/stack_exec_data_restore.bin \
	$(BUILD_DIR)/pointer_probe.bin $(BUILD_DIR)/pointer_restore.bin \
	$(BUILD_DIR)/crossbank_probe.bin $(BUILD_DIR)/crossbank_restore.bin \
	$(BUILD_DIR)/protection_roundtrip.bin \
	$(BUILD_DIR)/status_roundtrip.bin
ELFS += $(FRONTIER_ELFS)
BINS += $(FRONTIER_BINS)

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
$(BUILD_DIR)/maxrecord_probe.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574d50u -DKW_ARM_MAGIC=0x41524d45u \
		-DKW_BUFFER_CRC32=0xde37c157u \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0xde37c157u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/maxrecord_probe.map -o $@ $<
$(BUILD_DIR)/maxrecord_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574d52u -DKW_ARM_MAGIC=0x41524d46u \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0xde37c157u \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/maxrecord_restore.map -o $@ $<
$(BUILD_DIR)/overmax_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574449u -DKW_ARM_MAGIC=0x41524d47u \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0x6417ecbdu \
		-DKW_EXPECTED_TARGET_CRC32=0xf154670au \
		-DKW_EXPECTED_FINAL_CRC32=0x6417ecbdu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/overmax_data_install.map -o $@ $<
$(BUILD_DIR)/overmax_data_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574452u -DKW_ARM_MAGIC=0x41524d48u \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0xf154670au \
		-DKW_EXPECTED_TARGET_CRC32=0x6417ecbdu \
		-DKW_EXPECTED_FINAL_CRC32=0xf154670au \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/overmax_data_restore.map -o $@ $<
$(BUILD_DIR)/overmax_pointer_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574f50u -DKW_ARM_MAGIC=0x41524d49u \
		-DKW_BUFFER_CRC32=0x6f68933fu \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0x6f68933fu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/overmax_pointer_install.map -o $@ $<
$(BUILD_DIR)/overmax_pointer_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574f52u -DKW_ARM_MAGIC=0x41524d4au \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0x6f68933fu \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/overmax_pointer_restore.map -o $@ $<
$(BUILD_DIR)/boundary128_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b573849u -DKW_ARM_MAGIC=0x41524d4bu \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0x1f18aa83u \
		-DKW_EXPECTED_TARGET_CRC32=0xf154670au \
		-DKW_EXPECTED_FINAL_CRC32=0x1f18aa83u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary128_data_install.map -o $@ $<
$(BUILD_DIR)/boundary128_data_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b573852u -DKW_ARM_MAGIC=0x41524d4cu \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0xf154670au \
		-DKW_EXPECTED_TARGET_CRC32=0x1f18aa83u \
		-DKW_EXPECTED_FINAL_CRC32=0xf154670au \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary128_data_restore.map -o $@ $<
$(BUILD_DIR)/boundary128_pointer_restore_retry.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b575852u -DKW_ARM_MAGIC=0x41524d4du \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0x6f68933fu \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary128_pointer_restore_retry.map -o $@ $<
$(BUILD_DIR)/boundary160_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b573649u -DKW_ARM_MAGIC=0x41524d4eu \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_SECTOR_ADDRESS=0x0000c000u \
		-DKW_BUFFER_CRC32=0x0c91e3d5u -DKW_EXPECTED_TARGET_CRC32=0x1f18aa83u \
		-DKW_EXPECTED_FINAL_CRC32=0x0c91e3d5u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary160_data_install.map -o $@ $<
$(BUILD_DIR)/boundary_pointer_install_retry.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b575849u -DKW_ARM_MAGIC=0x41524d4fu \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_BUFFER_CRC32=0x6f68933fu \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0x6f68933fu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_pointer_install_retry.map -o $@ $<
$(BUILD_DIR)/boundary192_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b573749u -DKW_ARM_MAGIC=0x41524d50u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_SECTOR_ADDRESS=0x0000c000u \
		-DKW_BUFFER_CRC32=0x80fff2a8u -DKW_EXPECTED_TARGET_CRC32=0x0c91e3d5u \
		-DKW_EXPECTED_FINAL_CRC32=0x80fff2a8u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary192_data_install.map -o $@ $<
$(BUILD_DIR)/boundary224_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574149u -DKW_ARM_MAGIC=0x41524d51u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_SECTOR_ADDRESS=0x0000c000u \
		-DKW_BUFFER_CRC32=0xff988d5cu -DKW_EXPECTED_TARGET_CRC32=0x80fff2a8u \
		-DKW_EXPECTED_FINAL_CRC32=0xff988d5cu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary224_data_install.map -o $@ $<
$(BUILD_DIR)/boundary_data_audit.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574144u -DKW_ARM_MAGIC=0x41524d52u \
		-DKW_AUDIT_ONLY=1 -DKW_SECTOR_ADDRESS=0x0000c000u \
		-DKW_BUFFER_CRC32=0x80fff2a8u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_data_audit.map -o $@ $<
$(BUILD_DIR)/boundary224_data_install_erased.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574145u -DKW_ARM_MAGIC=0x41524d53u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_SECTOR_ADDRESS=0x0000c000u \
		-DKW_BUFFER_CRC32=0xff988d5cu -DKW_EXPECTED_TARGET_CRC32=0xf154670au \
		-DKW_EXPECTED_FINAL_CRC32=0xff988d5cu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary224_data_install_erased.map -o $@ $<
$(BUILD_DIR)/boundary240_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574249u -DKW_ARM_MAGIC=0x41524d54u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0xaba2265eu \
		-DKW_EXPECTED_TARGET_CRC32=0xff988d5cu \
		-DKW_EXPECTED_FINAL_CRC32=0xaba2265eu \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary240_data_install.map -o $@ $<
$(BUILD_DIR)/boundary240_data_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574346u -DKW_ARM_MAGIC=0x41524d55u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0xf154670au \
		-DKW_EXPECTED_TARGET_CRC32=0xaba2265eu \
		-DKW_EXPECTED_FINAL_CRC32=0xf154670au \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary240_data_restore.map -o $@ $<
$(BUILD_DIR)/boundary_pointer_audit.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b575041u -DKW_ARM_MAGIC=0x41524d56u \
		-DKW_AUDIT_ONLY=1 -DKW_BUFFER_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_pointer_audit.map -o $@ $<
$(BUILD_DIR)/boundary_pointer_bitbang_audit.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574241u -DKW_ARM_MAGIC=0x41524d57u \
		-DKW_AUDIT_ONLY=1 -DKW_BITBANG_SPI=1 -DKW_BUFFER_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_pointer_bitbang_audit.map -o $@ $<
$(BUILD_DIR)/boundary_pointer_interrupted_audit.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574249u -DKW_ARM_MAGIC=0x41524d59u \
		-DKW_AUDIT_ONLY=1 -DKW_BITBANG_SPI=1 -DKW_EXPECTED_STATUS_BEFORE=0x02u \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_pointer_interrupted_audit.map -o $@ $<
$(BUILD_DIR)/boundary_pointer_interrupted_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574952u -DKW_ARM_MAGIC=0x41524d5au \
		-DKW_BITBANG_SPI=1 -DKW_STATUS_ALREADY_CLEAR=1 -DKW_STRICT_MUTATION_WAIT=1 \
		-DKW_EXPECTED_STATUS_BEFORE=0x02u -DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0x559db759u -DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_pointer_interrupted_restore.map -o $@ $<
$(BUILD_DIR)/boundary_pointer_bitbang_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574252u -DKW_ARM_MAGIC=0x41524d58u \
		-DKW_BITBANG_SPI=1 -DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-DKW_BUFFER_CRC32=0xf5c23372u -DKW_EXPECTED_TARGET_CRC32=0x33e293e2u \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/boundary_pointer_bitbang_restore.map -o $@ $<
$(BUILD_DIR)/frontier_pointer_bitbang_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574652u -DKW_ARM_MAGIC=0x41524d5bu \
		-DKW_BITBANG_SPI=1 -DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-DKW_BUFFER_CRC32=0xf5c23372u -DKW_EXPECTED_TARGET_CRC32=0x6f68933fu \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/frontier_pointer_bitbang_restore.map -o $@ $<

$(BUILD_DIR)/language9_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574e49u -DKW_ARM_MAGIC=0x41524d5cu \
		-DKW_BUFFER_CRC32=0xfa2d76bbu \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0xfa2d76bbu \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/language9_install.map -o $@ $<

$(BUILD_DIR)/language9_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574e52u -DKW_ARM_MAGIC=0x41524d5du \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0xfa2d76bbu \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/language9_restore.map -o $@ $<

$(BUILD_DIR)/language9_list_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574c49u -DKW_ARM_MAGIC=0x41524d5eu \
		-DKW_BUFFER_CRC32=0x4779b7f4u \
		-DKW_EXPECTED_TARGET_CRC32=0xf5c23372u \
		-DKW_EXPECTED_FINAL_CRC32=0x4779b7f4u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/language9_list_install.map -o $@ $<

$(BUILD_DIR)/language9_list_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574c52u -DKW_ARM_MAGIC=0x41524d5fu \
		-DKW_BUFFER_CRC32=0xf5c23372u \
		-DKW_EXPECTED_TARGET_CRC32=0x4779b7f4u \
		-DKW_EXPECTED_FINAL_CRC32=0xf5c23372u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/language9_list_restore.map -o $@ $<

$(BUILD_DIR)/nulcopy_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574e44u -DKW_ARM_MAGIC=0x41524d60u \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0x733066b3u \
		-DKW_EXPECTED_TARGET_CRC32=0xf154670au \
		-DKW_EXPECTED_FINAL_CRC32=0x733066b3u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/nulcopy_data_install.map -o $@ $<

$(BUILD_DIR)/nulcopy_data_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b575a52u -DKW_ARM_MAGIC=0x41524d61u \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0xf154670au \
		-DKW_EXPECTED_TARGET_CRC32=0x733066b3u \
		-DKW_EXPECTED_FINAL_CRC32=0xf154670au \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/nulcopy_data_restore.map -o $@ $<

$(BUILD_DIR)/stack_exec_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574549u -DKW_ARM_MAGIC=0x41524d62u \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0x041ae9b0u \
		-DKW_EXPECTED_TARGET_CRC32=0xf154670au \
		-DKW_EXPECTED_FINAL_CRC32=0x041ae9b0u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/stack_exec_data_install.map -o $@ $<

$(BUILD_DIR)/stack_exec_data_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b574552u -DKW_ARM_MAGIC=0x41524d63u \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0xf154670au \
		-DKW_EXPECTED_TARGET_CRC32=0x041ae9b0u \
		-DKW_EXPECTED_FINAL_CRC32=0xf154670au \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$(BUILD_DIR)/stack_exec_data_restore.map -o $@ $<

define FRONTIER_RULES
$(BUILD_DIR)/frontier$(1)_data_install.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$$(CC) $$(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b46$(shell printf '%04x' $(1))u -DKW_ARM_MAGIC=0x4149$(shell printf '%04x' $(1))u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=$$(FRONTIER_CRC_$(1))u \
		-DKW_EXPECTED_TARGET_CRC32=0xf154670au -DKW_EXPECTED_FINAL_CRC32=$$(FRONTIER_CRC_$(1))u \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$$(BUILD_DIR)/frontier$(1)_data_install.map -o $$@ $$<
$(BUILD_DIR)/frontier$(1)_data_restore.elf: restore_sector.c linker_mutation.ld | $(BUILD_DIR)
	$$(CC) $$(CFLAGS) -Oz -DKW_RESTORE_BUFFER=0x20000a00 \
		-DKW_MAILBOX_BASE=0x20002100 -DKW_STACK_TOP=0x20002300 \
		-DKW_HELPER_MAGIC=0x4b52$(shell printf '%04x' $(1))u -DKW_ARM_MAGIC=0x4152$(shell printf '%04x' $(1))u \
		-DKW_STATUS_CLEAR_ATTEMPTS=2u -DKW_STRICT_MUTATION_WAIT=1 \
		-DKW_SECTOR_ADDRESS=0x0000c000u -DKW_BUFFER_CRC32=0xf154670au \
		-DKW_EXPECTED_TARGET_CRC32=$$(FRONTIER_CRC_$(1))u -DKW_EXPECTED_FINAL_CRC32=0xf154670au \
		-nostdlib -Wl,-T,linker_mutation.ld -Wl,--build-id=none \
		-Wl,--gc-sections -Wl,-Map,$$(BUILD_DIR)/frontier$(1)_data_restore.map -o $$@ $$<
endef
$(foreach allocation,$(FRONTIER_ALLOCATIONS),$(eval $(call FRONTIER_RULES,$(allocation))))
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
	$(OBJDUMP) -h -d $(BUILD_DIR)/maxrecord_probe.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/maxrecord_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/overmax_data_install.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/overmax_data_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/overmax_pointer_install.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/overmax_pointer_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary128_data_install.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary128_data_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary128_pointer_restore_retry.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary160_data_install.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_pointer_install_retry.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary192_data_install.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary224_data_install.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_data_audit.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary224_data_install_erased.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary240_data_install.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary240_data_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_pointer_audit.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_pointer_bitbang_audit.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_pointer_interrupted_audit.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_pointer_interrupted_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/boundary_pointer_bitbang_restore.elf
	$(OBJDUMP) -h -d $(BUILD_DIR)/frontier_pointer_bitbang_restore.elf
	$(foreach elf,$(FRONTIER_ELFS),$(OBJDUMP) -h -d $(elf);)
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
		$(BUILD_DIR)/maxrecord_probe.map $(BUILD_DIR)/maxrecord_restore.map \
		$(BUILD_DIR)/overmax_data_install.map $(BUILD_DIR)/overmax_data_restore.map \
		$(BUILD_DIR)/overmax_pointer_install.map $(BUILD_DIR)/overmax_pointer_restore.map \
		$(BUILD_DIR)/boundary128_data_install.map $(BUILD_DIR)/boundary128_data_restore.map \
		$(BUILD_DIR)/boundary128_pointer_restore_retry.map \
		$(BUILD_DIR)/boundary160_data_install.map $(BUILD_DIR)/boundary_pointer_install_retry.map \
		$(BUILD_DIR)/boundary192_data_install.map \
		$(BUILD_DIR)/boundary224_data_install.map \
		$(BUILD_DIR)/boundary_data_audit.map \
		$(BUILD_DIR)/boundary224_data_install_erased.map \
		$(BUILD_DIR)/boundary240_data_install.map \
		$(BUILD_DIR)/boundary240_data_restore.map \
		$(BUILD_DIR)/boundary_pointer_audit.map \
		$(BUILD_DIR)/boundary_pointer_bitbang_audit.map \
		$(BUILD_DIR)/boundary_pointer_interrupted_audit.map \
		$(BUILD_DIR)/boundary_pointer_interrupted_restore.map \
		$(BUILD_DIR)/boundary_pointer_bitbang_restore.map \
		$(BUILD_DIR)/frontier_pointer_bitbang_restore.map \
		$(foreach allocation,$(FRONTIER_ALLOCATIONS),$(BUILD_DIR)/frontier$(allocation)_data_install.map $(BUILD_DIR)/frontier$(allocation)_data_restore.map) \
		$(BUILD_DIR)/restore_sector.map $(BUILD_DIR)/pointer_probe.map \
		$(BUILD_DIR)/pointer_restore.map \
		$(BUILD_DIR)/crossbank_probe.map $(BUILD_DIR)/crossbank_restore.map \
		$(BUILD_DIR)/protection_roundtrip.map \
		$(BUILD_DIR)/status_roundtrip.map
