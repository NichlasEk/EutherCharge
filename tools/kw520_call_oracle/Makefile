CROSS ?= arm-none-eabi-
BUILD_DIR ?= ../../build/kw520-call-oracle

CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size

ELF := $(BUILD_DIR)/oracle.elf
BIN := $(BUILD_DIR)/oracle.bin
MAP := $(BUILD_DIR)/oracle.map

ASFLAGS := -mcpu=cortex-m4 -mthumb
LDFLAGS := -nostdlib -Wl,-T,linker.ld -Wl,--build-id=none \
	-Wl,--gc-sections -Wl,-Map,$(MAP)

.PHONY: all inspect clean

all: $(BIN)

$(BUILD_DIR):
	mkdir -p $@

$(ELF): oracle.S linker.ld | $(BUILD_DIR)
	$(CC) $(ASFLAGS) $(LDFLAGS) -o $@ oracle.S

$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<
	sha256sum $@

inspect: $(ELF)
	$(OBJDUMP) -h -d $<

clean:
	rm -f $(ELF) $(BIN) $(MAP)
