# Latest — KW520 access/EMFI work paused, 2026-11-02

User explicitly paused this part until purchased equipment arrives:
Faulty Cat V2.1 (PicoEMP-based EMFI, from Neven in Czechia) and
AT-START-F421 V1.2 with AT32F421C8T7. First practice with own firmware on
the development board and verify the entire flash is preserved after erase
suppression; then consider applying the findings to the charger.
Read [the pause and EMFI plan](docs/kw520-emfi-plan-paus-20261102.md) before
resuming. Verify actual hardware/installed firmware before selecting software
or wiring. User-supplied research lead: CHES/TCHES 2024, “Unlock the Door
to my Secrets, but don’t Forget to Glitch”, CVE-2024-21740.
No automatic hardware attempts during this pause. Other project work is not
automatically paused. User confirmed responsive UI after the final CSW test
below; no subsequent full power cycle is confirmed. The pause plan, ADC/CSW
probe changes and host tests are included in the checkpoint carrying this update.
Older uncommitted/pending statements below describe their historical snapshots.

# Earlier — isolated KW520 logic board, 2026-11-02

Newest result after full power cycle: clean initial DP status=0 at 3.300 V.
System-only setup passed. Reviewed CSW helper wrote 00000002 (ACK=1), then
immediately read DP status=c0000060 versus prior c0000040: new STICKYERR.
Stopped before further AP operations; restore deliberately skipped. Exit 1,
USB closed; no RAM/flash access or debug-power request. This is a fresh error
following the write, not just stale state. UI confirmation pending; power-cycle
both logic supply and J-Link USB before any further hardware attempt.

Latest live attempt: precheck returned VTref=3290 mV, valid DPIDR, but initial
DP CTRL/STAT=c0000020 (system request/ack + STICKYERR). Clean-state gate
stopped before any write. Revised CSW helper was NOT run. No retry/clear.
Ask for both logic supply off and J-Link USB disconnected before the next
fresh baseline, to avoid retained debug state/backfeed. UI status not checked.

Update after the failure below: user cold-started and confirmed responsive UI.
Host-only review fixed unsafe AP cleanup after FAULT and misleading restore
logging; added post-write DP status check and failure on CSW SIZE mismatch.
Mock fault-path tests pass; new binary `raw-csw-systemonly-reviewed` has only
been dry-run, NOT executed on hardware. See probe README's host review section.
No new hardware connection during review; system-only precondition must be
re-established before another experiment. First FAULT cause remains unresolved.

Power board disconnected. User reports bench supply 3.30 V, 0.10 A limit,
0.04 A draw and normal UI; raw DPIDR read left UI responsive. System-only
AP ID/CSW reads returned zero. New `firmware/kw520-probe/raw-csw-systemonly.c`
tested AP0 CSW SIZE=2 without debug power or any target-memory access.
At VTref=3.290 V the write got ACK=1; next read FAULT/ACK=4; attempted restore
got invalid ACK=7. Restoration NOT verified. Helper exited 1, USB closed.
Stop retries; cold-cycle logic board before another attempt. UI recovery not
yet confirmed. See firmware/kw520-probe/README.md for exact results.
Source and these notes are uncommitted. No RAM/flash read/write was attempted
by this helper and no reset/debug-power request was issued.

# Earlier — KW520 button mapping and ADC probe, 2026-11-01

Resume from [KW520 probe handoff](docs/kw520-probe-handoff-20261101.md).
All five buttons are confirmed. RAM probe/button inventory commit `6bc7003`
was pushed; subsequent ADC capture work and this handoff remain uncommitted.
Latest same-session clamp capture failed the live-state gate; no ADC data was
read. User was asked to separate clamps and cold-start, not yet confirmed.
No openocd/JLinkExe process was found at handoff. Do not repeat the failed
attachment blindly or treat ADC correlations as a mapped protection input.
Original internal firmware is still not backed up; no flash unlock/erase done.

# Earlier — user-authorized C6 probe flash, 2026-10-27

User confirmed empty XIAO ESP32-C6 and explicitly requested probe installation
without backup. Live ESP32-C6FH4 rev0.2,4MB on /dev/ttyACM0; no secure boot or
flash encryption. Wrote probe bootloader0x0, partition0x8000, app0x10000.
Esptool write hashes verified; separate app+partition verify_flash passed.
App SHA256 b29ff0e34ddab12c1bb97d6da1c570af74a2ec289f66d2a9e5ebe23d3fe3f83b.
Reset to boot after write. Serial confirms ESP-IDF boot, app loaded0x10000 and
Wi-Fi PHY initialization; no panic seen in10s capture. Network/API still untested.
Host has no Wi-Fi adapter. Next: phone imports
build/h6cs-probe-private/pairing.json and tests setup SSID / provisioning.
Report artifacts/probe-bench/flash-report.json. No ADC/output control enabled;
no charger electrical qualification. Previous no-flash notes below are historical.

# Latest — EutherCharge Apps card published, 2026-10-27

Published exact tested 0.1.0-probe debug APK to EutherOxide on192.168.32.186.
Server checkout /home/nichlas/EutherOxide is authoritative. Added Apps card and
exact allowlisted APK route; built npm UI and release host, restarted eutherhost.
LAN32162 and https://apothictech.se/downloads/EutherCharge-0.1.0-probe-debug.apk
both fetched in full:26368966bytes, SHA256
fa1723b4496cacc766e983d30fbda69a297e417bb7638de672e36e8770287130.
Report artifacts/android/publication.json. Server source changes remain uncommitted;
preexisting webview/build-info.ts change preserved in rollback snapshot:
.euther-bridge/euthercharge-publish-1793079522 (source,binary,dist).
No Caddy/auth changes, no physical hardware/firmware flash.

# Latest — Kotlin app + isolated C6 probe alpha, 2026-10-27

User changed direction: phone provisioning + local C6 probe/assistant workflow.
Implemented android/ (Kotlin/Compose), firmware/xiao-c6-probe/, encrypted
Security2 patch1 RPC, separate read-only tools/h6cs_probe_client.py, persistent
journal/export, explicit demo. See docs/h6cs-app-and-probe.md for scope/commands.
APK: artifacts/android/EutherCharge-0.1.0-probe-debug.apk. Screenshots and
verification.json alongside it. Build output firmware: build/h6cs-probe-c6/.
Private pairing: build/h6cs-probe-private/pairing.json (0600, directory0700).
Retained across rebuilds; do not print/commit/share credentials. No private
pairing data in APK (decompressed entries checked). Per-build identity only.
Tests:6 JVM crypto/validation,2 Android11 emulator UI+encrypted fixture,4 Python
protocol,175 exact RPC host boundary cases under ASan/UBSan; C6 build succeeds;
Android lint0errors,17warnings (mostly available dependency updates/API attrs).
All charger GPIO/ADC/PWM absent/blocked in probe target. Reports only MCU/heap/
Wi-Fi data. NOT a solder-in-ready charger or qualified electrical probe. First
physical gate: disconnected C6 USB bench provisioning, then measured adapter +
independent inhibit. Original controller/firmware images unchanged.
No physical device installed/flashed, no commit/push. Browser emulator untouched.

# Latest — interactive own-C6 browser mode, 2026-10-26

`http://127.0.0.1:8766/?profile=c6` now runs the SAME portable C++ Application,
Controller, Display and Indicator via WebAssembly with a virtual Board adapter.
Not a C6/RISC-V CPU emulator; no production ESP-IDF driver execution in browser.
Run/pause, MODE, ADC/temperature, millisecond stepping, LCD/indicator outputs,
reset/watchdog and JSON snapshot. Synthetic timing/temperature explicitly labeled.
No private ROM bundled. C6 hardware profiles/images unchanged and unqualified.
Build: tools/build_h6cs_browser.sh (WASI SDK34 in ignored build/toolchains).
Tests: tests/h6cs-browser.mjs (500 native/WASM checkpoints,30fields+LCD),
tests/h6cs-browser-ui.cjs (Firefox interactive,export,profiles,mobile).
Screenshot: artifacts/h6cs-emulator/c6-browser.png. Read emulator/README.md.
No hardware/USB/flash/commit/push. Server CSP permits WASM only in addition to
self scripts; restart server after this change if restoring an older process.

# Latest — all C6 pins assigned and combined image, 2026-10-26

Complete15-signal XIAO pin proposal in independent/main/pin_assignment.hpp; see
 docs/h6cs-c6-pin-assignment.md. Uses all11 edge GPIO plus rear4/5/6/7 pads.
GPIO4/5 permitted only for mode indicators via explicit profile field; other
roles/reservations stay blocked. No guessed NC outputs. Electrical qualification,
clock, ADC transfers/curve are still missing: deployment profiles remain disabled.
12,000 exact-map virtual-driver passes, all indicator modes/reset plus existing
profile/board regressions pass. Full C6 image built and merged:
build/h6cs-independent-c6/euthercharge-independent-c6-full.bin (256128 bytes),
SHA256 9b986384050830487323d2836052b8ae90013c7461301c4719ede8d53ab087e7.
Embedded bootloader/partition/app byte matches verified; report pinned-build.json.
This is a complete build artifact, NOT an installation-qualified charger image.
No hardware/USB/flash/commit/push. Historical images remain withdrawn.

# Latest — independent application, virtual board and C6 image, 2026-10-26

Implemented display/indicator rendering, startup gating, reset/watchdog lifecycle
and direct production Board integration for the independent controller. Complete
ESP-IDF target firmware/xiao-c6-independent builds without private ROM/CPU generator;
checked-in profiles intentionally block startup before charger pin access.
10,000 display comparisons;131,072 timer cases and16,000 loop passes /45 fields;
12 lifecycle/error/indicator cases;24,000 virtual-driver application passes and94
LCD wire frames. Driver regressions and Firefox playback pass. Preview:
artifacts/h6cs-emulator/application-preview.html (recorded playback, not live CPU).
Read firmware/xiao-c6-independent/README.md for exact scope and build/test commands.
Full ELF/app/bootloader/partitions under build/h6cs-independent-c6. New image is
start-blocked and not installation-qualified. No actual C6/charger test or flash.
Physical profile/curve/timing, C6 workload and independent inhibit remain gates.
Historical translated C6 images stay withdrawn. No commit/push.

# Latest — portable temperature and serviced-Timer0 loop, 2026-10-26

Independent controller now includes ADC1 curve/filter/hysteresis, feedback display
level classification and serviced-overflow pending-event rules/main-loop ordering.
No original table bundled: TemperatureCurve requires explicit caller-supplied
thresholds; standalone demo uses a clearly synthetic linear curve.
Temperature/level: 20,000 sample + 32,005 hysteresis + 196,608 level cases.
Thermal composition: 14,000 frames / 35 fields. Scheduler: 131,072 counter cases
and16,000 loop passes / 37 fields;13 coalesced bursts,25 display requests.
ASan/UBSan comparisons against original routines pass. C6 code object now2862
bytes; no undefined symbols. See docs/h6cs-independent-controller.md and latest
Regis handoff. Remaining: LCD/indicators/startup, reset/watchdog, actual timing,
asynchronous I/O and guarded adapter integration, then physical qualification.
No hardware/flash/image link/commit/push. Historical C6 images remain withdrawn.

# Latest — independent portable controller, 2026-10-26

Added firmware/components/h6cs_controller: ROM-free C++17 state policy, button,
main-loop gates, filters and regulator composition. Offline advanceFrame has
explicit event cadence and excludes temperature/display/scheduler implementation.
96,000 isolated comparisons, 5,082 original-ROM live handler calls (4M instructions)
and 14,000 composed event frames / 31 compared values pass with native ASan/UBSan.
Standalone ROM-free demo: build/h6cs-reference/controller-sim; CSV/report artifacts
under artifacts/h6cs-emulator/controller-*. C6 code object compiles to1962 bytes,
no undefined symbols. No linked app or actual C6 execution. Existing translated
application unchanged. See docs/h6cs-independent-controller.md for commands,
exact comparison exclusions and next implementation steps.
No hardware/flash/commit/push. Historical C6 firmware images remain withdrawn.

# Latest — nominal internal IR carrier, 2026-10-26

Added opt-in nominal internal-source IR in JS/native, including 38/57kHz,
polarity/gating, PB1 direction/mux, sleep/reset handling and browser configuration.
50% duty, phase origin and gating phase are explicit experiment conventions.
15,844 GPIO differential checkpoints pass, including 4,256 IR checkpoints;
native ASan/UBSan guards, Firefox, 128 adapter scope guards and actual C6 component
compilation pass. Four original-ROM GPIO runs (16M instructions / 19,996
checkpoints) still agree and reach state5. Full JS suite: 180/180 tests pass.
See docs/h6cs-ir-model.md and latest docs/h6cs-regis-handoff.md section.
External-crystal IR, exact phase/duty, live PSxCV, prescaler-derived buzzer and
physical timing/configuration remain open. No hardware, image link or flash.
Previous C6 images remain withdrawn.

# Latest — Timer0/RFC/LVD and native GPIO, 2026-10-26

Added explicit Timer0 external/low oscillator inputs, RFC gating and ideal LVD,
plus native latch/pad GPIO resolution with IRQ/LCD edges and Halt wake. Fixed
Timer0 residual-phase bypass ticks, IR enable decoding and comparator priority.
173/173 JS tests and 9,531 auxiliary + 11,588 GPIO differential checkpoints pass. Four original-ROM
latch/pad/fill runs (16M instructions total) agree and reach state5. Adapter guards
now cover 128 unsupported-state cases. Firefox and actual C6 component builds pass.
Detailed evidence: docs/h6cs-remaining-peripherals.md and final Regis handoff.
Live prescaler values, dependent buzzer taps, IR carrier and physical timing/fuses
remain unresolved. No hardware, image link or flash; historical C6 images withdrawn.

# Latest — Halt/Standby, comparator and buzzer, 2026-10-26

Both cores now support explicitly configured sleep/wakeup, ideal comparator
inputs/mismatch flags/output priority, and all 24 timer-derived buzzer taps.
Browser exposes sleep assumptions and comparator test voltages. PS0–PS3CV reads
are counted, but their live values/prescaler-derived buzzer taps remain unmodeled.
161/161 JS tests, 3,881 sleep and 26,640 analog/buzzer differential checkpoints
pass, as do original
ROM, reset, adapter, feedback, Firefox and actual C6 component regressions.
See docs/h6cs-low-power-and-comparator.md and the final Regis handoff section.
No hardware/flash/image link. Board still rejects unverified physical modes.
Original 4M reference startup reaches state5 with zero PSxCV reads/sleep/comparator
use; this does not establish that other paths never use them.

# Latest — Timer2/3, external timer clocks and DAA, 2026-10-26

Timer2/3 counters, buffered reload/duty, PWM outputs and underflow interrupts now
work in JS/native. Timer1/2/3 accept explicit external clock edges. DAA supports
valid packed-BCD addition. Browser diagnostics/export include Timer2/3.
145/145 JS tests; 26,751 synthetic timer differential checkpoints; all 20,000 BCD
addition/carry combinations; normal/reset original-ROM comparisons, adapter
regressions, Firefox and actual C6 component builds pass. No hardware/flash.
Board still rejects physical Timer2/3 output use. Live PSxCV encoding, SLEEP/wakeup,
buzzer, analog event generation and exact IRQ timing remain open.
See docs/h6cs-timers-and-daa.md and the final Regis handoff section.

# Latest — reset, watchdog and ADC reference, 2026-10-26

Hardware reset/startup and native watchdog now have explicit opt-in models.
128/128 JS tests; 16,009,974 reset differential instructions/16,022 checkpoints;
24M adapter recovery instructions; 8 watchdog sensitivity runs pass. At assumed
1 MHz/3.5 ms the original ROM resets twice in 4M quanta; at 2 MHz it does not.
This is configuration sensitivity, not recovered original settings. ADC reference
lookup now ignores reserved bits; 1024 decode/256 invalid-key checks pass.
See docs/h6cs-reset-model.md and final docs/h6cs-regis-handoff.md section.
No hardware operation or new linked image. Historical C6 images remain withdrawn.

# Latest — photo-based display and functional lab run, 2026-10-25

**Newest replacement-focused work:**120/120 emulator tests pass. Fixed PB3–5
analog register selection and CPU writes to read-only status/counter/table fields.
C6 adapter now rejects unsupported state before output updates and reports failed
shutdown commands.104 scope/8 shutdown tests,184M board replay,61.6M differential,
144M feedback instructions plus Firefox and actual C6 component build pass.
Incremental builds regenerate instruction source. No image link/flash/hardware.
See final Regis handoff section for exact logs and unresolved physical/software gaps.

**Newest continuation:** comparator interrupt routing, read-only CMPOUT and11
cold-reset register values corrected in JS/native.114/114 emulator tests,
132096 interrupt gating cases,512 OSCCR writes,61.6M differential instructions,
Firefox UI and C6 component compile pass. See last Regis handoff section for
logs and remaining peripheral/reset/timing limitations. No image link or flash.

**Later continuation:** CPU skip/fetch boundary fixes and106/106 emulator tests
pass, plus61.6M native differential instructions and Firefox startup/error UI.
Server restarted at http://127.0.0.1:8766. See final section of
`docs/h6cs-regis-handoff.md` for evidence and remaining fidelity gaps.
No hardware access or flash; historical firmware images remain unqualified.

**Latest interrupt follow-up:** fixed LVD/Timer2 flag dispatch and Timer3's
separate enable/flag routing in JS and native runtime.109/109 emulator tests,
131584 gating cases per runtime,61.6M differential instructions and C6 component
compile pass. Event generators and timing/reset gaps remain open; see final
Regis handoff section. No new linked image or hardware operation.

User supplied actual red EAFC charger photo (28.0°C, summer, car LED).
Rebuilt emulator housing with SVG seven-segment blue LCD driven by actual LCD
RAM; code-derived digit map, preliminary icon labels. Four LEDs read emulated
GPIO direction+values. Private photo copied into artifacts/h6cs-emulator/.

