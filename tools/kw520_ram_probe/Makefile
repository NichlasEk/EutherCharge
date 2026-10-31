CROSS ?= arm-none-eabi-
BUILD_DIR ?= ../../build/kw520-ram-probe

CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size

ELF := $(BUILD_DIR)/probe.elf
BIN := $(BUILD_DIR)/probe.bin
MAP := $(BUILD_DIR)/probe.map

ASFLAGS := -mcpu=cortex-m4 -mthumb
LDFLAGS := -nostdlib -Wl,-T,linker.ld -Wl,--build-id=none \
	-Wl,--gc-sections -Wl,-Map,$(MAP)

.PHONY: all inspect clean

all: $(BIN)

$(BUILD_DIR):
	mkdir -p $@

$(ELF): probe.S linker.ld | $(BUILD_DIR)
	$(CC) $(ASFLAGS) $(LDFLAGS) -o $@ probe.S

$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<
	sha256sum $@

inspect: $(ELF)
	$(OBJDUMP) -h -d $<

clean:
	rm -f $(ELF) $(BIN) $(MAP)
