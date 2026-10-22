# H-6CS / HC-XS6: TL866A readout workbench

2026-10-22. Separate target from the KW520 in HANDOFF.md.

## Current boundary

The MCU is NOT identified. No target or programmer was accessed or flashed.
USB inventory during development did not show a TL866. The local minipro
source is at `/home/nichlas/minipro`, but `minipro` is not on PATH in this
environment. A historical installation is not evidence of current availability.

`tools/h6cs_pdk.py` implements an experimental, offline-only OTP2_2 read
sequence for PMC131-S16A / PMS131-S16. It has **no USB/serial backend** and is
not a ready-to-use TL866 programmer. Simulation cannot establish electrical
safety, device identity, timing tolerance, or real firmware readout.

## Reproduce the software checks

```sh
python3 tools/h6cs_pdk.py status
python3 tools/h6cs_pdk.py trace --profile PMS131-S16 --count 8 --output /tmp/h6cs-read-trace.json
python3 -m unittest discover -s tests -p 'test_h6cs_pdk.py' -v
```

Trace output is explicitly labelled simulation and cannot overwrite an existing
file. Fake sample values are not exported as a firmware binary. `compare` accepts
three or more existing full 3072-byte LE16 captures, checks 14-bit word width,
compares all bytes and reports SHA-256 without displaying the contents. It rejects
path aliases and flags uniform data. Matching captures do not prove unlocked or
valid firmware; distinct files do not prove independently acquired measurements.

## Board evidence (user measurements, not independently measured)

- MCU SOP16: pin 1 +5 V, pin 16 ground; 2, 3, 5, 6, 7 externally unused.
- Pin 4 button; 8 LED; 9/10/11 LCD DATA/WR/CS candidates.
- Pin 12 RT11 network; pin 13 to edge connector via 62 kOhm.
- Pin 14 to connector via another 62 kOhm, capacitor, 10 kOhm and 0-ohm ground link.
- Pin 15 to connector via 1 kOhm, also C3. Exact branches remain unconfirmed.
- LCD corrected to **24 pins**. HGSEMI HT1621D 24-pin diagram matches pins
  10 CS, 11 WR, 12 DATA, 13 VSS, 14 VLCD, 15 VDD, 16 COM0. Pin 9 is SEG9, not RD.
- YFC4604-S16A, PFC460-S16, PMC131-S16A, PMS131-S16 and PMS163-S16A remain
  pin-compatible candidates, NOT confirmed identities or programming substitutes.

## Critical correction: upstream READ is not purely read-command-only

Reviewed EasyPDK commit `cdc40ae65f85c1ed93f304f5008c6b9b6c5c0043`:

- `fpdkicdata.c`: PMS131 / PMC131 share ID 0xC83, OTP2_2, 12-bit addresses,
  14-bit code, 0x600 words, read VDD=3 V and VPP=5 V.
- `Firmware/source/Src/fpdk.c`, `_FPDK_GetIDIC`: OTP2_2 identification sends
  **command 0x7 (WRITE)**, then clocks the response and exits before programming.
- `FPDK_ReadIC` calls that ID routine before reading an OTP device. Looking only
  at the host `read` switch missed this. Do not run upstream `probe` or `read`
  on the original on the assumption that neither emits a write command.
- Our workbench omits ID entirely and emits only frame 0x5A5A5A56, followed by
  12-bit addresses and 14-bit input words, MSB first. This omission requires
  validation on a known part; it is NOT an alternate identification method.
- OTP clock is PA3 (physical 13), command/address output PA4 (14), data input
  PA6 (3), VPP PA5 (4), VDD 1, GND 16. Do not confuse this with the MTP interface.
- Upstream entry: clock low, VPP then 100 us, VDD then 500 us; clock pulses have
  1 us requested high delay. A future backend must reproduce and measure timing,
  rail order and shutdown, including voltage decay and back-power paths.
- YFC4604/PFC460/PMS163 are absent from that EasyPDK device table.

## TL866A electrical blocker

Reviewed Open-TL866 commit `58f889638992d6a06a94e842fa8efa0a52c407a4`:

- `py/otl866/aclient.py` and `firmware/io.h` enumerate nominal VPP levels
  9.8, 12.6, 14.0, 16.6, 14.4, 17.1, 18.5, 21.2 V. No 5 V setting.