New controls: Labbkörning (explicit experimental arithmetic + fast synthetic
Timer0, warmup200k), Displaytest28.0°C (original subroutine fixture), speed selector,
and firmware-table sensor temperature slider. Actual100sample conversion tested
for all65points -15..49; R33:R32=temp*100 under experimental arithmetic. Raw ADC
controls remain. ADC1=2176 yields28°C model. No physical calibration claim.
16core tests pass; Firefox tested photo28.0, summer/LED, ADC mapping, running main
loop nonzeroLCD and prior interactions/mobile. Screenshot original-desktop.png.
Server still http://127.0.0.1:8766; refresh page to load updates.
No original-ROM change, programmer access, hardware writes, commit or push.

---

# Latest — graphical emulator running, 2026-10-25

User requested graphical charger emulator with editable states and MCU-family
switching. Implemented separate `emulator/` (existing KW520 studio untouched).
Open http://127.0.0.1:8766 then Ladda labbdump. Server currently launched via
`python tools/serve_h6cs_emulator.py --firmware dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin`.
If process ended, run that command again. Loopback only, no hardware access.

NY8 partial CPU executes actual ROM, banked RAM, GPIO LCD, ADC stimuli, button,
state edits, breakpoints and snapshots. Strict mode stops at0207/3537 after
correct LCD init. Experimental carry-arithmetic + synthetic timer/ADC runs1M
instructions; unverified assumptions remain visible. AVR/STM32 are standalone
behavioral porting profiles, NOT CPU emulators or drop-in compatibility claims.

12Node tests pass. Firefox GUI test passes including mobile, ROM load, strict
halt, state/RAM edit, profiles, faults, breakpoint and export. See
`emulator/README.md`, `docs/h6cs-emulator.md`, screenshots under
`artifacts/h6cs-emulator/`. `tests/h6cs-emulator-ui.cjs` accepts PLAYWRIGHT_MODULE
and FIREFOX_EXECUTABLE for installed local tooling.

Extra analysis: routine071C exhaustively matches65entrytable floor lookup over
all256inputs; mode assignment block sets281/100,256/100,143/65,256/45 raw
parameters. Physical units remain unresolved. Replacement datasheets redirected
to homepage; no pin-compatible MTP replacement validated.
Original dump hash unchanged; original chip last installed, programmer rails off.
No programmer access, physical modification, commit or push during this work.

---

# Latest dissection — 2026-10-25

Functional map: `docs/h6cs-firmware-functional-map.md`. Identified ten-state
dispatcher, four user modes, button debounce, ADC channels1..4, PWM1 feedback
output and LCD routines. Button handler executed offline:21pressed polls, no
hold repeat, four-mode cycle, bounce rejection. RAM-only one-word modification
changed acceptance to6polls; original binary unchanged, no flashable mod produced.
NY8B062D official lineup confirms OTP if identity correct; not ordinary reflash.
Pin2/3/5 actively used under candidate mapping despite earlier NC tracing; fan
output NOT identified. Don't mod PWM1 frequency blindly (feedback controller).
All work offline, original remains installed with rails last acknowledged off.

---

# Latest offline analysis — 2026-10-25

Dump contains coherent NY8-family code. LCD initializer0x751, called from0x17F,
executes offline to reproduce all four earlier physically captured LCD frames
bit-for-bit (01/18/28/03); eight initial-state variations pass. Candidate port
mapping PA0/PB5/PB4 matches measured SOP16 pins11/10/9.1940nonzero words,
108zeros contiguous at0x792..0x7FD,844unique values. Strong code validation,
exact model still unconfirmed. See `docs/h6cs-nyquest-dump-analysis.md` and
private `dumps/h6cs-nyquest-20261025/analysis/`. No hardware touched this turn.
The live post-read LCD capture issue remains separate from this offline success.

---

# Latest result — 2026-10-25: repeatable 2048-word original MCU readout

Two independent sequential reads match in all2048decoded14-bit words and every
raw byte per input lane. Both lanes agree; prefix matches earlier64-word result.
Dump: `dumps/h6cs-nyquest-20261025/h6cs-readout-2048x14-le16.bin` (4096bytes,
little-endian uint16 per14-bit word).
SHA256: `4b8f241e38f60983267cf0f2de480d9c93e3d9766aefab901aef6e2afb615784`.
Details/remaining limitations: `docs/h6cs-nyquest-chunks-prepared.md`,
`dumps/h6cs-nyquest-20261025/verification.json`.
Installed programmer image: `artifacts/tl866-open-20261025-nyquest-chunks/`.
Original installed, outputs acknowledged disabled. No target write/erase/unlock.
Post-read LCD CS activity observed but no commands decoded on two captures;
normal startup sequence not reconfirmed. Do not claim full function verification.
Exact MCU and complete memory/config coverage still unknown. Next: offline
instruction analysis and investigate capture regression before more hardware work.
Raw data/dumps remain local and git-ignored. No commit/push performed.

---

# EutherCharge handoff — uppdaterad 2026-10-22


## GENOMBROTT: fyra LCD-kommandon avkodade och upprepade

Efter användarens redo kördes FAST-capture på originalet, sedan en andra
passiv fångst för reproducerbarhet. lcd-fast-original-20261024-01/02.json.
Båda gav exakt samma fyra fullständiga12bitarsramar med100prefix:
100000000010 ->0x01 SYS EN
100000110000 ->0x18 RC 256K (LCD-driverns interna oscillator, EJ MCU-klocka)
100001010000 ->0x28 BIAS1/2,4COM
100000000110 ->0x03 LCD ON
Kontrollerat mot Holtek HT1621/1621Gv3.40 kommandotabell s16-17.
https://www.holtek.com/webapi/116711/HT1621_21Gv340.pdf

Första triggningsintervallet innehöll0observeradebitar och tolkas inte;
fyra efterföljande ramar kompletta, inga '?' eller boundaryambiguiteter.
Varje ram~30,7us, startoffset~5,3/37,7/70,3/102,7us från råcapturestart.
768par,256us nominellt. Startburst omkring15,5ms efterpåslag som tidigare.
Båda avslutade med shutdownkvittens. Chipet är monterat, rails avstängda.
Detta är verklig reproducerbar HT1621-kompatibel inittrafik; styrker att
originalkod exekverar. Identifierar INTE exakt MCU eller LCD-tillverkare.
Ingen LCD-RAM-skrivning/displayinnehåll i fångade kompletta ramar.
Hostdecoder utökad med0x18 och0x28 namn, syntetiska tester passerar.
Äldre långsamcapture missadeflanker och CS-intervall; dess3CS-siffra var
undersampling, inte komplett antal transaktioner.


## Senaste: snabb rå LCD-fångst installerad och tomtestad

Användaren godkände snabbare logikanalys och bekräftade chip urtaget inför
flash. Artifacts/tl866-open-20261024-lcd-fast/ är flashad via USBbootloader,
app-only, programmeraren startar. Ingen originalkörning med FAST ännu.
Tomtest lcd-fast-empty-20261024-01.json: ingen trigger,0prover, shutdown OK.
Nästa: USBur, användaren monterar original+adapter och bekräftar, sedan
/tmp/h6cs-open-tl866-venv/bin/python tools/h6cs_lcd_fast.py --output NY.json.

f H6CSFAST: allGPIOinput, normaldrift5,1V VDD och regulator5V DIP4. Ingen
programmeringssekvens. Timer0 prescaler32, trigger kräver CS hög sedan låg;
maxväntan65536ticks nominellt174,76ms. Därefter768par PORTJ/PORTG med exakt
1536 MOVFF till POSTINC0 utan instruktioner mellan. Nominellt3Mpar/s,
256us fångst; CS samplas1/6us efter DATA/WR (som läses samtidigt i PORTJ).
Triggerlatens kan missa början på första ramen; pulser kan fortfarande missas.
Alla rails off före serialoutput. IRQ av under väntan+capture.
Delad1536byte union ersätter äldre LCDbuffert så RAMräcker. Linker map
placerar buffert0x418..0xA17. FSR0 initieras på denna adress. Tidstämplar
behålls bara i gamla captureläget, inga i rawinnerloopen.

Tester: faktisk emitterad assembler räknad/verifierad,1536MOVFF i rättordning;
syntetiskHT1621 SYSEN/LCDON ochRAMWRITE avkodning, trunkeringsavvisning;
LCDcore,ID40,READ8,LATregression och22H6CS-tester passerade.
XC8v1.45FREE. Stor makroexpansion kraschade kompilatorn, ersatt med explicita
assembler-rader; långa timeoutbranch ändrade tillGOTO. Slutbygge lyckades.
Patch tools/patches/open-tl866-lcd-fast.patch plus alla4h6cs*.h återbygger.
Ingen commit/push. Original fortfarande urtaget, inga fler testkommandon körda.


## ID40 originalförsök genomfört 2026-10-24

Efter användarens "klart" kördes ett enda h6cs_id_probe.py-försök.
Capture dumps/h6cs-probe/id40-original-20261024-01.json: ffffffffff,
low12fff, identiskt med tomreferens. Inget giltigt ID; C83-match falsk.
VDD3/regleradDIP4=5, opcode0x7 följt avabort enligt uttryckligt godkännande.
Shutdown kvitterad. Ingen programmeringspulsgrupp/erase/unlock eller retry.
Original sitter kvar. Detta utesluter inte familjen; ingen bekräftad entry
eller fysisk svarssignal i programmeringsläget. Normaldrift hade återkommande
LCD-aktivitet. Fortsatt arbete behöver ändra en dokumenterad entry-/protokoll-
parameter eller verifiera signalnivå/timing, inte identiska repetitioner.


## Senaste: ID40 via opcode7 uttryckligen godkänd, flashad, tomtestad

Användaren sade "den bör vi ta kör på det" efter förklaring av OTP-ID via
WRITE-opcode0x7 följt av abort, och bekräftade sedan "prog är tom".
Detta godkänner det specifika ID-försöket; INTE faktisk skrivning/erase/unlock.
Tidigare förbud mot alla0x7 gäller alltså inte längre just denna sekvens.
Ny firmware artifacts/tl866-open-20261024-id40/ är flashad. Bootloader kom
sent (~15s) och behövde USBreset+set_configuration1; report model1/status2
kontrollerades före erase. Application boot och nytt helpkommando verifierat.

j H6CSID40: exakt frame0x5A5A5A57,32clocks,40responsebits (OTP2_2 med14bit
code). Samma VDD3V/reguleradDIP4=5V. Ingen programmeringspulsgrupp. Omedelbar
abort i firmware efter svar: DATAut blir input, set_vdd(zero), vpp_dis utan
hostväntan; CLOCK hålls aktivt låg tills rails fått1s att urladdas, sedan input.
GPIO/latchfix, READ8 och passivLCDcapture finns kvar.
H6CS_ID40_V1 svarar5bytes ochOFF. tools/h6cs_id_probe.py sparar alla40bits,
visar low12 som hypotes, avvisar all0/all1 och low14all1; enda jämförelsen är
C83 förPMC131/PMS131, ingen automatisk identifikation eller efterföljande read.

Tomreferens dumps/h6cs-probe/id40-empty-20261024-01.json är ffffffffff;
shutdown kvitterad. Originalet är URTAGET och ej ID-testat ännu. Nästa:
USBur, användaren sätter tillbaka original+adapter och bekräftar, kör sedan
h6cs_id_probe.py med ny outputfil utan --empty-socket.

Test tools/test_h6cs_id40.py verifierade256injekterade svar, exaktframe,
72clocks totalt,40sample, ingen extrasignal efteråt. ASan/UBSan. Parsertest
för C83/all0/all1/trasiga svar passerade. Befintliga READ8/LCD/LAT-tester och
22H6CS-tester passerade. XC8v1.45FREE bygge. Ej fysiskt mätt waveform.
Repro: tools/patches/open-tl866-id40.patch motupstream58f8896 samt alla tre
h6cs_{read8,lcd_capture,id40}.h tillfirmware/modes/bitbang. Ej commit/push.


## Senaste webbaudit/test 2026-10-24

Inga reservchip finns; fortsätt webbsökning och diskriminerande tester.
FreePDK development85f5a7b har PMC131/PMS131 readrails2,5/5,5 i stället för
master3/5. Ändring1074054b694ed65db24affbd9db815f0d75cca22 motiveras med
stabilitet/långa ledningar. Befintlig TL866selector+HA17805 kan INTE ge det
paret direkt. Inget spänningssvep eller ändring av targetspänningar utfört.
PFC4600x254a och PMS1630x2a49 finns i issue94 utan angivet stöd; inga
validerade alternativa protokoll hittade. ID0x7-audit dokumenterad i research-
filen; INTE implementerad/körd på originalet. Ingen WRITE/erase/unlock.
Andra passiva LCD-startfångsten lcd-native-original-20261024-02.json gav
DATA10/WR15/CS6 övergångar och6 observerade WR-rises med CS låg, shutdown
kvitterad. Tre CS-pulser vid ~15,5ms återkommer; ej exaktdekoder/MCU-ID.
Originalet fortfarande monterat. Se sista avsnitt docs/h6cs-tl866-research.md.


## Uppstartsaktivitet från originalet efter rättad LCD-ordning

Användaren korrigerade ledningsordningen på 9/10/11; äldre normaldriftstest
ska inte tolkas med säker DATA/WR/CS-mappning. Nu förutsatt DIP9->ZIF9 etc.
Körde lcd-native-original-20261024-01.json: 22 observationer, DATA10/WR17/CS6
nivåändringar, 6 observerade WR-stigflanker när CS låg. Första förändringen
vid nominellt15,539ms efter capturestart, sista vid15,672ms. Tre CS-låga
intervall. Idle initial DATA0/WR0/CS1; stabilt efter burst till100ms.
Tomreferens gav noll övergångar. Alla host outputs inputs, shutdown kvitterad.
Detta stödjer att chipet startar och driver LCD-liknande signaler; inget exakt
MCU-ID och ingen firmwaredump. För få klockflanker för säker HT1621-dekodning;
polling/tvåportsläsning missar sannolikt flanker (många samtidiga ändringar).
Nästa tekniska förbättring: snabbare capture/WR-triggered data sampling om
LCD-protokoll behöver identifieras, inte blint byte av programmeringsprofil.


## Senaste: passiv LCD-capture flashad, inväntar original 2026-10-24

Användaren bekräftade original urtaget. Ny firmware i
artifacts/tl866-open-20261024-lcd-capture/, app-only flashad. USB-bootloader
hamnade utan konfiguration: USB reset följt av set_configuration(1) återställde
report model1/status2; ingen erase innan detta var verifierat. Flash/reset OK.
Nytt r H6CSLCD kräver exakt token. Alla GPIO ingångar; normaldrift samma
matning som föregående test: DIP1 nominellt5,1V, regulatorn håller DIP4 vid5V.
Inga programmeringsklockor/kommandon till target. Fångar förändringar på
ZIF9=RJ4 DATA, ZIF10=RJ5 WR, ZIF11=RG3 CS. Två portläsningar ej simultana.
Timer0 16-bit Fosc/4 prescaler32 -> nominellt375000ticks/s, max37500ticks
(~100ms) eller512observationer. IRQ av under fångsten. GPIO polling ej
kalibrerad, kan missa korta pulser. Alla rails off innan serialresultat.
Tomreferens dumps/h6cs-probe/lcd-native-empty-20261024-01.json:
0 nivåändringar9/10/11, ingen buffertmättnad, shutdown kvitterad.
Original ännu INTE testat med denna firmware; användaren ska USB ur, sätta
originalet tillbaka och bekräfta redo innan tools/h6cs_lcd_watch.py körs.
Hosttest tools/test_h6cs_lcd_capture.py verifierar idle timeout, timestamps,
512-gräns med ASan/UBSan. Tidigare READ8, LAT och22H6CS-tester passerar.
Parser har testats för giltig trace och felaktig header/count/timestamp.
Repro: tools/patches/open-tl866-lcd-capture.patch mot upstream58f8896 plus
båda tools/firmware/h6cs_{read8,lcd_capture}.h till modes/bitbang; XC8v1.45.


## Normaldriftstest med befintlig adapter 2026-10-24

Användaren har anslutit DIP9/10/11 till ZIF9/10/11. Ville undvika mer lödning.
Körde tools/h6cs_runtime_watch.py --existing-adapter-confirmed, inga
programmeringskommandon, alla GPIO ingångar. VDD selector3 nominellt5,1V
på DIP1 först; rawVPP40 selector0 nominellt9,8V till HA17805 sedan, så DIP4
hålls hög på reglerade5V. Inget råVPP till chipet. Fysiska nivåer under last
inte mätta. Vid stopp E0, vänta0,3s, sedan safe_off. Shutdown kvitterad.
Capture runtime-original-20261024-01.json: 1500 USB-prov under 3.345s,
LCD övergångar {'9': 1, '10': 2, '11': 0}. Kan vara uppstart/flytande ingångar;
INTE bevis för fungerande originalkod eller rätt MCU. USB-prov kan missa
korta pulser. Max4s eller1500prov; denna körning nådde provgränsen först.
DIP4 behövde inte isoleras för detta begränsade hög-nivåtest.


## Upprepad native-probe efter visuell adapterkontroll

Användaren säger att kontakten ser bra ut; direkt kontakt till dolda chipben
fortfarande inte mätt. native-original-20261024-02.json sparad.
Samma som tidigare: True; samma som tom sockel: True.
Avstängning kvitterad: True. Inget modell-ID verifierat.


## Korrigering: chipkontakt INTE verifierad

Användaren förtydligade att kontinuitetsmätningarna endast nådde chippklämman;
originalets ben är dolda i klämman. ZIF3/13/14 -> själva kiselkretsens ben är
alltså inte bekräftat. Tidigare formuleringar om verifierad chipkontakt är för
starka. Glapp/dålig kontakt kvarstår som konkret förklaring till svar identiskt
med tom sockel. Ingen ny hårdvaruprobe i denna vända; omplacera/kontrollera
kontakt strömlöst före fortsatt protokolltolkning. Inget alternativt läsprotokoll
för YFC4604/PFC460/PMS163 har validerats med nuvarande adapter/spänningar.


