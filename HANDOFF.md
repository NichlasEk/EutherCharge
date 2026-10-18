# EutherCharge handoff — 2026-10-18

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