- VDD includes 3.0 and about 5.1 V but is a single shared selectable rail, not
  two independent outputs. Setting VDD to 5.1 V does not supply 3 V and 5 V
  independently. Digital pin levels must be verified separately.
- Consequently a stock board using these interfaces plus a passive adapter is
  NOT a verified way to supply the required independent rails.
- A switched, regulated external rail/interface might resolve this, or a
  dedicated EasyPDK board may be simpler. No external circuit has been validated.
  Do not use the 9.8 V setting as an approximation to 5 V.
- Open-TL866 replaces the programmer firmware and is incompatible with normal
  host software while installed. No firmware replacement was performed.
- No XC8 compiler was found here; no PIC firmware image was built.

## Adapter and next physical boundary

A passive SOP16 150-mil, 1.27-mm-pitch breakout is useful for preserving and
accessing the desoldered MCU. Mark original pin 1 and verify breakout continuity.
**Chip pin numbers above are not ZIF socket positions.** There is no approved
insertion position or wiring diagram yet. Leave the adapter out of the programmer.
Do not connect anything to a mains/battery-connected charger.

Next: choose and bench-validate the rail/interface hardware with no original chip,
verify levels and power-up/down behavior, then run the read-only sequence on a
known sacrificial PMC131/PMS131 containing a known image. Only after successful
validation can the original-target procedure be assessed. Keep dump files local
under `dumps/`; no unlock, erase, calibration or security writes.

## Sources and licensing

- https://github.com/free-pdk/easy-pdk-programmer-software/tree/cdc40ae65f85c1ed93f304f5008c6b9b6c5c0043
- https://github.com/JohnDMcMaster/open-tl866/tree/58f889638992d6a06a94e842fa8efa0a52c407a4
- https://www.padauk.com.cn/upload/doc/PMC131%20PMS131%20PMS130%20datasheet%20V107%28CN%29_20191226.pdf
- https://www.padauk.com.cn/upload/doc/YFC4604%20datasheet%20V000_CN_20240621..pdf
- https://atta.szlcsc.com/upload/public/pdf/source/20210707/C910857_72C1A9E8DEB3B11475F394DC4426CEB5.pdf

The read-protocol adaptation in `tools/h6cs_pdk.py` is GPL-3.0-or-later, based on
freepdk's firmware. See `tools/LICENSE-h6cs-pdk-GPL-3.0.txt`; this exception does
not relicense the rest of EutherCharge. Upstream source checkouts are temporary
research inputs, not vendored into this repository.

## Original firmware bench follow-up (2026-10-22)

TL866A 03.2.86 now confirmed over USB. Built local minipro 0.7.2 in
`/tmp/h6cs-minipro-check.BbSOkT` with `-std=gnu17` (modern GCC defaults break
its older callback declarations). Stock hardware self-test passed all VPP/VCC/GND
pin drivers and both overcurrent checks.

User measured empty socket with black probe on ZIF16: ZIF1 VCC = 4.47 V,
ZIF40 VPP = 9.8 V. Shutdown commands succeeded; physical decay was not reported.
These are unloaded measurements of the diagnostic routing, not all selectable
rails. Initial ambiguous 4.47/5.3 reading was superseded by this explicit repeat.

`tools/h6cs_socket_meter.c` preserves the limited stock-firmware diagnostic.
It links against minipro objects (all except main.o), uses fixed ZIF1/40/16,
checks TL866A and firmware 03.2.86, polls overcurrent and shuts down after 120s
or SIGTERM/SIGINT. USB failure can prevent shutdown; unplug USB in that case.
This is a GPL-3.0-or-later adaptation of minipro, not a chip reader. No CLI
arguments: prints instructions without USB access. `--empty-socket` uses the
original diagnostic; `--empty-socket --vcc-code-0` additionally sends D6 with
selector 1, value 0, and disconnects VPP from the socket. Code 0 voltage and
its interaction with D1 remain UNVERIFIED until measured. Software timeout is
not a hardware interlock. Only use the physical empty socket, no adapter/chip.

New source: https://gist.github.com/radiomanV/69ef14c704325bfa58339f2ae73a900f
The original investigator documents D6 selector 0=VPP, 1=VCC, 2/3=VIO, with
explicit uncertainty and cross-reset between VCC and VPP settings. Treat this
as a bench experiment, not a guaranteed programmable supply. Do not infer 5V
VPP support from discovery of a voltage-select command.