## Viktig elektrisk begränsning efter kontinuitetskontroll 2026-10-24

Användaren har nu bekräftat ZIF3->chip3, ZIF13->chip13, ZIF14->chip14.
Inga nya hårdvarukommandon denna vända. Tidigare uppmätta 3,9V GPIO-high
vid 3V mål-VDD är INTE elektriskt validerat för originalet. Lokal tillverkar-
PDF /tmp/h6cs-pmc131.pdf, V107, s15 anger VIN -0,3..VDD+0,3, VIH maxVDD;
s17 upprepar ingångsgräns. Programmeringsundantag för klock/data ej verifierat.
Assistenten borde ha flaggat detta före originalproberna. Kör inga fler pulser
innan målrelaterade logiknivåer/ingångströskel på TL866 är utredda. Detta är
inte bevis för skada eller förklaring till nollor/ettor. Nästa arbete: kontroll
av programmerarens utgångsdrivning och mottagartröskel, nivåanpassning vid behov.
Höj inte VDD som genväg: 3V/5V är endast vald profils läsvillkor, identitet okänd.


## Native originalprobe genomförd 2026-10-24

Efter användarens klar kördes tools/h6cs_native_read.py med originalet.
Capture dumps/h6cs-probe/native-original-20261024-01.json.
Åtta ord; uniform=True; alla noll=False;
matchar native tomreferens=True.
Tid inklusive off-väntan 1.397s, avstängning kvitterad=True.
Detta identifierar inte MCU och verifierar inte firmware. Inga automatiska
retries, inga skriv-/raderingskommandon. Originalet sitter fortfarande i.


## Senaste: native READ8 implementerad, flashad och tomtestad 2026-10-24

Användaren beställde lokalt klockad rutin och bekräftade programmeraren tom.
Nytt kommando q H6CSREAD8 (exakt token, inga extra argument) gör fast
OTP2_2 READ 0x5A5A5A56, adresser0..7, 14 databitar. Inga ID/write/erase.
Klocka RD0/ZIF13, data ut RD1/ZIF14, svar RC3/ZIF3. LAT-fix bibehållen.
Endast bitsekvensen kör med IRQ av, USB är aktivt under matningsväntetider.
Samma fasta rails och regulatorväntetid50ms som tidigare; VDD3V, reglerad
VPP5V från rawZIF40=9,8V. Automatisk off innan svar, med 0,3+1s väntetid.
Ny firmware i artifacts/tl866-open-20261024-native-read8/, app-only, flashad
via mjukvarubootloader. Första device-sökningen för tidig: ingen erase då.
Native help verifierad. tools/h6cs_native_read.py med 5s timeout körde
--empty-socket -> dumps/h6cs-probe/native-empty-20261024-01.json; svar efter
1,397s inklusive off-väntan, uniforma ord, avstängning kvitterad.
Ingen ny originalprobe ännu. Be användaren USB ur, montera original rätt,
USB åter och bekräfta innan originalkörning.
Hosttest tools/test_h6cs_native.py kompilerar exakt kärna och verifierar
240 klockor, 112 bitprov och injicerade varierande ord. LAT-regression och
22 H6CS-tester passerade. XC8 1.45 FREE byggde. Pulser ej oscilloskopmätta.
Repro: applicera tools/patches/open-tl866-native-read8.patch på upstream
58f8896, kopiera tools/firmware/h6cs_read8.h till firmware/modes/bitbang/,
bygg tl866-bitbang. Patchen inkluderar LAT-fix. Ingen commit/push gjord.


## Kantdiagnostik och protokollgranskning 2026-10-24

Jämfört med lokal free-pdk fpdk.c: OTP2_2 READ 0x5A5A5A56 MSB-first,
12-bitadress och 14-bitdata på hög klocknivå matchar vår implementation.
Upstream ID-preflight använder WRITE 0x7 och är avsiktligt INTE implementerad.
original-edge-diagnostic-20261024-01.json: en ordläsning, 116 kantprov.
DIP3 hög före frame, låg redan vid FÖRSTA stigande klockkanten och sedan låg
vid samtliga prov. Kan därför inte tolkas som kvittens på hela kommandot.
Klockans digitala readback matchade begärd hög/låg vid samtliga 116 prov.
Host-observationer mellan kanter: min6,42/median8,43/max11,45 ms. Detta är
USB-diagnostikens samplingstid, INTE oscilloskopmätt pulsbredd eller timing
i tidigare probe. Upstream begär 1 us högpuls. MCU-identitet fortsatt okänd.
Shutdown kvitterad. Skript diagnose_edges.py ligger i LAT-fix-artifactmappen.
Nästa meningsfulla mjukvaruarbete: lokalt klockad, strikt READ-only sekvens i
programmerarfirmware för att eliminera USB per kant, med offline-verifiering.
Ingen sådan firmwareändring/ny flash ännu utförd.


## Svarslinjetest på original 2026-10-24

original-response-diagnostic-20261024-01.json sparad under dumps/h6cs-probe/.
DIP/ZIF3 lästes HÖG precis före READ-frame, sedan LÅG vid alla 112 databitsprov.
TRIS bekräftade pin3 som ingång vid samtliga observationer; clock ZIF13 lästes
hög vid alla data-samples. Åtta nollord igen. Shutdown kvitterad.
Detta visar olika digitala nivåer vid skilda faser, inte när övergången skedde
eller att MCU tolkat kommandot. Extra T/Z-USB-läsningar ändrar timing.
Ingen erase/write/unlock, ingen spänningshöjning eller pulländring.
Diagnostikskript sparat i artifacts/tl866-open-20261024-latfix/diagnose_response.py.


## Första originalprobe genomförd 2026-10-24

Användaren bekräftade adapterspänningarna OK, sedan originalets pinne1 mot
ZIF1 och gav klartecken. PMS131-S16-hypotes, 8 ord READ-only körd.
Capture dumps/h6cs-probe/original-first-20261024-01.json: åtta nollord,
4,266 s, SHA256 LE16 374708fff7719dd5979ec875d56cd2286f6d3cf7ec317a3b25632aab28ec37bb.
Shutdown kvitterad, inga writes/erase/unlock eller automatiska retries.
INTE identifierad MCU eller verifierad dump. Nollor bevisar inte skydd/tom ROM.
Tidigare tomreferens var före LAT-fix och är inte en likvärdig kontroll.
Fortsatt utredning behövs av signalväg/timing/profil; höj inte spänning blint.


## Senaste fysiska test: GPIO efter LAT-fix

Tom programmerare, levels --high: användaren mätte +3,9 V på både ZIF13
 och ZIF14 mot ZIF16. Tidigare negativ puls återkom inte i denna rapport.
Testet avslutades med SIGTERM till exakt mätprocess; finally kvitterade
shutdown (exit 130 från avsiktlig KeyboardInterrupt). Fysisk avklingning
ännu inte bekräftad. Ingen original-MCU ansluten/testad. Detta verifierar
högnivån enligt multimetern, inte timing eller signalnivåernas kompatibilitet
med okänd MCU. Lågnivå och adapter behöver verifieras före originalprobe.


## Uppdatering: LAT-fix flashad 2026-10-24

Efter uttryckligt "ok flasha på" användes bitbang-kommandot b för bootloader.
Ingen fysisk brygga behövdes. Första sökningen kom före USB-omregistreringen
(ingen erase skickades då); därefter exakt en TL866A med bootloaderstatus 2.
Alla block i nya artifacts/tl866-open-20261024-latfix/-applikationen överfördes,
reset lyckades och /dev/ttyACM0 svarade som bitbang. i+s gav nVPP_EN:1 och
nVDD_EN:1. Ingen spänning aktiverades för test. Ingen full flash-readback.
Fysisk GPIO/spänningsverifiering återstår i TOM programmerare före MCU.
Denna notering ersätter tidigare "ännu inte omflashad" nedan.


## Senaste status: GPIO-granskning 2026-10-24 — ännu inte omflashad

Användaren förtydligade att cirka -2,3 V mättes med röd på ZIF13 och svart
på ZIF16 i HELT TOM programmerare, utan adapter. Skyll inte på adaptern.
Inga hårdvarukommandon under denna granskning. Original-MCU ännu inte testad.
Källkodsdefekt: zif_write läser PORT och återanvänder fysiska nivåer för
icke-ZIF-styrbitar; dessutom använder kontrollmakron PORT för RMW.
Patch tools/patches/open-tl866-preserve-control-latches.patch använder LAT
för utgångar och bevarande. ZIF-läsning och OVC läser fortfarande PORT.
Status via kontrollmakron rapporterar nu LAT (begärd nivå), inte fysisk nivå.
Detta är INTE bevisad orsak till den negativa spänningen.
Hosttest tools/test_open_tl866_latches.py extraherar verkliga C-funktioner:
10496 skrivningar passerar med patch, samma test fallerar på upstream.
22 H6CS-tester passerar. XC8 1.45 FREE byggde patched bitbang firmware.
Ny applikationsfil och manifest: artifacts/tl866-open-20261024-latfix/.
Bootloader/config är exkluderade. INTE flashad; ingen ny spänningsmätning.
Nästa steg är installation av patchad programmerarfirmware och kontrollerat
mättest i tom sockel innan originalet ansluts. Tidigare flash-script pekar på
GAMLA filen; använd det inte oförändrat för den nya versionen.

## Läsprobe implementerad 2026-10-24, original ännu inte anslutet

Användaren accepterar uttryckligen risken med originalet utan känd test-MCU och
vill försöka läsa; detta ersätter tidigare krav på test med känd MCU. Erase,
unlock och WRITE-baserad ID ingår fortfarande inte i genomförandet.
`tools/h6cs_open_probe.py` implementerar open-tl866-backend till den befintliga
READ-sekvensen (PMC131/PMS131-hypotes). Max 16 ord per anrop, 90 s deadline,
inga automatiska retries. DIP3 alltid ingång; endast DIP13/14 drivs.
USB-paced timing är långsammare än upstream och inte verifierad på en MCU.
22 H6CS-tester passerar inklusive transportfel och att shutdown ändå försöks.
Tomadapterreferens `dumps/h6cs-probe/empty-baseline-20261024-02.json`: 8 uniforma
ord, 4,259 s inklusive sekvensens avstängning. Första referensen avbröts korrekt
på svarstolkningsfel; parser rättad till verkliga tio hexsiffror utan Result-prefix.
Inget av detta är en firmwaredump. Därefter startades 45 s hög-nivåtest för
DIP13/14; användarens mätvärden inväntas. DIP3 förblir ingång.
Använd `/tmp/h6cs-open-tl866-venv/bin/python tools/h6cs_open_probe.py ...`.
Innan originalmontering: avsluta nivåtest, USB ur, bekräfta rätt orientering och
placering av 16-bensadaptern i den längre sockeln. Sätt inte MCU med matning på.

## SENASTE STATUS 2026-10-24: Open-TL866 flashad och startad

Senare samma pass monterades tom mellanadapter och samma open-protokoll kördes.
Användaren bekräftade "ja det funkar" efter mätinstruktion DIP4 cirka 5 V och
DIP1 cirka 3 V, båda mot DIP16. Exakta värden lämnades inte. Båda matningarna
är därmed användarverifierade samtidigt genom tom adapter. Testet avslutades
med kvitterade avstängningskommandon och nVPP_EN=1/nVDD_EN=1. Fysisk urladdning
efter detta test behöver fortfarande bekräftas. Originalchipet är inte testat;
GPIO-nivåer, start/stoppförlopp och känt MCU-lästest återstår.

Efter flashningen genomfördes tomsockeltest med open-protokollet: `i`, `v 0`,
`V 0`, `g 0000008000`, `d 0000000000`, `p 8000000000`, `e 1`, `E 1`,
sedan `d 0000000001`. Användaren bekräftade "det funkar ja!" efter instruktion
att mäta ZIF1 cirka 3 V och ZIF40 cirka 9,8 V mot ZIF16 samtidigt. Exakta
mätvärden lämnades inte. Detta verifierar samtidig tomsockelmatning; adapter-
test och fysisk avstängning med den nya firmwaren återstår. AClient.cmd tar
kommando och argument separat (`c.cmd('v', '0')`), inte en sammansatt sträng.

Användaren startade fysisk bootloader och sade "klar". Direkt fråga bekräftade
modell TL866A=1, status BOOTLOADER=2. Förberedda scriptet kördes med --flash:
applikationen raderades och samtliga block överfördes, därefter reset.
Ny USB-identitet 1209:8661 och `/dev/ttyACM0`. ASCII `?` gav
`open-tl866 (bitbang)` och rätt kommandolista med LSB=ZIF1. `i` följt av `s`
gav `nVPP_EN:1 nVDD_EN:1`, alltså båda driverbankarna rapporterat avstängda.
Inga spänningar aktiverades efter flashningen; fysisk spänningsmätning återstår.
Detta är lyckad överföring/start/kommunikation, inte bytevis firmware-readback.

Använd INTE längre minipro/socket_meter mot den nya firmwaren. Använd
`/tmp/h6cs-open-tl866-venv/bin/python` och `otl866.aclient.AClient('/dev/ttyACM0')`.
Sockeln är tom och mellanadaptern borttagen enligt användaren. Bootbygeln ska
vara borttagen. Nästa steg är separat tomsockelmätning med nya protokollet,
sedan tom mellanadapter. Originalchipet förblir utanför.

Flashfil: `artifacts/tl866-open-20261024/tl866-bitbang-58f8896-application.hex`.
Applikations-SHA256: 5b118586994dfa3888206b72893decd07555c169b4d38f2be01c2813d40491ec.
Bygg/recovery-manifest och privat preflashrapport finns i samma ignorerade katalog.
Det äldre avsnittet nedan beskriver förberedelsen före lyckad flashning.

## Aktivt firmwarebyte 2026-10-24: auktoriserat, ännu INTE flashat

Användaren sade "flasha på!" och bekräftade tom ZIF-sockel. Open-TL866 bitbang
byggd från 58f889638992d6a06a94e842fa8efa0a52c407a4, XC8 1.45 Free,
CMake 3.31.10. Applikationsfil och manifest ligger i ignorerade
`artifacts/tl866-open-20261024/`. Bilden är begränsad till 0x1800..0x1fbff.
Bootloader/data/configuration exkluderade. Intel HEX, signatur och krypterings-
rundtur verifierade. Public stock-applikation finns som recovery, INTE som
avläsning av användarens enhet; versionsmatchning är inte fastställd.

USB-reset till bootloader försöktes en gång med upstreams resetkommando; USB
misslyckades sedan med enumeration. Efter användarens återanslutning svarade
enheten som TL866A NORMAL status=1. INGA erase/write-kommandon har skickats.
Ingen anledning att upprepa samma mjukvarureset. Behöver dokumenterad fysisk
bootloaderstart (verifiera punkterna på foto av användarens kort med USB ur).

Förberett verktyg: `/tmp/h6cs-open-tl866-venv/bin/python
artifacts/tl866-open-20261024/flash_prepared.py`. Utan argument: endast offline-
validering. `--flash`: kräver exakt en TL866A med status BOOTLOADER innan erase.
Användarens flash-auktorisering kvarstår; detta är fysisk blockerare, inte ny
begäran om tillstånd. Kontrollera rätt status före flash och ny USB/ASCII-
funktion efteråt. Sätt inte tillbaka mellanadaptern ännu.

## Ny pauspunkt 2026-10-24: mellanadapter byggd, D6-läge felaktigt

HA17805-adaptern är byggd. En kortslutning i experimentkortets koppar upptäcktes
och åtgärdades av användaren. Tom programmerare gav därefter förväntade
grundspänningar. Tom adapter gav DIP4=4,98 V och DIP1=4,47 V; användaren
bekräftade avstängning/urladdning. Originalchipet är fortfarande utanför.

Försöket med samtidig 3,1 V/5 V misslyckades: DIP1 visade 3,1 V men både DIP4
och rå ZIF40 saknade spänning. Firmwaregranskning visar att D6 selector 1
skriver om VPP- och jordlatchar. Det är INTE ett rent spänningskommando och
tidigare påstående om kvarvarande GND16 gäller inte. Nio-bytekommandot saknar
dessutom två bytes som denna gren läser. D1 återställer spänningsvalet och kan
inte användas för att återställa enbart routningen efteråt.

`--adapter-rails` är spärrat före USB-access. Inga nya hårdvarutester ska göras
med detta läge. Nästa arbete är en verklig, granskad styrning av båda matningarna;
upstreams tl866a_set_voltages är en stub. Se forskningsloggens 2026-10-24-notering.
Senaste testet avslutades med skickade D0/04. Ingen MCU-läsning är implementerad.

## Paus inför nästa arbetspass — H-6CS

Användaren fortsätter tidigast nästa dag eller lördag. Inga fler hårdvarutester
ska startas under pausen. Vid handoffkontrollen körde varken socket_meter eller
dumpcap. Detta bevisar inte att sockeln är spänningslös; USB kan kopplas ur för
förvaring. Originalchipet ska ligga utanför programmeraren tills kopplingen är klar.

### Ny information från användaren

- Adaptern är en **rak SOP16→DIP16 med 16 ben**, kopplad ben-till-ben.
- Den får plats i MiniPro men omfördelar inga signaler och reglerar ingen matning.
- Planen är att behålla den som chipbärare och bygga en **mellanadapter**, exempelvis
  på experimentkort med DIP16-sockel. Ingen mellanadapter är ännu byggd eller ritad.
- Användaren har även en GQ-4x4, men inget verifierat stöd för kandidatkretsarna där.

### Matning och pinstatus — blanda inte ihop chipben och ZIF-positioner

| Chipben | Uppmätt på laddarkortet | Kandidatens experimentella läsläge |
| --- | --- | --- |
| 1 | VDD, normalt +5 V | Cirka 3 V VDD |
| 16 | GND | Gemensam jord |
| 4 | Knappingång | 5 V VPP **endast enligt PMC131/PMS131-hypotesen** |
| 13 | Resistorväg till kontakt | Klocka enligt samma hypotes |
| 14 | Resistor-/kondensatornät till kontakt | Data från programmeraren enligt hypotesen |
| 3 | Externt oanslutet på kortet | Data från MCU enligt hypotesen |

