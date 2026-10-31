# KW520: offline analysis of KONNWEI updaters — 2026-10-31

## Scope and result

UPLINK and BTLINK were downloaded and unpacked without running their Windows applications or connecting them to the charger. Selected BTLINK checksum/frame-building machine code was executed only in Unicorn with mapped memory and no OS, USB, serial or network interface. No traffic was sent to KW520.

There is evidence of shared updater components, but no confirmed KW520 updater support, standalone firmware image, bootloader entry method or MCU flash readback operation. The user reports no other visible ports. An internal UART/test pad is only a hypothesis; do not assign pins or send frames without identifying the interface.

## Sources and local evidence

- Official tool list: https://www.konnwei.com/capabilities/Download-Update-Tool.html — KW520 was absent from the listed supported models; absence does not establish impossibility.
- Product page: https://konnwei.com/product/454.html
- Download index: http://www.itoscanner.com/download/
- UPLINK archive: http://www.itoscanner.com/down/duugy1qcqds8s
- BTLINK archive: http://www.itoscanner.com/down/4njkteiucfi88

Archives and extracted proprietary files remain under ignored `build/kw520-jlink-20261031/`.

| Archive | SHA-256 |
| --- | --- |
| btlink.rar | 6976989d738f6257ea8244a1260d6b735e478677cf5d843edd79bc6a01f3e2c9 |
| uplink.rar | 9e2a733703951c3ee6ce6546de89ece0a2f497771783488b1e147f7f7cddf34c |

Both contain Artery VirtualCOM drivers, ROM/FLASH update paths and the endpoint `http://svr.oscanner.com/uplink/od_checkupgrade.php`. BTLINK contains the literal UPLINK. Requests use `types=%s&subtype=%s`; actual KW520 values remain unknown. No firmware server query with guessed device identifiers was made. An Artery driver alone does not establish the interface used by KW520.

## BTLINK packet reconstruction

Addresses below are virtual addresses in extracted `btlink-extracted/app/bin/BTLink.exe`, image base 0x400000.

- Frame builder: 0x40c4f8; checksum: 0x40c3b0; byte update: 0x40c36c; response validation: 0x40c3f8.
- Request prefix: `40 40` (@@); command 0x0104 uses `5e 5e` instead.
- Response prefix: `24 24` ($$).
- Bytes 2–3: total frame length, little endian, including the ten framing bytes.
- Bytes 4–5: command, little endian.
- Payload begins at byte 6.
- Last four bytes: two-byte little-endian CRC, then CR LF.
- CRC covers everything before those final four bytes. Reflected polynomial 0x8408, initial 0xffff, final XOR 0xffff (CRC-16/X-25 parameters). Check value for ASCII 123456789: 0x906e.
- The same entire 512-byte CRC lookup table occurs in UPLINK at 0x586224. Full protocol identity has not been established.

The device-information routine sends command 0x0103 with no payload and accepts command 0x0143 in a 50- or 54-byte response. It copies four ten-byte fields from offsets 6, 16, 26 and 36. Exact field semantics remain unconfirmed. The longer response supplies two additional 16-bit values at offsets 46 and 48; defaults in the code are 512.

Offline information-request example: `40 40 0a 00 03 01 33 d3 0d 0a`. This is a reconstruction for analysis, not a verified safe KW520 command.

## Verification and next gate

Local `verify_protocol.py` checks all 256 CRC table entries against polynomial 0x8408, compares four reconstructed checksums against the isolated vendor x86 routine and compares the ten-byte information request against the vendor frame builder. All passed. This establishes encoding accuracy for the analyzed BTLINK routines, not behavior on KW520.

The software contains write/erase/update flows for .rom and .fls. No demonstrated readback path or bypass of SWD flash access protection was found. SWD identification previously established AT32F421C8T7 with protection enabled; do not unlock or erase it.

Next useful physical evidence is clear photographs of both sides of the PCB and continuity tracing of candidate test pads to MCU pins. Determine whether any communications interface is actually routed before selecting voltage, baud rate, adapter or sending data. Lack of an external connector may mean this model has no user-accessible update path.

## Follow-up: live metadata service and updater request path

Static UPLINK analysis found an additional endpoint embedded at VA0x58f2c5 and0x5b2842: `http://47.251.40.156/HandheldDeviceUpdate/OSSService.php`. Helper0x578dd4 constructs an application/x-www-form-urlencoded POST when given a body; call sites0x403ae5 (list) and0x409326 (upgrade metadata). Format strings are `types=%s&subtype=%s&getlist=yes` and `types=%s&subtype=%s`. Response parser expects success code100 and rom/fls metadata with list/url/md5/ver fields, plus ROM length. This identifies a metadata path, not a validated KW520 update.

Bounded requests made (no serial, private pairing data, serial number or firmware uploads):

- Old server root: HTTP403.
- Old od_checkupgrade endpoint with types=KW520, empty subtype, getlist=yes: HTTP200, `service unavailable!`.
- OSS endpoint GET and POST with the same incomplete parameters: HTTP200, JSON code101, message `The parameter cannot be null...`, data null.

KW520 was a model-label hypothesis; the correct device-reported type/subtype tuple is unknown. These errors do not prove KW520 unsupported. No subtype guessing/enumeration was performed. User asked to transcribe model/hardware/software version from the charger's information screen to compare with the protocol identifiers; display strings need not equal protocol identifiers. Responses are saved under ignored build/kw520-jlink-20261031 as kw520-oss-{query,post}.response and kw520-list-query.response.

The UPLINK info UI format `%s-%s ROM_ver:%s FLASH_ver:%s` supports four textual identity/version fields. Routine0x4041c0 splits one type string at underscore before list retrieval. Exact device-to-server semantics still need tracing. A call at0x405c50 sets the UART property to1000000 baud; this is a UPLINK code-path observation, not verified KW520 wiring or baud rate.

Offline external-flash check: original 4MiB image contains KW520 at0x3010. A four-byte-aligned scan for plausible Cortex-M vector starts (SRAM20000000..20004000; Thumb reset vector08000000..0800ffff) found none. This does not exclude compressed/encrypted images, a payload without vectors, or different mappings. Scan results saved as external-flash-vector-scan.json.

No original updater application was executed, no target communication or firmware writes occurred in this follow-up. No KW520-specific firmware image has been obtained.

### Reported device versions

User transcribed SW1.0.7 and HW1.2.0 from device. Serial number deliberately omitted from repository notes and metadata requests. Tested types=KW520, subtype=1.2.0 as an explicitly unverified mapping, using POST getlist=yes. HTTP200 returned JSON code101/message failure/data null. This is not proof firmware unavailable: displayed HW version may not be protocol subtype. No image obtained, no target writes. Do not treat historical external-backup filename1.0.1 as current MCU software-version evidence.

The same tuple using the regular metadata POST (without getlist=yes) returned HTTP200/code100/Get successful, but rom.list=[], rom.ver empty, fls.list=[], fls.ver empty, other.list=[] and other.ver1.0.0. Thus the endpoint accepts this request syntactically but supplies no downloadable firmware. Success code does not establish recognition or compatibility of the model/HW tuple; other.ver1.0.0 is not a verified KW520 firmware version. Raw response kw520-hw120-metadata.response retained locally.
