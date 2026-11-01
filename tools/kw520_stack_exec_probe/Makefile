CROSS ?= arm-none-eabi-
CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size
BUILD_DIR ?= ../../build/kw520-stack-exec-probe

.PHONY: all inspect clean
all: $(BUILD_DIR)/stub.bin

$(BUILD_DIR):
	mkdir -p $@

$(BUILD_DIR)/stub.elf: stub.S linker.ld | $(BUILD_DIR)
	$(CC) -mcpu=cortex-m4 -mthumb -nostdlib -Wl,-T,linker.ld \
		-Wl,--build-id=none -o $@ $<

$(BUILD_DIR)/stub.bin: $(BUILD_DIR)/stub.elf
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<
	sha256sum $@

inspect: $(BUILD_DIR)/stub.elf
	$(OBJDUMP) -h -d $<

clean:
	rm -f $(BUILD_DIR)/stub.elf $(BUILD_DIR)/stub.bin