Ingen kandidat är identifierad. Tidigare 24-benskorrigering gäller LCD-drivern;
den nu bekräftade raka MCU-adaptern har 16 ben. Inget godkänt chip→ZIF-schema finns.

För läsprofilen ska VPP vara stabila 5 V under läsningen, inte pulsas bitvis.
EasyPDK-sekvensen slår på VPP först, sedan VDD; vid avslut VDD av före VPP.
Klockpulserna går på en separat signalledning. Regulatorns start och urladdning
måste därför ingå i adapterverifieringen.

TL866 kan ge två spänningar, men dess dokumenterade VPP-skena börjar vid cirka
9,8 V. Föreslagen lösning utan separat nätaggregat: VCC cirka 3 V och VPP cirka
9,8 V genom en **5-V-regulator på mellanadaptern**, exempelvis en lämplig 78L05.
Detta är en oprövad konstruktion, inte ett färdigt inkopplingsråd. En regulator
ersätter inte krav på rätt signalnivåer, sekvensering, strömbegränsning och
verifierad avstängning. Anslut aldrig råa 9,8 V till kandidatens 5-V-VPP-ben.

### Börja här nästa gång

1. Kontrollera aktuell Git/USB-status och läs forskningsloggen. Upprepa inte
   tidigare felande D6-test: varje D6 måste följas av läsning av sitt sjubytes svar.
2. Rita och granska mellanadaptern: exakt ZIF-placering, signalomfördelning,
   regulator med rätt kapselpinout/kondensatorer samt på/av-förlopp. Fastställ
   vilka komponenter användaren faktiskt har innan en bygglista låses.
3. Verifiera utan originalchip: kontinuitet, 3 V och 5 V samtidigt, GPIO-nivåer,
   avstängning och urladdning. Testa därefter lässekvens på en känd krets innan
   originalet övervägs. Fortsätt MCU-identifieringen parallellt med dessa steg.

Skrivskyddsupplåsning, erase, programmering och EasyPDK:s WRITE-baserade ID-probe
ingår inte. Läsning av originalet är fortfarande ett framtida steg, inte redo nu.

### Kod, verifiering och lokala artefakter

- Pushat till `origin/main`: `a4cdb22` (H-6CS-verktyg och D6-fix),
  `12573d2` (digital pinhantering och tomsockeltest). 24 Python-tester passerade.
- `tools/h6cs_pdk.py`: enbart offline-lässekvens och dumpjämförelse; ingen USB-backend.
- `tools/h6cs_socket_meter.c`: stock TL866A 03.2.86-tester för tom sockel.
  `--voltage-cycle` läser båda D6-svaren; `--logic-test` kontrollerar digitala pinnar.
  Inget av dessa läser en MCU. Normal firmwarestatus kontrolleras före pin-kommandon.
- `docs/h6cs-tl866-research.md`: källor, mätningar, felspår och verifieringsgränser.
- Privata USB-fångster i `dumps/h6cs-usb/`, särskilt
  `voltage-cycle-050.pcapng` (fel) och `voltage-cycle-fixed-053.pcapng` (rättad).
  De innehåller enhetsidentitet och ska inte pushas. dumpfiler är Git-ignorerade.
- Byggd testbinär och minipro-objekt i `/tmp/h6cs-minipro-check.BbSOkT/`.
  Upstream EasyPDK i `/tmp/h6cs-easypdk-software/`; firmwareanalys i
  `/tmp/h6cs-protocol-review/`. Dessa kataloger kan försvinna vid omstart.
  Källorna som behövs för vårt eget arbete finns i repot; detaljer om upstream
  revisioner och byggning finns i forskningsloggen.
- USB-buss/enhetsnummer ändras vid återanslutning: använd inte sparade nummer
  50/53 blint i fångstfilter. usbmon-åtkomst och USB-enhetens rättigheter är olika.
  Linux timeout vid enumeration är inte ett vanligt användarbehörighetsfel.

## Nytt separat spår — H-6CS, 2026-10-22

HC-XS6-kort med okänd SOP16-MCU och 24-bens LCD-driver. Se
`docs/h6cs-tl866-research.md`, `tools/h6cs_pdk.py` och `tools/h6cs_socket_meter.c`.
Ingen MCU har identifierats eller dumpats; ingen programmerarfirmware har ändrats.
Originalkretsen har legat utanför TL866 under samtliga tester. KW520-status nedan kvarstår.

TL866A 03.2.86: tom sockel uppmätt till 4,47 V VCC och 9,8 V VPP;
D6 VCC-kod 0 efter D1 gav 3,1 V. Tidigare USB-låsningar kunde reproduceras.
Firmwareanalys visade att D6 returnerar sju byte som testverktyget inte läste.
Rättad cykel på enhet 53 gav båda svaren d6000000560201, lyckade D0/04 och
fungerande informationsfråga efteråt. Fix verifierad över USB i en cykel;
fysisk avstängning efter denna cykel är inte uppmätt. Timer är ingen hårdvarubrytare.
USB-fångster, identitetsuppgifter och firmwarefiler ligger lokalt i ignorerade dumps/.

24 Python-tester passerar. Padauk-läsaren är fortfarande en offline-prototyp.
Nytt --logic-test: alla åtta digitala kombinationer på ZIF3/13/14 lästes tillbaka
korrekt på tom TL866-sockel utan VCC/VPP-drivare. Dessa är testpinnar, inte en
godkänd adapterkoppling. Signalnivåer och MCU-kommunikation återstår att verifiera.
EasyPDK:s OTP-identifiering, även före read, skickar WRITE 0x7; använd inte detta
på originalet som antaget ren läsning. Endast experimentella PMC131/PMS131-profiler.
Nästa gräns: separat verifierad 3-V/5-V-matning, adapter, signalnivåer/timing och
läsprov på känd krets. VPP 9,8 V får inte ersätta profilens 5 V. GQ-4x4 finns som
reserv, men stöd/protokoll för dessa kandidater är inte verifierat.
Extern strömkälla är inte fastställd som nödvändig: en 5-V-regulator på adaptern
från TL866:s 9,8-V-skena är ett möjligt alternativ som ännu inte är verifierat.

## Läs detta först

EutherCharge modifierar den externa SPI-flashen i en KONNWEI KW520. Den första
modifierade kretsen är programmerad, verifierad, återmonterad och har startat i
den riktiga laddaren. Användaren bekräftar att gränssnittet nu visar svenska.
Laddaren visade ingen märkbar ny grafik.

Detta är fysisk bekräftelse av uppstart och den svenska externa textbanken,
inte ett godkänt laddnings- eller skyddstest. Laddningsreglering, kalibrering,
temperaturövervakning och skydd har inte modifierats.

## Checkout och Git

- Arbetskatalog: `/run/media/nichlas/Kingston1TB/EutherCharge`
- Publik remote: `https://github.com/NichlasEk/EutherCharge.git`
- Branch: `main`
- Git-metadata ligger avsiktligt i `.git-local`, inte `.git`.
- Använd alltid `git --git-dir=.git-local --work-tree=.` i denna checkout.
- Senaste verifierade commit före denna handoff: `9e1058c`.
- `dumps/`, `build/` och firmwarebinärer är Git-ignorerade och ska förbli lokala.

## Bekräftad hårdvara

- Produkt: KONNWEI KW520.
- MCU-märkning, användarrapporterad: `AT32F421C8T7`, Cortex-M4.
- Extern flash: Eon EN25Q32A/B, 4 MiB, JEDEC-ID `1c 30 16`.
- Stabil programmerare: TL866A, firmware `03.2.86`.
- Profil: `EN25Q32A@SOP8` med `minipro` 0.7.4.
- CH341A gav instabila läsningar och ska inte användas som bevis eller
  skrivunderlag för denna krets.
- En J-Link är beställd men hade inte anlänt vid handoffen.

## Bitexakta artefakter

Alla filer nedan är lokala och Git-ignorerade.

### Original

```text
Fil: dumps/original/kw520-1.0.1-original-d369a860.bin
Storlek: 4 194 304 byte
SHA-256: d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2
Rättighet: skrivskyddad lokalt, mode 0444
```

Tre separata TL866A-läsningar var byte-identiska. En extra förläsning precis
före programmering matchade också originalet byte för byte:

```text
dumps/preflash/kw520-before-euthercharge-2026-10-18.bin
```

### Programmerad EutherCharge-image

```text
Fil: build/euthercharge-kw520-1.0.1-full.bin
Storlek: 4 194 304 byte
SHA-256: 4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329
```

Imagen skiljer sig från originalet med exakt 2 269 byte, endast inom:

- `0x000000–0x0001ff`: en 512-byte, 128×32, 1-bpp kolumn/LSB-logotyp;
- English-bankens redan allokerade strängpayloads: 142 ändrade poster.

Pekartabeller, längdprefix, filstorlek och alla andra områden är oförändrade.

### Readback efter programmering

```text
Fil: dumps/readback/kw520-after-euthercharge-2026-10-18.bin
Storlek: 4 194 304 byte
SHA-256: 4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329
```

TL866A:s automatiska verifiering, en separat verifieringskörning och en full
oberoende readback lyckades. Readbacken matchade byggimagen byte för byte.

## Fysiskt resultat

Användarens rapport efter återmontering:

- laddaren startar igen;
- den visar svenska, vilket den sannolikt inte gjorde före modifieringen;
- ingen ny grafik syntes;
- inget laddnings-, temperatur- eller skyddstest är dokumenterat.

Den svenska texten bevisar att MCU:n läser English-banken från externflashen.
Den uteblivna grafiken betyder att datan vid `0x000000` inte kan kallas en
verifierad, aktiv startlogga trots att den avkodar till en komplett KONNWEI-
bild. Den kan vara en oanvänd resurs, visas endast i ett annat läge eller
ersättas av grafik från MCU:ns interna flash. Undersök detta efter MCU-dump;
programmera inte om externflashen enbart på denna hypotes.

Animationer, fysiskt ljud och Fan Hymn finns endast i Studio-prototypen och har
inte implementerats i laddaren.

## Reproducering och tester

Bygg till ett nytt filnamn; byggskriptet vägrar skriva över en befintlig fil:

```sh
node tools/build-euthercharge.mjs \
  dumps/original/kw520-1.0.1-original-d369a860.bin \
  build/euthercharge-rebuild.bin
sha256sum build/euthercharge-rebuild.bin
```

Förväntad SHA-256 är
`4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329`.

Kör hela den nuvarande testsviten med:

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/studio-core.test.mjs
```

Senast verifierat resultat: 9 Python-test och 7 JavaScript-test passerar.

Studio startas lokalt med:

```sh
python3 -m http.server 8765 -d studio
```

Använd Firefox för `http://127.0.0.1:8765`.

## Nästa fas när J-Link anländer

Målet är en helt icke-destruktiv SWD-inventering av MCU:n. Läs
`docs/internal-flash-access.md` innan något ansluts.

1. Bekräfta MCU-märkningen med ett skarpt foto av kortet.
2. Med allt spänningslöst: identifiera MCU-pin 1 och mät kontinuitet från
   `PA13/SWDIO`, `PA14/SWCLK`, `NRST` och `GND` till testpunkter.
3. Koppla aldrig J-Link samtidigt som laddaren är ansluten till nätspänning
   eller batteri. Mata aldrig MCU:n med 5 V.
4. Använd J-Linkens `VTref` som spänningsreferens, inte som en antagen
   strömkälla. Bestäm kortets säkra 3,3-V-matning innan start.
5. Börja med 50–100 kHz SWD och connect-under-reset.
6. Läs endast debug-ID, chip-ID och skyddsstatus först.
7. Avbryt om verktyget erbjuder eller kräver `unlock`, `recover`, `unprotect`,
   option-byte-skrivning eller mass erase.
8. Om huvudflashen är läsbar utan ändring: läs `0x08000000–0x0800ffff`
   tre gånger till nya filer, jämför byte för byte och beräkna SHA-256.
9. Om den är låst: försök inte avlägsna skyddet. Dokumentera status och
   fortsätt med icke-invasiv bussmätning i stället.

Använd inte en STM32-profil som ersättning bara för att kärnan liknar en
STM32. Kontrollera först att den installerade J-Link-versionen uttryckligen
stöder rätt AT32F421-enhet eller en verifierad Cortex-M4/SWD-läsmetod utan
skrivning.

## Analysmål för internflashen

Prioriterad ordning om tre identiska MCU-dumpar kan erhållas:

1. verifiera vektortabell, minneskarta och kodarkitektur;
2. hitta SPI-läsningar från externa EN25Q32 och referenser till `0x000000`;
3. hitta displayinitiering, buss, framebuffer och ritprimitiver;
4. hitta textindexering och förklara varför svenskan laddas men loggan inte syns;
5. hitta batteri-/statusikoner och animationslogik;
6. kartlägg temperaturmätning och fläkt-PWM endast som read-only analys;
7. separera UI-kod från laddreglering, kalibrering och skydd innan någon patch
   ens föreslås.

Ingen intern MCU-patch ska skrivas innan en separat kodgranskning och en
kontrollerad verifieringsplan finns. Originaldumpar ska alltid bevaras
bitexakt och förbli lokala.

## Viktiga dokument

- `docs/research-log.md`: kronologiska fynd och fysisk programmering.
- `docs/firmware-map.md`: externflashens verifierade minneskarta.
- `docs/resource-format.md`: textbanker och historikposter.
- `docs/architecture.md`: systemgränser och experimentnivåer.
- `docs/internal-flash-access.md`: read-only SWD-plan och stoppvillkor.
- `studio/README.md`: lokal Studio-prototyp.

## Exakt pauspunkt

Externflashfasen är avslutad med lyckad readback och fysisk svensk UI-start.
Gör ingen ny externflashskrivning nu. Nästa praktiska grind är att J-Linken
anländer och att kortets MCU-märkning och SWD-testpunkter dokumenteras utan
nätspänning eller batteri.

## System Regis emulator continuation (2026-10-25)

See `docs/h6cs-regis-handoff.md` for current emulator, independent NYASM carry
verification, ADC/Timer0 models, tests, artifacts and next state-graph work.
No hardware operations performed. Earlier programmer research changes preserved.

### Latest C6 continuation

`firmware/xiao-c6/README.md` and the latest section of
`docs/h6cs-regis-handoff.md` describe the integrated original-program C6 firmware.
Full ESP-IDF build and61.6M instruction differential tests pass; the electrical
profile is unconfigured, outputs are inhibited and no physical test/flash has
been performed. Current private image: `build/h6cs-c6/euthercharge-c6-full.bin`.

### Flash qualification withdrawn; continue emulation

Latest user instruction requires working firmware before flash. The previous
merged C6 image is NOT a candidate: subsequent production-driver replay found
PWM API and lost-GPIO-transition bugs. Both fixed in source;32 virtual adapter
runs /184M instructions pass. See `tests/h6cs-board-replay.mjs` and latest Regis
handoff section. Timing, real electrical transfer and power-stage behavior remain
unverified. No new image linked or flashed in this continuation.

### Latest virtual timing/feedback continuation

Scheduler now checks elapsed time around instructions and driver updates; long-
uptime arithmetic and blocking telemetry fixed. `tests/h6cs-timing-feedback.mjs`:
12 scheduler guards,6 latency cases,18 raw-domain feedback experiments pass.
32 adapter replay regressions also pass. Reports explicitly remain flashReady=false;
model gains/polarities are hypothetical, not hardware configuration. See latest
`docs/h6cs-regis-handoff.md` section. No new image linked or flashed.

### 2026-10-27: probe Wi-Fi handover repair

USB-only XIAO ESP32-C6 EC6-D51654 updated in place to probe 0.1.1, app partition
only; NVS/pairing preserved. USB status confirms wifi_configured=true and home
DHCP IP 192.168.32.80. RSSI -93 to -95 dBm; desktop LAN RPC initially failed with
no route to host. User asked to reposition module. USB was then disconnected.
Do not equate DHCP with proven end-to-end LAN RPC. Electrical IO still blocked.
Firmware now has restricted USB status/reconnect console (no secret output).
App 0.1.1 versionCode2 permits cancelling pending provisioning/connection,
releases setup Wi-Fi request, opens Wi-Fi settings, remembers confirmed LAN IP
and explains uncertain handover instead of reporting definite failure.
6 JVM tests, lint, 3 Android instrumentation tests including busy cancellation,
firmware build and exact RPC ASan/UBSan tests passed. Artifacts/checksums in
artifacts/android/verification-0.1.1.json. Server publication in progress.

Follow-up: after user repositioned/powered the C6 separately, authenticated
encrypted status and capture succeeded over LAN from desktop. MAC matches
10:bd:a3:b3:b9:b0, IP192.168.32.80, RSSI -84dBm at first successful response.
USB absent from desktop at this point. Physical LAN evidence saved in
artifacts/probe-bench/lan-{status,capture}-0.1.1.json. This verifies live MCU
telemetry only: ADC remains empty and charger outputs remain unconfigured.

Publication complete: EutherCharge 0.1.1-probe versionCode2 is on the server app
card and https://apothictech.se/downloads/EutherCharge-0.1.1-probe-debug.apk .
Server build and eutherhost restart succeeded; service active. Full LAN/public
APK readbacks match local SHA256; report artifacts/android/publication-0.1.1.json.
Old 0.1.0 route retained. Server changes uncommitted, baseline unrelated dirty
files preserved. Android physical-phone handover fix still awaits user test.
For evening: join home Wi-Fi, import private pairing if app restarted, use
192.168.32.80 and connect; avoid provisioning again since credentials are saved.
No charger/power-stage IO has been enabled or tested. Test emulator/fixture stopped.

### 2026-10-31: first KW520 J-Link SWD attempt

