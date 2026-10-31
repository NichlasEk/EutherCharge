CROSS ?= arm-none-eabi-
BUILD_DIR ?= ../../build/kw520-spi-probe
CC := $(CROSS)gcc
OBJCOPY := $(CROSS)objcopy
OBJDUMP := $(CROSS)objdump
SIZE := $(CROSS)size
ELF := $(BUILD_DIR)/spi_probe.elf
BIN := $(BUILD_DIR)/spi_probe.bin
MAP := $(BUILD_DIR)/spi_probe.map
SECTOR_ELF := $(BUILD_DIR)/sector_probe.elf
SECTOR_BIN := $(BUILD_DIR)/sector_probe.bin
SECTOR_MAP := $(BUILD_DIR)/sector_probe.map

.PHONY: all inspect clean
all: $(BIN) $(SECTOR_BIN)
$(BUILD_DIR):
	mkdir -p $@
$(ELF): spi_probe.S linker.ld | $(BUILD_DIR)
	$(CC) -mcpu=cortex-m4 -mthumb -nostdlib -Wl,-T,linker.ld \
		-Wl,--build-id=none -Wl,--gc-sections -Wl,-Map,$(MAP) -o $@ spi_probe.S
$(BIN): $(ELF)
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<
	sha256sum $@

$(SECTOR_ELF): spi_probe.S linker_sector.ld | $(BUILD_DIR)
	$(CC) -mcpu=cortex-m4 -mthumb -nostdlib \
		-DKW_MAILBOX=0x20001f00 -DKW_READ_BUFFER=0x20000a00 \
		-DKW_STACK_TOP=0x20002300 -Wl,-T,linker_sector.ld \
		-Wl,--build-id=none -Wl,--gc-sections -Wl,-Map,$(SECTOR_MAP) -o $@ spi_probe.S
$(SECTOR_BIN): $(SECTOR_ELF)
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<
	sha256sum $@
inspect: $(ELF) $(SECTOR_ELF)
	$(OBJDUMP) -h -d $<
clean:
	rm -f $(ELF) $(BIN) $(MAP) $(SECTOR_ELF) $(SECTOR_BIN) $(SECTOR_MAP)
