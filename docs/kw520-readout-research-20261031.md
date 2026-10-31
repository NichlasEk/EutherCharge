# Protected AT32F421 readout: public evidence, 2026-10-31

No live target access in this research step. User confirmed previous CSW-read trial left menu responsive.

## Exact MCU: published research

Schink et al., Unlock the Door to my Secrets, but don't Forget to Glitch, TCHES2024(2),88-129, DOI10.46586/tches.v2024.i2.88-129 explicitly studies AT32F421C8T7. Section7.1 reports no successful voltage-glitch parameters for that target. Section7.2 reports successful electromagnetic fault injection suppressing flash erasure, with high success rates in selected laboratory conditions. This is specialized fault-injection work, not a J-Link software-only unlock; an unsuccessful erase-suppression attempt can destroy the desired firmware.

Paper full text reviewed:
https://www.researchgate.net/publication/378949926_Unlock_the_Door_to_my_Secrets_but_don%27t_Forget_to_Glitch_A_comprehensive_analysis_of_flash_erase_suppression_attacks
Author context: https://blog.zapb.de/unlock-the-door-to-my-secrets-but-dont-forget-to-glitch-cccamp23/

## Exact MCU: updater-based extraction report

https://www.mikrocontroller.net/topic/558990

2023 RT-890/UV5118 radio discussion identifies AT32F421C8T7. Participants report protected-flash extraction using a modified updater/payload that outputs memory through UART; a bootloader attachment and firmware analysis are discussed. This is a firsthand project report, not independently reproduced here. It depends on that product's available update mechanism and images, neither established for KW520. Later live SWD debugging in the thread explicitly follows protection removal/erase and reflashing known images; it is not evidence of non-destructive SWD access to the protected original.

## Different MCU: public SWD race-condition proof of concept

https://github.com/racerxdl/stm32f0-pico-dump

Author targets STM32F0x level1 protection using RP2040-controlled reset and power plus precisely timed SWD reads. Other families are not validated there. It cannot be treated as a demonstrated AT32F421 solution, or applied through our present wiring without further work.

## Official tool boundary

https://kb.segger.com/ArteryTek_AT32

SEGGER states that unsecuring AT32 causes mass erase. Its supported-device/unlock functionality is not a protected firmware backup method.

## Implication for KW520

There is credible evidence the exact MCU's protection has been overcome, but no verified command-only J-Link method was found in this search. The radio's updater route is a relevant research direction only if a KW520-specific update path/image can be established. EMFI is a separate hardware project with original-data loss risk. No unlock, injection or foreign firmware was attempted.