User confirmed wiring/isolation after discussing MCU 3.3 V from charger PSU;
these physical facts remain user-reported. No NRST wire. USB ACL granted by user.
OpenOCD ESP32 build v0.12.0-esp32-20250707 with built-in J-Link driver reports
J-Link V9 firmware May 7 2021 16:26:12, HW9.40, target3.290V. USB product label
PLUS was not sufficient to identify actual model. No probe firmware update.
Generic ARM DAP-only attempts at50kHz and10kHz both failed:
Error connecting DP: cannot read IDR. No CPU/flash driver loaded, no reset/halt,
no flash read/write, no erase/unlock, no target-power command. Debug transport
initialization was attempted; do not describe it as entirely passive.
Logs/configs: build/kw520-jlink-20261031/. Do not infer flash protection or wrong
MCU identity from missing DP response. Next: power down before wiring changes,
verify SWDIO/SWCLK continuity/orientation and add verified NRST for controlled
connect-under-reset if wiring is correct. No blind retries or STM32 profiles.

### 2026-10-31: corrected connector, successful SWD identification

User discovered reversed ribbon connector, reported charger still starts, then
corrected connection. USB re-enumerated002/076; user granted new ACL. At50kHz,
no reset wire, generic DAP + mem_ap (no MCU-specific flash driver):
DPIDR2ba01477, AP0_IDR24770011, BASEe00ff003, CPUID410fc241,
DEVICE_ID atE0042000=50020100 (AT32F421C8T7 per upstream OpenOCD artery.c).
FLASH_USD status at4002201C=03fffffe: bit1 FAP=1, bit26 FAP_HL=0 ->
low-level access protection enabled. STOPPED without flash dump/unlock.
No CPU halt/reset, no program/option-byte writes, no erase or target-power-on
command. DAP transport setup necessarily writes debug access registers only.
Probe firmwareV9 May7 2021; HW9.40, measuredVTref3.290V. Not proof all charger
functions survived earlier wiring. Firmware backup NOT obtained.
Evidence artifacts/kw520-jlink/20261031-identification.json; raw logs and
configs build/kw520-jlink-20261031/identity-protection.{cfg,log}.
No reset soldering required for identification now. Do not disable protection:
Artery documentation says removing access protection erases main flash/USD.

### 2026-10-31: offline vendor updater analysis

See docs/kw520-updater-analysis-20261031.md. UPLINK/BTLINK downloaded into ignored build directory; shared endpoint, Artery drivers and CRC table found. BTLINK framing/info command reconstructed and checked against isolated x86 routines in Unicorn. No target traffic, no KW520 firmware file or confirmed updater compatibility/readback. User reports no other visible ports. Internal UART/test pads remain hypothesis; identify board routing before any serial attempt.

### 2026-10-31: bounded live peripheral inventory

User authorized config-register investigation via existing J-Link. Two generic mem_ap sessions at50kHz, VTref3.291V; no halt/reset, peripheral writes, flash reads, erase or unlock. DEVICE_ID50020100 and FLASH_USD03fffffe unchanged. CRM CTRL00009283 CFG00000000 AHBEN00000014 APB2EN00000000 APB1EN00000000. GPIOA reads repeated28000000 across config and mux offsets; GPIOB/USART config zero. Clock-gated/reset-like register image is not a reliable runtime pin map or proof no UART exists. Stopped without enabling clocks or changing target. Need user observation of display/normal operation before further action. Evidence artifacts/kw520-jlink/20261031-peripheral-inventory.json and build/kw520-jlink-20261031/peripheral-stage{1,2}.{cfg,log}. Register layouts checked against official ArteryTek AT32F421_Firmware_Library gpio/usart/crm headers and CMSIS base addresses.

### 2026-10-31: single-register attempt also freezes UI

User reported menu recovery after reboot and explicitly authorized more bounded experiments despite risk. Reviewed matching Espressif OpenOCD mem_ap.c: runtime CPU state is synthetic, not a hardware-running guarantee. Six separate mdw count1 reads after init (DEVICE_ID, CRM AHBEN/APB2EN, GPIOA MODE/OTYPE/MUXL) returned plausible values; user then confirmed UI frozen again. No halt/reset command, peripheral writes, flash reads/writes/unlock/erase. Do not claim that single reads avoid the disturbance or that block increment alone caused it. Evidence artifacts/kw520-jlink/20261031-single-read-freeze.json. Next useful discriminating test after user power cycle: DAP-only connection with no mem_ap target and no target-memory access; require observed button response between stages. No further live access this turn after freeze confirmation.

### 2026-10-31: DAP-only isolation test executed

After user reported ready following requested reboot, ran dap-only-prepared.cfg: SWD50kHz, no target/mem_ap, init then DPIDR read and shutdown. ID2ba01477, VTref3.290V, exit0. No target memory access, halt/reset or flash command. DAP setup still writes debug transport registers. User button-response observation pending; do not infer recovery or freeze from ID alone. Evidence artifacts/kw520-jlink/20261031-dap-only.json and build/kw520-jlink-20261031/dap-only.log.

### 2026-10-31: DAP-only freeze confirmed; offline init audit

User reported immediate freeze during DAP-only trial and subsequently rebooted. No new live access after this reboot. Matching Espressif tag v0.12.0-esp32-20250707 arm_adi_v5.c dap_dp_init writes DP_CTRL_STAT CDBGPWRUPREQ|CSYSPWRUPREQ, waits for acknowledgments and enables CORUNDETECT. Therefore previous ID-only description was shorthand: this was not a raw DPIDR-only electrical transaction. Freeze cannot be attributed specifically to ID read. J-Link driver init calls jlink_reset(0,0), releasing reset lines, not an explicit target reset pulse; physical wiring still matters. Source copies saved in build/kw520-jlink-20261031/{arm_adi_v5.c,adi_v5_swd.c,jlink.c}. Next meaningful test requires audited raw SWD connection/DPIDR transaction omitting DP power-up (custom transport harness or modified tool), followed by separate power-up phase; do not simply repeat ordinary init. Read-protection interaction remains hypothesis, not established cause. Preserve original flash.

### 2026-10-31: raw SWD DPIDR experiment, no DP power-up

Built local libjaylink and raw-dpidr.c under build/kw520-jlink-20261031. Audited libjaylink open/close and swd_io; harness selects USB probe69401338, checks VTref3.0-3.5V, selects SWD50kHz, emits 56 ones + E79E16bits LSB-first +56 ones +8 idle +A5 read +38 input +8 idle (190 clocks). No DP write, AP access, CPU memory read, reset/power command or firmware operation. Dry run verified buffer; -Wall -Wextra -Werror build passed. One live invocation returned VTref3291mV, ACK1, DPIDR2ba01477, correct parity. Handle closed, no retry. UI response pending. Evidence artifacts/kw520-jlink/20261031-raw-dpidr.json and raw-dpidr.{c,log}. Do not equate successful ID read with running charger.

User confirmed menu remains responsive after the raw DPIDR trial. This is physical UI evidence for this exact limited sequence, not proof peripheral reads/debug power-up are safe. Difference from freezing OpenOCD init is established; specific causal operation remains unisolated.

### 2026-10-31: raw DP status read

User requested incremental experiments. Built raw-dp-status.c from successful raw DPIDR harness; adds exactly one read command0x8d at DP address4 (54 clocks), no DP/AP writes. DPIDR2ba01477 and DP_ADDR4=00000000, ACK1 and parity verified for both, VTref3290mV. Closed USB. UI observation pending; do not advance until received. Interpreted as CTRL/STAT assuming existing bank0; no SELECT write in this trial. Evidence artifacts/kw520-jlink/20261031-raw-dp-status.json.

### 2026-10-31: isolated debug power request

User confirmed raw status-read trial responsive. Next single mutation: raw-dp-debugpower.c requires initial DP address4 zero, writes DP CTRL/STAT10000000 (CDBGPWRUPREQ only), reads back30000000 (request+ack). All ACK/parity valid, VTref3291mV. No AP/CPU memory access, target reset, system power request, overrun enable or flash operation. Debug power request intentionally remains asserted after USB close; no automatic cleanup write. UI observation pending; await user before next stage. Evidence artifacts/kw520-jlink/20261031-raw-dp-debugpower.json.

### 2026-10-31: debug request set/clear trial

User confirmed prior debug-power-only experiment froze menu, then rebooted before clear-only test. Authorized repeat set-and-clear. raw-dp-powercycle.c (name refers to debug-domain request only, no target supply/reset command) executed: initial CTRL/STAT0 -> write10000000 -> status30000000 -> write0 -> status0. All ACK1/parity checks passed, VTref3291mV. USB closed. No AP/CPU access, flash or target reset. User UI recovery observation pending. Evidence artifacts/kw520-jlink/20261031-raw-dp-set-clear.json; raw logs/sources in build/kw520-jlink-20261031.

### 2026-10-31: frozen core is in HardFault lockup

User confirmed set/clear left UI frozen and authorized status reads while leaving it frozen. Generic OpenOCD mem_ap (no cortex_m target) read seven single words: DHCSR03090000, ICSR00000803, CFSR00021000, HFSR40000000, DFSR0 SHCSR0 DEMCR0. ARM CMSIS decode: S_LOCKUP1, S_HALT0, C_DEBUGEN0; exception3 HardFault active; FORCED1; STKERR and INVSTATE recorded. No normal debugger halt indicated. Fault flag ordering/root cause unknown; reads follow OpenOCD debug/system power reactivation so snapshot is not pre-attach evidence. DHCSR sticky RESET/RETIRE bits not proof of fresh reset/live progress. No reset/halt command, flash read/write or unlock/erase. Evidence artifacts/kw520-jlink/20261031-frozen-core-status.json and build/.../frozen-core-status.{cfg,log}. Original preservation boundary remains.

### 2026-10-31: AP ID without power requests

User requested investigation of memory access without debug power-up. Raw harness first read DPIDR2ba01477 and DP status0; wrote SELECT=f0 to select AP0 ID bank (DP bank0 remains), issued AP read addrC then DP RDBUFF. All ACK1/parity valid but both data zero, not prior powered ID24770011. No DP power request or CSW/TAR/DRW/CPU memory access, reset or flash operation. SELECT remainsf0. No further attempts; UI observation pending. Evidence artifacts/kw520-jlink/20261031-raw-ap-id-unpowered.json. This does not prove memory access impossible; next distinct hypothesis after UI confirmation is system-power-only versus debug-power requirement, not repeated blind accesses.

### 2026-10-31: system power alone also gives zero AP ID

User confirmed prior unpowered AP-ID trial UI OK. First system-only harness precheck stopped without writes because READOK40 set by prior AP read. Verified bit6 definition, allowed READOK in precondition; second invocation wrote CTRL/STAT40000000, readc0000040 (system req+ack, READOK; debug req clear), SELECTf0 then AP0 ID/RDBUFF both0, all ACK/parity valid. System request left asserted, USB closed. No debug-power request, CPU memory access, reset or flash. UI response pending. Evidence artifacts/kw520-jlink/20261031-raw-ap-id-systemonly.json.

User confirmed system-power-only trial leaves menu responsive. Current target DP system-power request remains asserted (40000000), debug request clear, SELECTf0. Raw ID and DP status reads, unpowered AP ID, and system-only AP ID each left menu responsive in observed trials; debug-power-only request froze UI and clearing it did not recover. System-only/unpowered AP ID returns0 rather than powered24770011. No usable memory-access route without debug power established; do not claim impossible or bypass proven.

### 2026-10-31: CSW also zero with system-only power

User authorized next bounded test. raw-ap-csw-systemonly requires existing statusc0000000 allowing READOK40; SELECT=0 then AP CSW read/RDBUFF ->0, final DP statusc0000040. All ACK/parity valid. No power request changes, CSW writes, TAR/DRW or CPU memory access, reset/flash. Actual zero CSW versus gated/masked readback not distinguishable; does not establish usable MEM-AP. SELECT now0, system request remains set, debug request clear. UI observation pending. Evidence artifacts/kw520-jlink/20261031-raw-ap-csw-systemonly.json.

### 2026-10-31: public protected-readout research

User confirmed CSW-read trial menu OK. Researched exact AT32F421C8T7 and similar targets online; see docs/kw520-readout-research-20261031.md. Exact-chip EMFI erase-suppression success in Schink et al TCHES2024; voltage glitch attempts unsuccessful for421 in that paper. RT890 forum reports updater/payload UART extraction on same MCU; product-specific and not independently verified here. STM32F0 RP2040 SWD race PoC exists but no421 support established. No live hardware actions this step.

### 2026-10-31: updater-path follow-up

Found active JSON metadata endpoint47.251.40.156/HandheldDeviceUpdate/OSSService.php in UPLINK; confirmed POST helper and metadata fields statically. Incomplete KW520/empty-subtype queries returned code101 missing parameter, old server unavailable. Exact device identity tuple unknown; async question pending for model/hardware/software screen text. External original4MiB scan found no aligned normal Cortex-M vector candidate. No target access/writes. Details docs/kw520-updater-analysis-20261031.md follow-up.

### 2026-10-31: user supplied device version screen

Reported SW1.0.7 HW1.2.0. Serial not sent to server or written into these notes. Bounded model/HW tuple test KW520/1.2.0, POST getlist=yes returned code101 failure. Display-to-protocol mapping remains unknown. No hardware traffic or firmware writes.

Regular metadata POST without getlist for same KW520/1.2.0 returned code100 but all rom/fls/other lists empty. No download URL; do not claim server recognizes KW520 or other.ver1.0.0 is target firmware.

### 2026-10-31: user clarified SPI dump as extraction attack surface

Goal is analyze external data to induce original MCU firmware to disclose protected program, not merely another SPI reader or assets-only patch. Rechecked full reference hash and1296 resource records; length range3..113, no early NUL, no percent bytes. Non-FF sectors only0..bfff,380000..381fff,383000..383fff. See docs/kw520-spi-parser-research-20261031.md. Length/offset/format parsing and SPI as output sink are hypotheses, no vulnerability established. No live target action, no malicious/malformed resource flashed. RAM execution alone must not be represented as protected flash readout permission. Existing SWD-to-SPI bridge remains unproven transport prerequisite.

### 2026-10-31: extraction plan and deeper SPI structure analysis

Added docs/kw520-jlink-spi-extraction-plan.md with staged gates from offline dump analysis through J-Link/SPI transport, reversible parser tests and independently verified internal-firmware readout. Added read-only tools/analyze_kw520_spi.py and generated ignored build/kw520-jlink-20261031/spi-deep-analysis.json from the preserved reference; size/hash match. New verified structure: byte3200 declares8 active languages, followed by sparse19-byte slots indexed by IDs3,4,5,6,7,8,10,14. Each slot is language ID plus three `(u32be relative table,u16be count)` pairs. Class1 has162 ordinary strings. Class2 has one7-byte `(u24be DTC code,u32be string pointer)` entry and resolves P0000 in every language. Class3 count is0 and common relative offset821e; do not infer active data. New integrity result: CRC-8/SAE-J1850 (poly1d initff xoroutff, non-reflected) validates record lengths60 at1000/2000,20 at1280/2280,10 at380000,8 at381000, and52 for all four history records. Updated docs/resource-format.md and added docs/kw520-spi-deep-analysis-20261031.md. No target traffic or flash mutation. No compressed/archive/executable magic or Cortex-M vector found; no SPI-resident firmware established. Best first physical parser test remains a same-bank valid pointer redirection, only after stable J-Link SPI read/restore transport is proven.

### 2026-10-31: corrected J-Link voltage reference resets debug conclusions

User reported the voltage-reference connection had been on the wrong point and likely shorted toward ground; the apparatus now powers its display without 220 after correction. Treat all earlier freeze/HardFault and DP/AP behavior as observations under faulty wiring, not evidence of AT32F421 corrected-wiring behavior or read-protection response. USB re-enumerated as bus002/device077 and initially lacked the user ACL; a temporary nichlas rw ACL was added through pkexec. Reused audited raw-dpidr harness only: VTref3291mV, ACK1, DPIDR2ba01477, parity valid, exit0. No DP/AP write, power request, reset, memory or flash access. USB closed. Evidence artifacts/kw520-jlink/20261031-raw-dpidr-corrected-wiring.json. Next step is to restart the isolation ladder from corrected baseline, checking menu response after each bounded stage.

### 2026-10-31: stable 3.3 V reproduces debug lockup and identifies SPI2 pins

User disconnected target-power pin19 and supplied stable external3.3V; corrected ladder at VTref3290–3293mV: raw DPIDR/status, unpowered AP ID, system-only AP ID and system-only CSW all left menu responsive. Transition CTRL/STAT c0000040 -> write50000000 -> f0000040 froze menu reproducibly. Corrected frozen snapshot again shows DHCSR03090000 S_LOCKUP, active HardFault3, HFSR40000000 FORCED and INVSTATE; one corrected snapshot CFSR00021000 had STKERR, later inventory CFSR00020100 had IBUSERR, so exact fault subtype varies. Clearing debug/system requests does not recover; full target power cycle does. DP sticky flags cleared with ABORT1e before cleanup; final CTRL/STAT00000040. A single read-only corrected-power inventory found CRM APB1EN00004010 with SPI2 clocked, SPI1 disabled; SPI2 CTRL100000357 decodes enabled master mode3 divisor8 MSB software-CS. PB13/14/15 are AF0 matching datasheet SPI2 SCK/MISO/MOSI; PB12 hardware-CS is analog; PB11 is adjacent GPIO output high and strongest software-CS candidate but unproven until continuity/scope or controlled observation. Evidence artifacts/kw520-jlink/20261031-corrected-power-spi-inventory.json. No target-memory write, halt/reset, internal/external flash operation, erase or unlock. Next: power-cycle target; prove PB11 to EN25Q32 nCS before GPIO writes, and test bounded SRAM write/restore to qualify an indirect SPI bridge.

### 2026-10-31: corrected-power SRAM write/restore passes

