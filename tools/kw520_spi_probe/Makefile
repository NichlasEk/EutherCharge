CROSS ?= arm-none-eabi-
BUILD_DIR ?= ../../build/kw520-spi-probe
CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size
ELF := $(BUILD_DIR)/spi_probe.elf
BIN := $(BUILD_DIR)/spi_probe.bin
MAP := $(BUILD_DIR)/spi_probe.map

.PHONY: all inspect clean
all: $(BIN)
$(BUILD_DIR):
	mkdir -p $@
$(ELF): spi_probe.S linker.ld | $(BUILD_DIR)
	$(CC) -mcpu=cortex-m4 -mthumb -nostdlib -Wl,-T,linker.ld \
		-Wl,--build-id=none -Wl,--gc-sections -Wl,-Map,$(MAP) -o $@ spi_probe.S
$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<
	sha256sum $@
inspect: $(ELF)
	$(OBJDUMP) -h -d $<
clean:
	rm -f $(ELF) $(BIN) $(MAP)
