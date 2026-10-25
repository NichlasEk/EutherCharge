# ESP32-C3 replacement architecture — design, not a hardware release

The original NY8 ROM/emulator remains the behavioral reference. The replacement
will be a new open implementation, not binary emulation on ESP32-C3. Firmware
state numbers and raw thresholds are not yet sufficient to reproduce safe charging.
No ESP32 firmware, pin assignments or power-stage outputs are enabled by this design.

## Boundaries

1. **Portable control library**: deterministic `step(previous, measurement, input,
   elapsed)` returning next state, requested limits, display values and fault status.
   It owns charging decisions; no ESP-IDF, radio, GPIO, wall-clock or heap dependency.
   Initially only inhibited/idle/fault states are implementable from verified facts.
   Physical thresholds require measured units, chemistry requirements and validation.
2. **Hardware abstraction**: timestamped battery voltage, current and temperature,
   validity/calibration metadata, battery presence/polarity, local button, actual
   output feedback and independent protection status. Output request and effective
   output are distinct. A simulation backend implements every interface first.
3. **Safety supervisor**: rejects stale/invalid samples and forbidden transitions,
   latches faults and controls a separate enable request. Reset, watchdog expiry,
   lost calibration and unknown board identity leave the output inhibited. Fault
   reset cannot itself resume charging. Independent physical cutoffs remain required.
4. **Presentation**: HT1621-compatible display encoder, indicators and local MODE
   input. Display has no authority to enable charging. Firmware-derived glyph maps
   are reusable, but icon positions still require validation against the real glass.
5. **Local BLE adapter**: serializes telemetry and validates user requests, then
   queues those requests to the same control API used by the button. BLE callbacks
   never manipulate PWM or bypass the supervisor. Charging must operate locally
   without an app or cloud connection once a validated local policy exists.

## Board mapping contract

Use logical signals until electrical roles are confirmed. Record for each signal:
original package pin, board net, direction, voltage range, active polarity,
boot/reset behavior, measurement source, uncertainty, and replacement interface.
The existing functional map is the initial evidence inventory, not a wiring guide.

| Logical signal | Existing evidence | Required before an ESP32 GPIO is assigned |
|---|---|---|
| LCD CS/WR/DATA | Three traced nets, matching startup bits | LCD input thresholds and power sequencing |
| MODE | Active-low firmware input and board button | Pull-up voltage, protection and debounce timing |
| Temperature | ADC1 and ROM lookup table | NTC type, divider, reference and calibration |
| Voltage/current feedback | ADC2–4 used by firmware | Resolve which quantity, scale, polarity and bandwidth |
| PWM/control | PWM1 registers used | Identify physical load and fail-safe off level |
| Fan | Not uniquely mapped | Identify driver, supply and independent thermal behavior |
| Output inhibit | Not established | Independent hardware disconnect and reset-safe default |

ESP32-C3 supply is nominal3.3V; the existing5V board is not directly pin compatible.
Translate/protect signal levels and redesign analog conditioning only after net
mapping. The [Espressif datasheet](https://documentation.espressif.com/esp32-c3_datasheet_en.html)
specifies3.0–3.6V recommended supplies and input thresholds relative to the I/O
supply. It does not justify connecting the charger's5V nets directly.

## BLE contract proposal (v0, transport-independent)

Choose ESP-IDF with ESP-NimBLE for the eventual port; the official
[ESP32-C3 BLE overview](https://docs.espressif.com/projects/esp-idf/en/latest/esp32c3/api-guides/ble/overview.html)
documents the supported host stack. No SDK version is pinned until a build exists.

- Capabilities/read: protocol version, board revision, firmware version, supported
  modes and limits, calibration status, simulation/physical-backend identity.
- Telemetry/read+notify: monotonic sequence and sample age, mV, mA, centi-degrees,
  validity flags, named state, requested/effective output, latched fault code.
- Request/write-with-response: request ID, operation and bounded parameters.
  Initial operations: read status, select a validated mode, stop. No raw register,
  direct PWM, unlimited voltage/current, calibration-write or remote-start command.
- Result/read+notify: request ID, accepted/rejected, reason and effective state.
  Duplicate IDs must not repeat actions. Unsupported versions/fields are rejected.

Use authenticated encrypted pairing for writes; local confirmation is required for
pairing. A Kotlin repository exposes a StateFlow of telemetry to Compose and retains
sample age/validity. The UI must distinguish a queued request from confirmed device
state and a simulation backend from hardware. BLE loss removes remote requests,
not autonomous local fault protection. No cloud account is required.

## Validation gates

First extend replayable raw-input scenarios and determine the original state graph.
Then validate a portable control library with calibrated physical-unit fixtures,
battery disconnect, reverse polarity, sensor faults, stale data, reset and boundary
conditions. Compare display and mode behavior separately from electrical control.

Only afterward build ESP32-C3 with a simulation/dummy output backend, test BLE
protocol failures and local-only operation, and perform bounded bench measurements
with the power stage disconnected. Real operation requires verified isolation,
independent voltage/current/thermal cutoffs, safe disconnect, measured pin mapping,
and explicit approval for hardware changes. Passing emulator tests is not this gate.