After cold power cycle, clean baseline VTref3291mV DPIDR2ba01477 CTRL/STAT0. OpenOCD generic mem_ap debug activation locked original firmware as expected. Two full SRAM reads0x20000000+0x4000 were byte-identical, SHA256254a6cbf37cb7d4a9e3d3518bbd050b5e6bc85413fb97fc76f8663fec8f1b90c. Longest zero run200009fc..2000236b length6512. At aligned200016b4: original0 -> writea55a3cc3 -> readbacka55a3cc3 -> restore0 -> readback0, PASS. This proves stable protected-state SRAM read and one-word MEM-AP write/restore, not SRAM execution. Cleaned sticky DP via ABORT1e then both power requests; final CTRL/STAT00000040. Evidence artifacts/kw520-jlink/20261031-corrected-power-sram-write-restore.json. Next physical gate with target fully unpowered: continuity EN25Q32 pin1 CS# to MCU PB11/pin22. If confirmed, build direct MEM-AP SPI2 JEDEC transaction before attempting any external-flash write.

### 2026-10-31: RAM-based internal firmware read bridge prepared, not run

The preferred route is now direct internal-flash extraction rather than an
SRAM-to-SPI bridge. `tools/kw520_ram_probe/probe.S` is a 308-byte Cortex-M4
helper linked at20001000. It reports through a mailbox at20001700 and can either
probe two words at08000000 or copy at most256 words into a1KiB SRAM buffer. Its
source range is hard-limited to08000000..0800ffff and it contains no internal or
external flash unlock/program/erase routine. Reproducible Makefile build passes;
`build/kw520-ram-probe/probe.bin` SHA256 is
abc47fdb82ec7dd17fdf6e11166e1973341cb092382d2c60d6a2149a460f5663.

Prepared but not executed live gates under build/kw520-jlink-20261031:
cortex-halt-gate, ram-probe-load-gate, ram-probe-exec-gate,
ram-probe-flash-gate, then ram-probe-full-dump. The stages deliberately separate
core halt, SRAM load/readback, SRAM alive mailbox, two-word protected read, and
64x1KiB acquisition. Backup/restore covers20001000+1400, including code,
mailbox, transfer buffer and possible fault stack; VTOR is also restored. The
full acquisition must be cold-cycled and repeated under a second tag, then
`tools/kw520_ram_probe/assemble_dump.py` requires exact64KiB layout and can
require equality to the independent first read. Synthetic64-chunk assembly and
comparison passed. Detailed plan: docs/kw520-ram-read-bridge-20261031.md.

This does not yet prove the locked-up core can be halted and redirected, SRAM
code can execute, or protected internal flash is readable. Target was last
requested fully unpowered; do not run a live gate until the user explicitly
reconnects stable external3.3V and J-Link. Run only the halt gate first and wait
for its result before any SRAM write.

Gate1 was subsequently run with user-reported external3.3V backfeed only and
J-Link pin19 not supplying the target. Raw precheck: VTref3290mV,
DPIDR2ba01477, valid parity. Cortex-M4 halt then passed at50kHz: target halted,
PC0, SP20003b90, XPSR20000003 (exception3 HardFault), DHCSR00030003. No SRAM
load, internal-flash read, reset, unlock, erase or program operation. Evidence:
artifacts/kw520-jlink/20261031-ram-probe-halt-gate.json. The debug halt boundary
is now proven. Next distinct gate is backup20001000+1400, load the308-byte
helper and dump/readback it while remaining halted; compare offline before any
attempt to execute it.

After user power-cycled, gates2–4 ran at VTref3290mV. Gate2 backup
20001000+1400 SHA256 258040a55efc585da1d0d85ce7741ca0b9279d2a1e1006b429482cced742bf89;
308-byte helper load/readback exactly matched SHA256
abc47fdb82ec7dd17fdf6e11166e1973341cb092382d2c60d6a2149a460f5663.
Gate3 proved SRAM execution: PC20001066, MSP20002300, mailbox magic4b575250,
state1. Gate4 completed a two-word read at08000000 without fault, state11/count2,
but returned0,0, not plausible vectors. SRAM restoration matched all5120 bytes
and VTOR0 was restored. Cleanup used DP_ABORT1e, released debug then system
requests; final CTRL/STAT00000040. No full dump, unlock, erase or programming.

This exactly matches official AT32F421 RM v2.05 section5.5.1/table5-5: FAP
forbids main-flash reads in debug mode or while booted/executing from SRAM or
boot memory; only main-flash execution retains read permission. The direct RAM
firmware bridge is therefore proven as transport/execution but blocked as a
protected-flash disclosure. `ram-probe-full-dump.cfg` now refuses execution.
Do not try aliases or accept a64KiB zero image. Next non-destructive work should
target a disclosure while original main-flash code runs (external SPI parser/
updater path), or a separately planned fault-injection experiment. FAP disable
remains prohibited because it mass-erases the main flash. Evidence:
artifacts/kw520-jlink/20261031-ram-probe-gates-2-4.json.

Prepared a separate512-byte read-only SPI2 helper after direct flash reads were
blocked. It requires PB11 GPIO-output-high, PB13/14/15 AF, SPI2 CTRL1=357 and
TDBE before accepting command1; the only transmitted sequence is9f ff ff ff,
with expected EN25Q32 ID1c3016. No06/write-enable, erase, program or status-write
exists. Build SHA256 d445ffa3a7073b44b93a5010687a86fd543c0b1c66baab3bc2e35085041c5437.

First live SPI attempt used separate OpenOCD load and execution sessions. Load
readback matched all512 bytes; backup20001000+1400 SHA256
f2470c33bfe45f01c94090d3ad847249e64c0c0312b2a78e3be48a5bcbc84d59.
On execution the helper correctly refused with statee1: captured GPIOB config
and SPI2 CTRL1 were reset values; direct MEM-AP inspection confirmed the same.
PB11 was not toggled and no9f or any SPI command was sent. SRAM restoration was
bit-identical. DP cleanup final CTRL/STAT00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-probe-multisession-refused.json.

The distinct next gate is prepared as spi-probe-single-session.cfg: after a
cold target start it checks the live original register image before writes,
then performs backup/load/helper-precondition/one JEDEC transaction/restore
without closing J-Link between stages. Host and helper both refuse if the live
PB11/SPI2 state is absent. User must cold-start again before running it.

The user cold-started and the single-session gate ran at VTref3291mV. Live
preconditions passed: GPIOB CFGRab41417f ODT908, SPI2 CTRL1357 STS2, AHBEN
004e0015, APB1EN4010. The512-byte helper readback matched; alive magic/state
4b575350/1. Exactly9f ff ff ff was sent with PB11 as candidate CS; response was
ff ff ff and helper state12, not EN25Q32 ID1c3016. No write-enable, status-write,
program or erase command exists or was sent. PB11 must not be treated as proven
CS and no alternate GPIO should be tried blindly.

VTOR08000000 was restored. Backup/readback was exact through200022ff, which
contains all helper code/mailbox and below-stack memory. OpenOCD reported an
external reset;28 later differences were only20002386..200023f4, above helper
stack top20002300, consistent with original live firmware updating SRAM after
reset rather than helper writes. DP cleanup final CTRL/STAT00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-probe-pb11-jedec.json. Next physical gate is
power-off continuity from EN25Q32 pin1 /CS to MCU LQFP48 candidate pins45/PB8,
39/PB3 and22/PB11. Runtime GPIOB showed PB3, PB8 and PB11 as the three high
GPIO outputs; package geometry makes PB8/PB3 more plausible than PB11, but only
continuity is acceptable evidence.

User continuity measurement then reported EN25Q32 pin1 /CS appears connected to
MCU LQFP48 pin29, which is PA8 per the official pinout. Reworked the helper to
use GPIOA PA8 only, while retaining PB13/14/15 and SPI2 checks. New binary is
520 bytes, SHA256 085b14605d6bdd656a3d9153000429a795d0d32bcaaaf75d687d8d4cbc531190.
Both host and helper require PA8 GPIO-output-high before one9f transaction;
timeouts/faults release PA8 high. Prepared one-session config
spi-probe-pa8-single-session.cfg with separate evidence filenames. This has not
yet run. Ask for measured resistance if possible and require a new normal cold
start before executing.

The user confirmed 0 ohms and the one-session PA8 gate then succeeded. Live
registers were GPIOA CFGR6951ffff, GPIOA ODT00009d00, GPIOB CFGRab41417f,
SPI2 CTRL100000357 and STS00000002. The SRAM helper returned
magic4b575350/state11 and exact EN25Q32 JEDEC ID1c3016. Helper readback matched
its 520-byte SHA256
085b14605d6bdd656a3d9153000429a795d0d32bcaaaf75d687d8d4cbc531190.
VTOR was restored to08000000, the helper-touched SRAM below the temporary stack
was restored, and raw-DP cleanup ended at CTRL/STAT00000040. No06/write-enable,
program, erase, status-write, internal-flash command, unlock or protection
change occurred. Evidence:
artifacts/kw520-jlink/20261031-spi-probe-pa8-jedec.json. Next gate: cold-cycle,
then one uninterrupted session using fixed opcode03 to read only 16 bytes from
external offset0 and compare exactly with the preserved original dump before
allowing any larger read.

Offline preparation for that gate is complete. `tools/kw520_spi_probe` now
builds a 732-byte helper with SHA256
d6eb6cfe19bd440f182718842834e727fbbefe82bba4a4c7d1011eb33b815547.
Command2 contains the fixed SPI opcode03 only, validates a 24-bit source range
inside the 4 MiB EN25Q32, limits each request to1..8192 bytes and returns data
at20001800. It has no host-selected opcode and still contains no flash-mutating
instruction. `spi-read16-pa8-single-session.cfg` backs up/restores the entire
20001000..20003fff work window, re-runs the JEDEC gate and requests only
offset0+16 bytes. The preserved original dump still hashes d369a860...41e2;
its first16-byte comparison hash is
e37500c9d94cae6741a39e82aeb3f2cca0a7c942818bb50700f8b308a4a5d2c0.
Do not run until a new cold target power cycle after the successful JEDEC
session.

First 16-byte gate attempt was safely inconclusive before any SPI transaction.
VTarget3290mV and all live preconditions passed; the 732-byte helper readback
was exact and reached alive magic/state4b575350/1. After host command1,
OpenOCD resume left state at1 with zero JEDEC words, so neither9f nor03 was
confirmed executed and no read output was created. The complete12288-byte
SRAM work window restored bit-identically, SHA256 both before/after
494d6bbb24afa6bea88bff95b38790e17c58ad3662cf45a09939c1ec2a7194c5;
VTOR08000000 restored and DP cleanup ended00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-read16-attempt1.json. Config now explicitly
sets PC to command_loop200010d3 plus Thumb xPSR before both command resumes to
avoid OpenOCD's stale run state after its reported external-reset recovery.
Require another cold target power cycle before retry.

Second attempt proved the failure mode more narrowly. At VTarget3288mV all
preconditions and helper readback passed; after explicitly setting command1,
PC200010d3 and Thumb xPSR, the halt still showed PC at command_loop200010d2,
state1 and command1. Thus the protected core executed no instruction after its
second resume. Again neither9f nor03 was confirmed, no output was created, the
full12288-byte work window restored bit-identically with before/after SHA256
a2d61aaa65476add5acca200eda01b774deadc9a23777e9aaf9844bc4c046ca5,
VTOR restored and DP ended00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-read16-attempt2.json.

Reworked the helper to avoid every second resume. New 760-byte SHA256 is
0f3656c859bea2bf139b4dcf28adf37e7fdca82cef0d56393666b1d9c7a3aac7.
Preloaded command3 is preserved at initial entry only if source=0 and length=16;
that single core run performs JEDEC, requires1c3016, branches directly to fixed
opcode03 read and collects exactly16 bytes before spinning. Updated config
preloads those exact values and makes only the initial resume, then validates
magic/state21/command0/ID/completed16. Require a new cold target power cycle
before this third attempt.

Third attempt showed OpenOCD resume itself is now unreliable even on initial
entry: all live preconditions and exact helper readback passed, but after the
single resume magic/state remained0, preloaded command3 remained3 and no SPI
operation or output occurred. Full12288-byte SRAM restore was bit-identical,
before/after SHA256
ac93da13b83ffa5a5372158aaeb38a9d75ad07794e1b1f0a34d20ef0c866cf03;
VTOR restored and DP ended00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-read16-attempt3.json.

Prepared a strictly non-SPI run-control qualification
`spi-direct-run-gate.cfg`. It preloads command0, then uses architectural
DHCSR/DCRDR/DCRSR directly: halt A05F0003, require S_HALT+S_REGRDY, write
MSP/PSP/CONTROL/xPSR/PC with REGWnR, run A05F0001 once, halt directly, and
require only helper magic/state1/command0. It cannot issue9f or03 because the
command remains zero. This direct-control gate must pass after another cold
cycle before adapting the same sequence to command3.

First direct-control gate remained SPI-free and safely inconclusive. At
VTarget3290mV command stayed0; DHCSR before/after was00030003
(S_HALT+S_REGRDY and C_HALT+C_DEBUGEN), but helper magic/state stayed0. Full
SRAM restored bit-identically, before/after SHA256
1d2b24d0b13f90e157b4ab616a56f720357018df760dfe0c4dd481a84bb52cfe;
VTOR restored and DP ended00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-direct-run-attempt1.json.

Strengthened the still-command0 gate: each DCRSR transfer now gets a delay and
S_REGRDY poll, then MSP/PSP/special/xPSR/PC are independently read back and
must equal20003f00/20003f00/0/01000000/20001040. After A05F0001 it samples
DHCSR at5ms and proceeds only if S_HALT really cleared. This discriminates a
failed register transfer, ignored run write, and immediate post-run lockup.
OpenOCD periodic target polling is disabled after live validation so its cached
halted state cannot interfere with the direct DHCSR run window.
Require another cold target cycle before running it.

The strengthened command0 gate refused before run and exposed a timing/reset
problem. Core readbacks were all the stale final DCRDR value20001040 instead of
MSP/PSP/special/xPSR/PC; DHCSR changed from00030003 stable halt to01090001
(not halted, lockup) without the config issuing the verified run request.
Helper magic remained0 and no SPI was possible. Full12288-byte SRAM restored
bit-identically with before/after SHA256
3e3f6370755ff90db7b9b261cb4d31ad8090bf0da57453abbb60f3b9a2beb988;
DP ended00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-direct-run-attempt2.json.

Prior full backups show the helper code768, mailbox128 and buffer16 windows
were consistently zero and stable; only high active-stack data varied. Reduced
the time before core-register setup by replacing the12288-byte backup and
pre-run helper dump with exact backups of code768 + mailbox128 + buffer16 +
64 bytes below the temporary stack, total976 bytes. All four exact windows are
restored and independently read back afterward; helper760-byte readback was
moved after the run/refusal. Command remains0 and the next gate still cannot
perform SPI. Require a cold cycle before retry.

The minimal-window command0 gate passed completely. At VTarget3290mV core
registers read back exactly MSP/PSP20003f00, special0, xPSR01000000 and
PC20001040. DHCSR transitioned00030003 halted ->01010001 running with S_HALT
clear ->01030003 directly halted. Helper returned magic4b575350/state1/command0,
so no SPI occurred. Its 760-byte readback matched SHA256
0f3656c859bea2bf139b4dcf28adf37e7fdca82cef0d56393666b1d9c7a3aac7.
Code/mailbox/buffer/stack windows all restored bit-identically and DP ended
00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-direct-run-qualified.json.

Prepared `spi-direct-read16-gate.cfg` by keeping that exact qualified timing,
run control, core readback and four-window restoration, but preloading the
reviewed fixed command3/source0/length16. It will dump output only if JEDEC is
1c3016, state21, completed16 and command cleared. No larger read or mutating
opcode is possible. Require a fresh cold cycle before running it.

The direct 16-byte physical gate passed end-to-end. At VTarget3290mV all core
registers were exact; DHCSR was00030003 halted,01010001 running,01030003
direct-halted. Helper returned magic4b575350/state21/command0, JEDEC1c3016 and
completed16. Output offset0+16 SHA256 was
6e55de265faea5577dae4d908b9ffb2a6c7cd736f49bbfbc04225f74c1b6c73b.
It intentionally differs from factory-original d369a860... because the charger
contains the previously installed EutherCharge package. The16 bytes match
exactly both `dumps/readback/kw520-after-euthercharge-2026-10-18.bin` and
`build/euthercharge-kw520-1.0.1-full.bin`, whose full4MiB SHA256 is
4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329.
Helper readback matched; code/mailbox/buffer/stack all restored bit-identically;
VTOR08000000 restored and DP ended00000040. No mutating command exists or was
sent. Evidence:
artifacts/kw520-jlink/20261031-spi-direct-read16-qualified.json. This physically
qualifies the read-only J-Link -> SRAM helper -> PA8/SPI2 -> installed EN25Q32
data path, not internal protected main-flash readout.

Prepared the next read-only gate without transferring4MiB over SWD. Helper
command4 first requires JEDEC1c3016, then issues only03+address0, reads exactly
0x400000 bytes continuously and computes reflected CRC-32B polynomialedb88320
with initial/final xorffffffff. Progress is published each4096 bytes and final
CRC stored at mailbox+34; expected installed-image CRC is268f3bd7. New helper
is972 bytes SHA256
be2b49d68933a98a54471f9494be585847495a974311ad1d439d63d7ba0d0246.
`spi-direct-crc32-full-gate.cfg` retains qualified direct run control and exact
window restoration, waits at most40 seconds and accepts only state41,
completed400000, correct ID and CRC. This gate is prepared but not physically
run; require a new cold cycle.

First full-CRC physical attempt was stable but hit only the host's fixed40s
wait limit. VTarget3291mV, exact core registers, JEDEC1c3016, helper
magic4b575350/state40/command4 and completed1703936 bytes proved continuous
progress with no watchdog/reset. CRC was correctly not finalized or accepted.
All exact SRAM windows restored bit-identically, helper readback matched
be2b49d6...d0246, VTOR restored and DP ended00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-crc32-full-attempt1.json. Only the host poll
limit is now increased from40 to130 seconds (520x250ms); helper binary, read
opcode, bounds and expected CRC268f3bd7 are unchanged. Require cold cycle.

