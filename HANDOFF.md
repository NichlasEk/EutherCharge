# EutherCharge handoff — uppdaterad 2026-10-22

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
