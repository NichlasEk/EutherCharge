BUILD := ../../build/kw520-board-probe
.PHONY: all
all:
	mkdir -p $(BUILD)
	arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -nostdlib -Wl,-T,linker.ld -Wl,--build-id=none -o $(BUILD)/probe.elf probe.S
	arm-none-eabi-objcopy -O binary $(BUILD)/probe.elf $(BUILD)/probe.bin
	arm-none-eabi-size $(BUILD)/probe.elf
	sha256sum $(BUILD)/probe.bin