The130-second repeat stopped at1699840 bytes, essentially the same point, proving
the first interpretation wrong. A same-power read-only post-stall diagnostic
found CRM_CTRLSTS2c000000 with WDT reset bit29 set and WWDT bit30 clear; WDT
post-reset DIV0/RLDfff and WWDT defaults were captured. Thus the independent
WDT, not host timeout, stops the CRC. All SRAM windows again restored exactly
and DP ended00000040. Evidence:
artifacts/kw520-jlink/20261031-spi-crc32-full-attempt2-watchdog.json.

Official Artery driver defines WDT base40003000 and counter reload as only
WDT_CMD=aaaa, with no unlock required. Command4 now refreshes once at entry and
every4096 bytes of actual SPI progress, records refresh count at mailbox+38,
and never writes WDT DIV/RLD or unlock. If progress stops, refresh stops and WDT
protection remains. New helper is996 bytes SHA256
5b55a03cdd89444487622d5ab4338882a406f844ffe06135b70765e64286aa71.
Full gate now additionally requires exactly1024 refreshes and helper readback
size3e4. Prepared but not physically run; require cold cycle.

Full external-flash fingerprint then passed with bounded WDT refresh. At
VTarget3293mV core registers were exact and DHCSR transitioned00030003 ->
01010001 ->01030003. Helper returned magic4b575350/state41/command0,
JEDEC1c3016, completed4194304, exactly1024 refreshes and CRC-32B268f3bd7,
matching the known installed EutherCharge4MiB image. Helper996-byte readback
matched SHA256
5b55a03cdd89444487622d5ab4338882a406f844ffe06135b70765e64286aa71;
all four SRAM windows restored bit-identically, VTOR restored and DP ended
00000040. Only SPI9f/03 occurred; WDT writes were reload-keyaaaa only, with no
unlock/divider/reload-config write. Evidence:
artifacts/kw520-jlink/20261031-spi-crc32-full-qualified.json.

This is physical end-to-end proof of the read-only J-Link/SRAM/SPI transport and
a full-device non-cryptographic fingerprint plus prior exact16-byte match for
the installed external flash. It is not a full bulk readback and does not expose
the AT32F421's FAP-protected internal main flash. Cold-cycle target before normal
charger operation or any distinct next internal-flash/oracle experiment.

### 2026-10-31: reversible physical external-resource parser probe passed

The installed EN25Q32(A/B) starts at status18 and fixed-block protection
readbackff. Commands39/36 did not change that protection; official flashrom
source instead identified EN25Q32(A/B) unlock as clearing BP bits with WRSR.
The fixed status-only roundtrip physically passed18 ->1a ->00 ->02 ->18 while
sector003000 stayed CRC32B f5c23372. The final mutation helper then accepted
only bytes6d65 at003899, original sector CRCf5c23372 and explicit ARM1. It
cleared status to00, issued only fixed Page Program payload2525, verified bytes
and patched sector CRC7985c2f6, then restored status18. Helper readback and all
qualified SRAM/VTOR restoration checks passed. Evidence:
`artifacts/kw520-jlink/20261031-spi-format-probe-programmed.json`.

On a physical cold start the LCD displayed `Huvud%%ny`, exactly the literal
prediction and not the printf-like `Huvud%ny`. This proves original firmware
consumes this external language payload and renders percent bytes literally;
it is not a format-string disclosure route. Evidence:
`artifacts/kw520-jlink/20261031-spi-format-probe-physical-observation.json`.

The fixed recovery helper accepted only patched CRC7985c2f6 plus an
independently qualified 4096-byte restore buffer CRCf5c23372. It cleared status,
erased only sector003000 (erased CRCf154670a), programmed exactly16 pages,
verified final CRCf5c23372 and restored status18. Helper/SRAM/VTOR readbacks
all passed. The user then performed a normal cold start and confirmed working
`Huvudmeny`. The apparatus is therefore restored, not left patched. Evidence:
`artifacts/kw520-jlink/20261031-spi-format-probe-restored.json` and
`artifacts/kw520-jlink/20261031-spi-format-probe-cycle-complete.json`.

Current evidence level is C plus narrow D: external transport, fixed-sector
mutation/restoration and controlled payload consumption are physical facts.
No external out-of-bounds read, write sink, code execution under original
firmware, or protected internal-flash disclosure exists yet. Do not repeat
percent-format probes on this literal path. Next useful parser discriminator is
a separately generated, fixed and recoverable same-bank pointer redirection,
then cross-bank pointer or conservative declared-length shortening.

### 2026-10-31: same-bank pointer probe prepared; recovery no-op qualified

The next fixed experiment redirects English-table entry1 at003604 from
relative pointer00000692 (`Huvudmeny` record003892) to existing entry2 pointer
0000069e (`Testa` record00389e). Only byte003607 changes92->9e; payloads and
length prefixes remain untouched. Because this includes0->1 transitions, the
forward helper uses the already qualified fixed-sector erase/program engine.
Its distinct KWPD/ARM5 gates require original target CRCf5c23372, exact SRAM
payload CRC14b0524b and final CRC14b0524b. Generated pointer-sector SHA256 is
e2a360307ecdf51373df959d68b3b8446aba39fc7aa69d7da863c3d4e52a0028;
forward helper SHA256 is
26bf5766a54891df9716b25b7771a512bc6a3c98105adc603b40dfa232c36a79.
No physical forward write has occurred yet.

A separate KWRO/ARM6 recovery helper accepts only exact patched target
CRC14b0524b, original SRAM payload CRCf5c23372 and final CRCf5c23372. Its
physical no-op qualification on the still-original sector passed at
VTarget3.291V: state42, JEDEC1c3016, status18, protectionff, buffer/target
CRCf5c23372, pages0, no erase/final CRC/status change, spi_error0. Helper
readback matched SHA256
9b2df2c5e404b2a6c258869af7496f83ca086dc45d2be080d2ea07352ddfe744;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261031-spi-pointer-restore-noop-qualified.json`.
Cold-start target normally before running the distinct forward pointer probe.

After that cold start the fixed KWPD/ARM5 forward run passed physically at
VTarget3.290V. It required JEDEC1c3016, status18, protectionff, input buffer
CRC14b0524b and live original target CRCf5c23372. It then verified erased CRC
f154670a, programmed exactly16 pages, verified final sector CRC14b0524b and
restored status18; state41, spi_error0, cleanup0. Helper readback matched
SHA256 26bf5766a54891df9716b25b7771a512bc6a3c98105adc603b40dfa232c36a79;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261031-spi-pointer-probe-programmed.json`. The target
is halted after the accepted session and the pointer patch is currently live.
Next required action is one normal cold start and an exact observation of the
main-menu title. Expected title is `Testa`. Do not run any other mutation before
that observation; afterward use only the already no-op-qualified ARM6 pointer
restore helper.

The user then cold-started the physical charger and reported that the main-menu
title displayed exactly `Testa`, matching the sole table-pointer redirection.
No string payload or length prefix was changed. This physically proves that
original firmware follows ordinary-string table entry1 as a relative
external-flash pointer to the existing same-bank record at00389e. It does not
yet prove cross-bank access, out-of-bounds access, a memory disclosure, or
internal-flash access. Evidence:
`artifacts/kw520-jlink/20261031-spi-pointer-probe-physical-observation.json`.
The pointer patch is still live. The only next target action is the fixed
KWRO/ARM6 pointer restore; do not run another parser mutation first.

The fixed KWRO/ARM6 restoration then passed physically at VTarget3.291V. It
accepted only pointer-patch target CRC14b0524b and original buffer CRCf5c23372,
verified erased CRCf154670a, programmed exactly16 pages, verified final sector
CRCf5c23372 and restored status18; state41, spi_error0, cleanup0. Helper
readback matched SHA256
9b2df2c5e404b2a6c258869af7496f83ca086dc45d2be080d2ea07352ddfe744;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261031-spi-pointer-probe-restored.json`. The target is
halted after the accepted session. Final required gate: normal cold start must
show working `Huvudmeny` before declaring the complete cycle closed.

The user performed that final normal cold start and confirmed working
`Huvudmeny` with responsive buttons. The same-bank pointer-probe cycle is
therefore closed: original `Huvudmeny` -> pointer-only patch -> physical
`Testa` -> exact sector/status restore -> physical working `Huvudmeny`.
Evidence:
`artifacts/kw520-jlink/20261031-spi-pointer-probe-cycle-complete.json`.
Evidence level D is now physical for same-bank pointer following. Cross-bank
pointer interpretation, out-of-bounds behavior and internal-flash disclosure
remain unproven. The next discriminating parser experiment is a fixed valid
cross-bank pointer, with a separately CRC-gated restoration pair; do not reuse
the same-bank CRC helpers for a different sector image.

### 2026-10-31: valid cross-bank pointer probe prepared; recovery qualified

The next fixed experiment redirects English-table entry1 at003604 from
relative pointer00000692 (`Huvudmeny`, record003892) to the existing Français
entry1 relative pointer000013e9 (`Menu principal`, record0045e9). Only pointer
bytes003606..003607 differ; payloads and length prefixes remain untouched.
Patched sector CRC is b29ee7d1 and SHA256 is
3efd9a22de5e71a4e864cb712058c21180eb660eedeba50718969b506559c72d.
The KWCB/ARM7 forward helper accepts only original target CRCf5c23372, exact
buffer CRCb29ee7d1 and final CRCb29ee7d1; SHA256
75d9cf3a479d35aacbcbec46bb8a46b43e3900fe354446150892bc3a7218811a.
No physical forward write has occurred yet.

The separate KWCR/ARM8 recovery helper accepts only cross-bank target
CRCb29ee7d1, original buffer CRCf5c23372 and final CRCf5c23372. Its physical
no-op qualification on the still-original sector passed at VTarget3.290V:
state42, JEDEC1c3016, status18, protectionff, buffer/target CRCf5c23372,
pages0, no erase/final CRC/status change and spi_error0. Helper readback matched
SHA256 c2efac5633809ad1347cbe01e554d8b15789e21aeb18796b7770875e95982842;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261031-spi-crossbank-restore-noop-qualified.json`.
Cold-start target normally before the distinct ARM7 forward probe.

After that cold start the fixed KWCB/ARM7 forward run passed physically at
VTarget3.291V. It required JEDEC1c3016, status18, protectionff, buffer
CRCb29ee7d1 and live original target CRCf5c23372. It verified erased CRC
f154670a, programmed exactly16 pages, verified final sector CRCb29ee7d1 and
restored status18; state41, spi_error0, cleanup0. Helper readback matched
SHA256 75d9cf3a479d35aacbcbec46bb8a46b43e3900fe354446150892bc3a7218811a;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261031-spi-crossbank-probe-programmed.json`. The target
is halted and the cross-bank pointer patch is live. Next action: normal cold
start and exact title observation; expected `Menu principal`. Then use only the
already qualified KWCR/ARM8 restoration helper.

The user cold-started the physical charger and reported the exact main-menu
title `Menu principal`. No target payload or length prefix was changed. This
physically proves that original firmware follows an ordinary-string relative
pointer from the active English/Swedish table across the language-bank boundary
to the valid Français record at0045e9. The pointer is not restricted to its
source bank. This is still an in-range external-SPI read, not out-of-bounds or
protected internal-flash disclosure. Evidence:
`artifacts/kw520-jlink/20261031-spi-crossbank-probe-physical-observation.json`.
The cross-bank patch remains live; run only the fixed KWCR/ARM8 restore next.

The fixed KWCR/ARM8 restoration then passed physically at VTarget3.290V. It
accepted only cross-bank target CRCb29ee7d1 and original buffer CRCf5c23372,
verified erased CRCf154670a, programmed exactly16 pages, verified final sector
CRCf5c23372 and restored status18; state41, spi_error0, cleanup0. Helper
readback matched SHA256
c2efac5633809ad1347cbe01e554d8b15789e21aeb18796b7770875e95982842;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261031-spi-crossbank-probe-restored.json`. Target is
halted. Final required gate is a normal cold start showing working
`Huvudmeny` before closing the cross-bank cycle.

The user performed that final normal cold start and confirmed working
`Huvudmeny` with responsive buttons. The cross-bank cycle is closed:
`Huvudmeny` -> pointer-only cross-bank patch -> physical `Menu principal` ->
exact sector/status restore -> physical working `Huvudmeny`. Evidence:
`artifacts/kw520-jlink/20261031-spi-crossbank-probe-cycle-complete.json`.
Level D now includes valid relative pointer following both within and across
language banks. The pointer is not source-bank bounded. This does not establish
invalid/out-of-range pointer behavior or internal-flash disclosure. Next safe
parser discriminator is a fixed shortening of one declared allocation/length;
do not combine it with a pointer change or attempt a length extension first.

### 2026-11-01: conservative declared-length shortening prepared

The next fixed probe changes only the main-title record length at003892 from
big-endian000a to0008. Payload `Huvudmeny\0` at003894 remains byte-exact. The
only changed byte003893 is0a->08, a NOR-safe1->0 transition, so the KWLN/ARM9
forward helper uses one fixed two-byte Page Program and no erase. It requires
original sector CRCf5c23372 and final CRC5e1e3b15; helper SHA256
c2807513f45fe679357bb2582eeb41e0191548413dee0da05ae911b7a6e3fd1b.
No physical forward write has occurred yet.