User measured VCC code 0 BEFORE routing: ZIF1-to-ZIF16 = 4.47 V, unchanged.
Reset/end sent successfully. This does not distinguish ignored D6 from D1
resetting the selection. Added --vcc-code-0-after-routing to change only the
ordering; VPP remains unmapped.

User measured VCC code 0 AFTER routing: ZIF1-to-ZIF16 = 3.1 V unloaded.
This confirms order-dependent voltage selection on this programmer/firmware;
it does not validate a loaded rail, programming protocol or MCU identity.
The run subsequently reported LIBUSB_ERROR_TIMEOUT on the D2 query send and
both shutdown sends (D0 and 04). Process exited with failure; shutdown is NOT
confirmed. User instructed to unplug USB and keep the original chip outside.
Resolve communication/cleanup reliability before further powered experiments.

After user unplugged/reconnected USB, ran --vcc-code-0-no-poll: identical
D0/D1/D6 selection, but no repeated D2 status/overcurrent queries, 45-second
hold, then D0/04 cleanup. Both shutdown sends succeeded and process exited 0.
This supports investigating the post-D6 D2 interaction, but one successful
run does not exclude a transient USB failure. Physical voltage during this run
and decay after shutdown are awaiting user measurement. No original chip used.

Repeat of the same no-poll test: user observed output apparently remaining on.
Log confirms USB timeouts on BOTH D0 and 04 shutdown sends; process exited 1.
User instructed to unplug USB immediately. Failure without any D2 polling
means D2 polling is not necessary to reproduce the failure; earlier suspicion
of polling alone is insufficient. D6 handling/USB state remains unresolved.
Do not repeat powered tests or connect the original chip until the command
handling has been reviewed. The 45-second timer only attempts shutdown and is
not a reliable power cutoff. The preceding successful sends never established
physical shutdown, because the user missed that measurement.

After next USB reconnection, three consecutive `minipro -V` information queries
succeeded (TL866A 03.2.86), with no socket activation commands. Kernel log
revealed repeated configuration-descriptor timeouts (-110) during enumeration
at 21:01 and 21:06, including failed enumeration and host port power-cycle
attempts, before device 38 finally enumerated. This broadens the investigation
beyond D6: USB transport/startup/power or programmer firmware state may be
involved. It does not prove a bad cable or rule out a D6 issue. Next discriminate
with another USB cable/direct port and information-only checks before any
powered socket tests.

## Software audit after shutdown failures (2026-10-22)

No USB or socket operations were performed during this audit. Compared the
helper against local minipro b7bfb1488688f34fd6093eadae537d5ae99ce16a and the
radiomanV bit-banging gist linked above.

| Command | Helper length | Evidence and limitation |
| --- | --- | --- |
| D0 reset | 10 | Matches gist and minipro hardware check. |
| D1 routing | 25 | Seven header bytes, count/OE, eight latch/value pairs; matches gist layout. Minipro hardware check uses 32-byte padded messages for fewer latches. Padding requirement is not established. |
| D6 voltage | 9 | Exactly matches the gist's seven-byte header plus selector/value. Gist explicitly calls this command unclear and reports VCC/VPP cross-reset. No response or timing contract is supplied. |
| D2 query | 18 | Matches minipro hardware check; gist and minipro get_zif_state use 10. Thus 18 alone is not evidence of a bug. Failure also reproduced with no D2. |
| 04 end | 4 | Matches hardware-check cleanup. Transport success does not establish physical shutdown. |

Confirmed helper defects and corrections:

- `msg_recv` hides the received byte count. A short successful USB transfer
  could leave `reply[1]` uninitialized/stale. Status reception now initializes
  the buffer, checks the transfer result and requires at least 47 bytes (seven
  header plus forty pin states). This does NOT explain the observed OUT timeout.
- `minipro_open` accepts bootloader mode as well as normal mode. Helper now
  requires normal mode before any pin commands.
- Replaced "OFF"/"Auto-off" wording with attempted shutdown and explicit
  unknown socket voltage; added command-stage, opcode, length and result logs.
- Both cleanup commands remain attempted even if the first fails. A host timer
  still cannot turn off hardware when USB is unresponsive.

Five hardware-free tests use a compiled fake transport (no libusb linkage),
covering rejected CLI arguments, bootloader rejection, short/error status,
overcurrent, failures at every no-poll send, cleanup attempts and the no-poll
command order. All passed. Real helper compiled with -Wall -Wextra -Werror;
the rebuilt binary was NOT run on hardware.