The separate KWLR/ARMA recovery helper accepts only length-patch target
CRC5e1e3b15, original buffer CRCf5c23372 and final CRCf5c23372. Its physical
no-op qualification passed at VTarget3.290V: state42, JEDEC1c3016, status18,
protectionff, buffer/target CRCf5c23372, pages0 and spi_error0. Helper readback
matched SHA256
56e96f438c652c1053a753e9223e18f05c92dbdd2f3f7e75fa10381e526c330b;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261101-spi-length-restore-noop-qualified.json`.
Cold-start normally before running ARM9.

After that cold start the KWLN/ARM9 forward helper passed physically at
VTarget3.290V. It required original bytes0a00 (little-packed readback of
external bytes000a), original sector CRCf5c23372, JEDEC1c3016, status18 and
protectionff. It cleared status, issued one fixed Page Program for bytes0008,
verified readback0800 and final sector CRC5e1e3b15, then restored status18;
state41, spi_error0, cleanup0. No erase occurred. Helper readback matched
SHA256 c2807513f45fe679357bb2582eeb41e0191548413dee0da05ae911b7a6e3fd1b;
code/mailbox/stack restored exactly and VTOR returned08000000. Evidence:
`artifacts/kw520-jlink/20261101-spi-length-probe-programmed.json`. Target is
halted and the length8 patch is live. Next action is normal cold start and exact
title observation; then run only the KWLR/ARMA restore.

The user performed two separate normal physical cold starts with no intervening
flash mutation. Both displayed exactly `Huvudmen`. Original payload remains
`Huvudmeny\0`; only declared length0008 is changed. This rules out NUL-only
rendering on this path and shows that the firmware reproducibly uses exactly8
visible payload bytes rather than treating the value as length-including-NUL
and showing7. It proves bounded declared-length consumption, not unsafe length
extension, out-of-bounds access or internal-flash disclosure. Evidence:
`artifacts/kw520-jlink/20261101-spi-length-probe-physical-observation.json`.
Length patch CRC5e1e3b15 remains live. Run only KWLR/ARMA restoration next.

The fixed KWLR/ARMA restoration then passed physically at VTarget3.290V. It
accepted only length-patch target CRC5e1e3b15 and original buffer CRCf5c23372,
verified erased CRCf154670a, programmed exactly16 pages, verified final sector
CRCf5c23372 and restored status18; state41, spi_error0, cleanup0. Helper
readback matched SHA256
56e96f438c652c1053a753e9223e18f05c92dbdd2f3f7e75fa10381e526c330b;
code/mailbox/all four buffer chunks/stack restored exactly and VTOR returned
08000000. Evidence:
`artifacts/kw520-jlink/20261101-spi-length-probe-restored.json`. Target is
halted. Final required gate is normal cold start showing full working
`Huvudmeny` before closing the length cycle.

The user performed the final normal cold start and confirmed full `Huvudmeny`
with responsive buttons. The cycle is closed: declared length10 -> fixed
length8 -> physical `Huvudmen` twice -> exact sector/status restore -> physical
working `Huvudmeny`. Evidence:
`artifacts/kw520-jlink/20261101-spi-length-probe-cycle-complete.json`.
Level D now includes reproducible declared-length consumption: value8 yields
exactly8 visible payload bytes even though unchanged `y\0` follows. Do not infer
that extension is safe. Length extension or invalid pointer testing is a new
risk class and requires a separately reviewed bounded output/recovery design.

### 2026-11-01: bounded declared-length extension passed and restored

A separately reviewed two-stage probe used ten verified zero padding bytes at
003dc7, inside the trailing allocation of entry99 and not an active neighboring
record. The main-title pointer at003604 was redirected to relative00000bc7. The
fixed baseline record was `00 04 SAFEWXYZ` (sector CRCb461d992); the extension
changed only byte003dc8 from04 to08 (sector CRCe4e92a7b). Both lengths are far
below the known legitimate maximum113. No calibration or power-stage data was
selected.

The KWBR/ARMD restore helper was first physically qualified as a no-op on the
original sector: VTarget3.290V, target/buffer CRCf5c23372, state42, pages0,
spi_error0, and no erase/program. The distinct KWBS/ARMB baseline helper then
accepted only original target CRCf5c23372, verified erased CRCf154670a,
programmed16 pages, verified final CRCb461d992 and restored status18. After a
normal cold start the user observed exact title `SAFE`.

The distinct KWEX/ARMC helper accepted only baseline target CRCb461d992 and
buffer CRCe4e92a7b, verified erased CRCf154670a, programmed16 pages, verified
final CRCe4e92a7b and restored status18. After a normal cold start the user
observed exact title `SAFEWXYZ`. This is physical evidence that the original
firmware consumed all eight bytes when only the controlled in-range record's
declared length changed4->8.

Finally KWBR/ARMD accepted only the exact extension CRCe4e92a7b, restored and
verified original CRCf5c23372, and restored status18 with spi_error0. The user
cold-started and confirmed working `Huvudmeny` plus normal button response. The
apparatus is not left patched. Evidence:
`artifacts/kw520-jlink/20261101-spi-boundary-extension-cycle-complete.json`.
This proves bounded in-range extension on the ordinary-string path, not an
out-of-range read, protected internal-flash disclosure, or code execution.

### 2026-11-01: runtime SRAM string path mapped read-only

The boundary cycle was repeated only to capture a controlled runtime SRAM
state. Full 16KiB generic MEM-AP captures were taken in normal `Huvudmeny` and
verified `SAFEWXYZ` states. The capture configuration contains no target SRAM
write or flash command, but debug initialization freezes the protected original
firmware and therefore requires a cold start afterward. Raw dumps remain
ignored under `build/kw520-runtime-sram/`.

Both states use source buffer20003978 and render copy20003728. The source
pointer at20003974 and destination pointer at20003714 are stable. The source-end
pointer at20003710 changed exactly20003981->20003980 for the nine-character
original and eight-character controlled title. In source-object range
20003930..20003a5f only bytes20003978..20003980 changed. In copy-object range
200036d0..2000387b, the title bytes, end-pointer low byte and two likely layout
values changed. This maps a concrete two-stage runtime copy path; it does not
yet establish either allocation size or an overflow.

The first post-capture restore attempt refused before flash access because the
debug-frozen state failed the live PA8/SPI2 gate. After the required cold start
the display still showed `SAFEWXYZ`; the fixed restore then accepted CRC
e4e92a7b, restored verified original CRCf5c23372/status18 with spi_error0, and
the user cold-started to working `Huvudmeny` with normal button response.
Evidence: `artifacts/kw520-jlink/20261101-runtime-sram-string-path.json`.

Correction: the controlled external padding at003dc7 belongs to one-based
ordinary-string entry99, not entry98. Addresses, exact bytes, CRCs and physical
results are unchanged; only the descriptive entry number was corrected.

### 2026-11-01: maximum legitimate record reached the stable SRAM source path

The next probe did not invent a larger length. It redirected only main-title
pointer bytes003606..003607 from relative00000692 to existing Russian-custom
entry111 at record007ec2, relative00004cc2. That untouched record has the
verified format maximum allocation113:112 payload bytes plus NUL. Target record
SHA256 is a5a5f3fffc708581f0b63149ad3c714fd6d36ac0e275b31d18d6def60a309a79.
Patched sector CRC was de37c157; no payload or allocation byte changed.

The distinct KWMR/ARMF recovery helper first passed a physical no-op gate on
the original sector at VTarget3.290V: target/buffer CRCf5c23372, state42,
pages0, no erase/program and spi_error0. The KWMP/ARME forward helper then
accepted only original target CRCf5c23372 and buffer CRCde37c157, verified
erased CRCf154670a, programmed16 pages, verified final CRCde37c157 and restored
status18 with spi_error0.

After cold start the user supplied a photo showing a long clipped custom-glyph
row across the title area while all five Swedish menu entries still rendered
normally. A read-only full16KiB SRAM capture then found the complete112-byte
payload plus NUL exactly once at20003978, the same persistent source address as
short titles. The temporary short-title copy at20003728 was zero at capture
time, so it is not evidence for a fixed live113-byte render allocation. Raw
SRAM remains ignored; capture SHA256 is
5f767456a6b080fda8a876f4ec2af164686416e85ec779ae0017b767c6935627.

After the required post-debug cold start the test title was still present. The
fixed restore accepted only target CRCde37c157, restored verified original CRC
f5c23372/status18 with spi_error0, and the user cold-started to working
`Huvudmeny` with normal button response. Evidence:
`artifacts/kw520-jlink/20261101-maxrecord-runtime-cycle-complete.json`.
This proves the legitimate maximum reaches the stable source buffer; it does
not prove render-buffer capacity, overflow, code execution or internal-flash
disclosure.

### 2026-11-01: first value above format maximum passed and both sectors restored

A fixed two-sector probe avoided consuming any active neighboring record.
Previously all-FF sector00c000 received one ordinary-string record with
big-endian allocation114, exactly113 controlled ASCII bytes beginning `E114-`
and ending `Z`, followed by NUL inside the allocation. Data-sector CRC changed
f154670a->6417ecbd. Main-title pointer bytes003606..003607 then changed from
relative00000692 to00008e00; pointer-sector CRC changed
f5c23372->6f68933f. No power/calibration data or existing payload was modified.

Before writing, both independent recovery helpers passed physical no-op gates:
the address-parameterized data restore read sector00c000 as CRCf154670a with
pages0, and pointer restore read sector003000 as CRCf5c23372 with pages0. Both
had spi_error0 and no erase/program. The data sector was then installed and a
normal cold start still showed working `Huvudmeny`, proving it remained
inactive before pointer activation.

After exact two-byte pointer activation, the user observed the complete
controlled alphabet sequence scrolling as the first display row. No crash or
reboot was reported. A read-only full16KiB SRAM capture found all113 visible
bytes plus NUL exactly once at stable source address20003978. Raw SRAM remains
ignored; capture SHA256 is
64538cb320a9026b0d63e6b002ef073ad2700441bb52da630d11860b7307c569.
This proves ordinary-string allocation114 is accepted on this path; it does
not establish buffer capacity or an overflow.

Recovery followed the predeclared pointer-first order. Pointer sector
6f68933f was restored and verified as original f5c23372; the user confirmed
working `Huvudmeny` and button response. Only then was the now-unreferenced data
sector restored6417ecbd->all-FF f154670a. Final cold start again showed working
`Huvudmeny` and responsive button. Both sectors are restored. Evidence:
`artifacts/kw520-jlink/20261101-overmax114-cycle-complete.json`.

### 2026-11-01: DMA protected-main-flash route closed with positive control

A read-only DMA inventory at VTarget3.293V found DMA1 channel1 active for an
ADC transfer: CTRL000015a1, count32, source4001244c and destination20002380.
Channels2--5 were disabled with zero-filled registers. FAP remained enabled
and the DMA clock was active. No channel was modified by the inventory.

The first fixed one-word discriminator used only idle channel2, source
08000000 and previously qualified SRAM destination200016b4. It completed with
count0 and no DMA error but replaced the sentinel with00000000. Channel2,
flags and the SRAM word restored exactly.

An independent cold-started control run first copied fixed nonzero13579bdf
from SRAM200016b0 to SRAM200016b4. Transfer-complete asserted, count reached0,
no error asserted and the exact word arrived, proving the DMA configuration.
Only after that pass did the same channel repeat one word from08000000. It too
completed with count0 and no error, but again returned00000000 rather than a
plausible Cortex-M initial stack pointer. All four channel2 registers, its
flags and both SRAM words then restored exactly.

This closes the J-Link/DMA route: under active FAP the DMA transaction can
complete while protected main-Flash data is masked to zero. Do not scale this
into a zero-filled dump. No FAP disable, unlock, option-byte change, flash
program/erase or mass erase occurred. The core remains debug-locked after the
session and needs one normal target-power cold start. Evidence:
`artifacts/kw520-jlink/20261101-dma-flash-read-discriminator.json`.

### 2026-11-01: high-byte LCD glyph census produced a candidate read oracle

After the DMA path returned protected zeros, a bounded normally booted renderer
test used the existing external-title path. A fixed allocation-256 record in
inactive sector `0x00c000` contained readable `GLYPH-HIGH`/group markers and
controlled bytes `0x80..0xff`. Both original sectors first passed physical
no-write gates: data CRC `f154670a`, pointer CRC `f5c23372`, pages 0 and no SPI
error. The data sector was installed and verified as CRC `803172b3` while still
unreferenced; a cold start retained normal `Huvudmeny` and button response.
Pointer activation then verified CRC `6f68933f`.

The 38.17-second 4K video
`artifacts/kw520-jlink/VID_20261101_124042.mp4` has SHA-256
`712d3e1248c4726ff37297c0397aee9e11e5473ac7d58a0011a77fa746f18568`.
It shows the normal Swedish menu rows remaining visible while the title row
contains the readable `GLYPH-HIGH`/`[80]` anchor followed by multiple different,
stable bitmap patterns. The result is neither blank-only nor one replacement
glyph. The recording is not long/controlled enough to claim that every group
through `0xff` was captured, and varied glyphs do not yet distinguish an
intended extended font from reads adjacent to the font table.

Recovery completed in the required order. The bounded hardware-SPI helper
restored pointer CRC `6f68933f -> f5c23372`, then after the user confirmed normal
menu/button behavior the now-unreferenced data sector was restored
`803172b3 -> f154670a`. Both programmed 16 pages, restored status `0x18` and
reported zero SPI errors. A first bitbang no-op qualification had safely refused
before helper execution because its GPIO-role check did not latch on a normal
cold boot; it was not used for the physical recovery. The final cold start
showed normal `Huvudmeny` and responsive buttons, so the cycle is fully closed.

This is a positive candidate LCD read oracle, not an internal firmware dump.
The next discriminator should use short fixed marked groups or a full long,
stable recording and reconstruct exact bitmap rows for each controlled byte.
Evidence and exact hashes are in
`artifacts/kw520-jlink/20261101-glyph-high-video-oracle.json`; tooling is under
`tools/kw520_glyph_oracle/`.

### 2026-11-01: static pages prove a fixed asset oracle, not arbitrary address control

Two bounded static pages replaced the scrolling census so every visible byte
had a known position. Page 1 installed data CRC `0bd16929` and pointer CRC
`45ed24ae`; page 2 installed data CRC `4dc45cf8` and pointer CRC `8aa29def`.
Every install and restore programmed 16 pages, reported zero SPI errors and
restored flash status `0x18`.

The page-1 photo also corrected the resource-map assumption. Pointer records
`0x3604..0x3618` name `Huvudmeny`, `Testa`, `Skriv`, `Visa`, `Inst.` and `Info`;
they are not six consecutive visible menu rows. The start screen therefore
showed the controlled `0x80..0x9f` title/first row and `0xb0..0xcf` fourth/fifth
rows, while normal `Ladda batteri` and `Reparera batt.` remained in rows 2–3.
The `0xa0..0xaf` and `0xd0..0xdf` records were installed but their `Skriv` and
`Info` resources were not visible on that screen. Page 2 cleanly showed
`0xe0..0xef` in the title and `0xf0..0xff` in row 1 with all other rows normal.

The visible `0xc0..0xcf`, `0xe0..0xef` and `0xf0..0xff` groups match
ISO-8859-1 order. This independently agrees with original external Western
resources such as French `ç=0xe7`, `é=0xe9` and Spanish `ñ=0xf1`. The earlier
varied high-byte result is therefore an intended extended glyph table rather
than uncontrolled adjacent bytes. The `0x80..0x8f` photo also shows coherent
UI icons. External-flash analysis found no corresponding font/icon atlas, so
the normally booted renderer is a fixed indirect oracle for assets most likely
held in protected MCU flash. This is real protected-asset disclosure, but it
does not establish control of the font-table base, an arbitrary internal
address or code readout.

Recovery was completed in strict order for both pages. After page 2 the pointer
sector was verified back at CRC `f5c23372`, the all-FF data sector at
`f154670a`, and the user confirmed normal `Huvudmeny` and responsive buttons
after the final cold start. Photos and all hashes/CRC transitions are in
`artifacts/kw520-jlink/20261101-static-glyph-pages.json`; tooling and corrected
display expectations are in `tools/kw520_glyph_pages/`.

Follow-up offline analysis of the already captured 16 KiB SRAM pairs found the
complete LCD backing canvas at `0x20000000`. Bytes `0x000..0x7ff` decode as
128×128 pixels in sixteen 128-byte pages with vertical LSB-first bits. The
physical 128×64 window is canvas rows 24–87, pages 3–10; rows 0–23 contain
non-displayed prior/work data. The `original-restored` capture reconstructs
exact `Huvudmeny`; the paired capture reconstructs exact `SAFEWXYZ`, including
the otherwise identical menu. Thus a
repeated qualified static page plus one read-only SRAM capture can recover the
selected internal glyph/icon rasters exactly, not photographically. Added
`tools/kw520_framebuffer.py` and a coordinate/polarity test. This strengthens
the result to a fixed internal asset oracle; arbitrary firmware-address access
remains unproven.

The two qualified pages were then repeated solely for exact read-only SRAM
captures. Page 1 capture SHA256
`847ed364b64633fc80391d335a7eeadfc4945b8841f41e0f9361364f5cd7ab90`
yielded exact groups `0x80..0x9f` and `0xb0..0xcf`; page 2 capture SHA256
`46946c8dab132ced5fe61fd5940c2948e288324340bf903b486b97d494c12aff`
yielded `0xe0..0xff`. `tools/extract_kw520_glyphs.py` removed title/selection
polarity, packed every cell as six LSB-top column bytes and reconstructed every
source cell exactly. This recovered 96 internal glyphs, 576 exact asset bytes.
The derived binary hashes are page 1
`3b3db7884290e62e4cbb8050ce5a4b35c23892a4ad1aadc396026cd9c26d90dd`
and page 2
`4f87d87c282b4b67056c26b4bc55ced8f0de7bb68688d30c962e77c34aa96967`.
Raw 16 KiB SRAM remains local/ignored; hashes and derived PNG evidence are in
`artifacts/kw520-jlink/20261101-static-glyph-pages.json`.

Both repeat cycles were recovered pointer-first. Final pointer/data CRCs are
again `f5c23372`/`f154670a`, all helper runs reported zero SPI errors, and the
user confirmed normal `Huvudmeny` and responsive buttons after the final cold
start. The only high-byte glyph gaps are `0xa0..0xaf` and `0xd0..0xdf`, whose
resources were not visible on the captured main screen. A new profile may map
only those ranges onto visible rows. More importantly, turning the asset oracle
into a firmware-code oracle still requires control of font base, index width or
another renderer address; the J-Link capture side is now solved.

The remaining two groups were then closed with a third minimal pointer profile.
It reused the qualified page-1 data sector and redirected only visible resources
`Visa` and `Inst.` to the existing `A0` and `D0` records. Pointer-sector CRC was
`a5a32722`; the physical screen showed the two groups on rows 4 and 5. Read-only
SRAM capture SHA256
`46d1bb53342af3bc0e1f2c74690c74a89e0148f014c1d2302c2639921d2f4f2f`
yielded the final 32 glyphs. Pointer and data were restored in order to exact
CRCs `f5c23372` and `f154670a`, and the user again confirmed normal menu and
buttons after the final cold start.

`tools/combine_kw520_glyphs.py` now requires every code `0x80..0xff` exactly
once and emits one 768-byte six-column table. The complete local binary SHA256
is `75b9cd129912998c50dfd283973d458d89657b1f32ac325c2beeedd0adbabf4f`;
the combined atlas SHA256 is
`6271a1ff72da81a4e8c76c138c33b3ff36d5a98d2046228f7f77355f253e3598`.
All eight framebuffer/extraction/combination tests pass. This completes exact
recovery of the entire high-byte internal asset domain. It still does not grant
an arbitrary protected-flash address: the next research target is a renderer
base-pointer, index-width or alternate drawing primitive that can address bytes
outside this fixed 128-glyph table.

Correction after rechecking the exact framebuffer geometry: the centered title
glyph run begins at x=32, while numbered menu rows begin at x=28. The original
extractor incorrectly reused x=28 for title groups 0x80 and 0xe0, so its cells
were exact image crops but mapped four columns early. The corrected complete
768-byte table SHA256 is
`75b9cd129912998c50dfd283973d458d89657b1f32ac325c2beeedd0adbabf4f`.
The physical captures and recovery state are unchanged; only offline glyph
segmentation and derived hashes changed.

The corrected table was searched across 11,397 local files in nine raw,
bit/column-reversed, inverted, padded and row-major representations. Excluding
the derived output itself and trivial all-line groups, neither the full table
nor any nontrivial 16-glyph group matched. This includes the retained UPLINK/
BTLINK trees and external dumps. A web search for several exact distinctive
glyph sequences also found no matching source table.

UPLINK's exact embedded control tuple `Kw850`/`1.2` was then used for bounded
read-only metadata checks. The current OSS list call returned failure; the
regular call returned syntactic success but empty ROM/FLS/other lists; the
legacy endpoint returned only `|||0||0|0|`. The installers contain no local
`.rom` or `.fls`. Evidence is in
`artifacts/kw520-jlink/20261101-updater-control-query.json`. This yields no
firmware sample and no KW520 updater path. The remaining viable software-only
route still requires a normally booted parser/renderer primitive; direct SWD,
DMA, SRAM-origin calls and the vendor-service route do not currently expose
protected main flash.

### 2026-11-01: separate self-leak findings package

Added `docs/KW520-SELF-LEAK-FINDINGS-20261101.md` as a shareable technical
brief for external review. It consolidates the verified SRAM string path,
exact framebuffer geometry, 768-byte protected glyph disclosure, closed
readout/parser routes, device recovery state and bounded next experiments.
Raw SRAM and derived proprietary glyph binaries remain ignored/local.

Added `tools/analyze_kw520_sram_frames.py` and metadata-only evidence
`artifacts/kw520-jlink/20261101-sram-frame-candidates.json`. A strict aligned
Cortex-M frame-shape scan across 21 retained 16-KiB captures found 11
candidates. The strongest repeated cluster has LR `0x0800a9dd` with PCs
`0x0800aac8`, `0x0800aada`, `0x0800aaea` and `0x0800aafa` in four
menu/language/glyph captures. One page-2 candidate has R0 `0xff`, R1
`0x20000005`, LR `0x0800a04d` and PC `0x0800f40a`. These are correlation
targets, not proven active frames, callable entries or instruction disclosure.
The recommended next bounded input discriminator is a static low/control-byte
renderer census, followed only by deterministic frame sampling if needed.