No root cause established: an unread D6 response, timing/padding requirements,
or firmware state are hypotheses, not findings. Kernel enumeration timeouts
are additional evidence of a broader startup/USB problem, not proof that D6 is
innocent or that the cable is defective. Next discriminating evidence should
be an information-only USB capture after cold reconnection, followed by review
of an exact-version firmware implementation or known-working D6 trace. Do not
resume original-chip work based on these software tests.

## Information-only USB capture (2026-10-22)

After user enabled usbmon and granted read access, captured usbmon2 with a
kernel capture filter `link[11] = 45` (USB device address 45). Saved locally
as `dumps/h6cs-usb/info-only.pcapng` (directory 0700, file 0600; contains device
identity bytes, do not publish). All 26 captured packets belong to address 45.
Five `minipro -V` queries identified TL866A 03.2.86 successfully. Each bulk OUT
payload was exactly five zero bytes (information opcode 00); each corresponding
IN returned 44 bytes successfully in 2.780–2.795 ms. All completed transfers
had status 0; -115 on submissions means pending, not a failed completion.
No D0/D1/D2/D6 or other socket commands were sent. Capture stopped with SIGINT;
zero capture drops reported. The requested duration did not promptly terminate
capture, so explicit process termination was used.

This establishes working information exchange in the current idle state only.
It does not reproduce or fix the intermittent enumeration/voltage-command
failure. A trace including the actual failing sequence or exact firmware
analysis is still needed to establish the cause; no such powered test was run.

## Authorized short voltage-sequence capture (2026-10-22)

User authorized empty-socket activation/capture without meter measurement.
Captured `dumps/h6cs-usb/voltage-sequence.pcapng` with the same device-only
filter; helper/capture logs saved beside it, private permissions. Ran rebuilt
helper in no-poll mode, sent SIGTERM at two seconds to trigger cleanup.
Trace confirms information opcode 00, D0 reset, D1 routing (25 bytes), D6
selector1/code0 (9 bytes), then D0/04 shutdown. All USB completions succeeded,
zero capture drops. D6 completed in 0.231 ms; shutdown D0/04 in 0.067/0.129 ms.
No receive was requested between D6 and cleanup; those OUT transfers still
succeeded in this run. Helper exited 0. This short run did NOT reproduce the
failure and does not rule out timing/intermittent faults or prove physical OFF.
No actual socket-voltage measurement was made and no original chip was used.
First follow-up information query did not identify the device (full output not
retained). Next query did identify it but exited 1 because it was run outside
the minipro directory and could not locate logicic.xml. Retried from the correct
directory: identification succeeded, exit 0. Do not conflate the database-path
error with a USB transport failure; initial inconclusive query remains noted.

## Attempted alternating-voltage capture (2026-10-22)

User authorized switching settings with USB capture and watching the yellow
indicator. Added --voltage-cycle: D0, then D1 baseline/D6 code0 twice with
one-second holds, then D0/04; VPP unmapped throughout. Six fake-transport tests
pass, including failure injection at all seven sends. Real helper compiles
without warnings. No-poll operation; timer is only a shutdown attempt.

Actual run FAILED BEFORE ANY PIN COMMAND: opening programmer timed out sending
the five-byte opcode-00 information request. Capture voltage-cycle.pcapng
contains that sole bulk OUT payload 0000000000; completion after 5.000119 s
has status -2 (host cancellation following libusb timeout). No D0/D1/D6 was
sent, so no voltage cycling occurred. Eight packets captured, zero drops.
This captures failure on a plain information request, but does not exclude a
persistent firmware state from the preceding run. Do not label it a proven
cable fault or a D6-specific fault. Logs remain local under dumps/h6cs-usb/.

## Captured alternating-sequence failure, device 50 (2026-10-22)

After reconnect, device 002/050 had user read/write access and an information
query identified TL866A 03.2.86, exit 0. User's previously authorized cycle test
then ran with device-filtered capture voltage-cycle-050.pcapng. Information,
D0, D1, D6, D1, D6 all completed successfully at USB transport level. Commands
were separated by about one second. The subsequent shutdown D0 and 04 each
timed out after five seconds (completion -2 following host cancellation).
Helper exited 1; user instructed to unplug USB immediately. No D2 polls ran.
This locates the observed loss of OUT responsiveness after the second accepted
D6 and before the next D0 completion. It does not prove exactly which command
or internal state caused it. Voltages and physical shutdown were not measured.
Do not repeat this sequence on an original chip or regard USB ACK as proof of
command execution. Raw trace and helper log are local/private in dumps/.

## D6 response discovery from public firmware disassembly (2026-10-22)

This review performed no hardware access. Sources inspected:

- Original bit-banging contribution: https://gitlab.com/DavidGriffith/minipro/-/merge_requests/213
  Its `tl866a_set_voltages` is a success-returning stub, not a working D6 reference.
- https://github.com/radiomanV/TL866/blob/1fd9c48b457aff72d5f1fa566fa2ffc79c742403/TL866_Updater/QT/firmwareA.bin
  Public 131072-byte image, SHA256
  `8aa8e74e39dcd7184a5da08d772c49284c6f11249edb819ea312fa06f2d9591d`.
  File history last change 2018-07-25; NOT established as installed 03.2.86.
- Open-TL866 `firmware/io.c` at 58f889638992d6a06a94e842fa8efa0a52c407a4:
  vdd_val/vpp_val set hardware selector bits and delay 2 ms. This is replacement
  firmware, not an implementation of the stock D6 protocol.

Disassembled the public image locally with gpdasm 1.5.2, processor 18f87j50.
Inputs/output are in `/tmp/h6cs-protocol-review/`; no firmware was installed.
Byte-address evidence (not source line numbers):

1. Dispatcher loads incoming opcode from RAM 0x470 at 0x9854. Following the
   cumulative XOR comparisons, opcode D6 branches at 0x98de to 0x9ab2.
2. At 0x9ab2, it copies fault/status RAM 0x4b9 into reply byte 1 (0x431),
   calls the voltage handler 0x100f6 with pointer 0x477 (request byte 7), and
   at 0x9ac6–0x9ac8 sets reply length RAM 0x24 to **7**.
3. Common epilogue 0xa06a tests reply length. At 0xa07e–0xa090 it tests bit 7
   of the previous IN-transfer descriptor through RAM 0x4f2/0x4f3, looping at
   0xa0bc while busy. It then submits the reply buffer at 0x430 with endpoint
   1/direction 1 via 0xd45c. Incoming opcode had been copied into 0x430 at
   0x9846, so the expected reply begins D6.

This is concrete evidence for a seven-byte D6 response in that public firmware,
and strongly supports an unread-response explanation of our trace: first D6
queues a reply; second D6 may wait for it to be consumed, preventing subsequent
OUT processing. Exact correspondence with 03.2.86 and actual physical repair
are still unverified. Earlier blanket suspicion of D2 polling was insufficient;
the helper itself omitted a response read required by this firmware path.

Fixed every D6 path to perform a bounded endpoint-0x81 read immediately after
the OUT transfer (64-byte buffer to accommodate the USB packet), require an
actual seven-byte reply, check opcode D6 and reject nonzero status. Timeouts,
short/wrong replies and reported faults stop the sequence and attempt cleanup.
Seven simulated transport tests pass, including D6 reply failures and two reads
in a two-D6 cycle. Built real helper with -Wall -Wextra -Werror; NOT run on
hardware after this fix. Next bench test: the same empty-socket cycle with USB
capture, checking both seven-byte IN replies and subsequent shutdown transfers.

User also has a GQ-4x4. Keep as a possible fallback; support for these Padauk
candidates and a suitable low-level interface have not been verified.

## Corrected D6 cycle verified over USB, device 53 (2026-10-22)

User indicated programmer ready; repeated the same empty-socket four-step
cycle using corrected D6 receive handling. Private capture:
`dumps/h6cs-usb/voltage-cycle-fixed-053.pcapng` and accompanying helper log.
Both D6 responses were exactly `d6 00 00 00 56 02 01`, seven bytes, status zero.
All USB completions succeeded, including subsequent D1, D6 and shutdown D0/04.
Helper exited 0; a separate post-test information query also identified TL866A
03.2.86 and exited 0. This verifies the seven-byte response on the installed
firmware and successful operation of the fix in one previously failing cycle.
Physical voltage levels/off-state were not measured; yellow-indicator report
is pending. This is not MCU identification or validation of the read protocol.
