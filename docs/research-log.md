# Forskningslogg

## 2026-10-18 — repo initierat

### Bekräftat

- Målprodukten uppges vara en KONNWEI KW520.
- Flashkretsen är fysiskt urplockad.
- Den rapporterade märkningen är `032C-104HOP`.
- Ingen firmwaredump fanns i projektkatalogen vid initiering.

### Hypotes

- Märkningen kan avse `PM25LQ032C`, en 4-MiB SPI-NOR-krets.

### Behöver mätas

- Foto av märkning och kapsel.
- Kapselvariant och orientering.
- Programmerarens VCC.
- JEDEC-ID och statusregister.
- Exakt storlek samt SHA-256 för tre oberoende dumpningar.
- CPU/MCU på huvudkortet och anslutningen mellan MCU och flash.

### Nästa grind

Läs kretsen tre gånger och kör:

```sh
python3 tools/fwtool.py compare dumps/read-1.bin dumps/read-2.bin dumps/read-3.bin
python3 tools/fwtool.py inspect dumps/read-1.bin --json
```

Lägg endast analysresultat och hashvärden i repot, inte dumpfilen.

## 2026-10-18 — första fysiska avläsningen

### Bekräftat

- Programmerare: CH341A, USB-ID `1a86:5512`.
- `flashrom` identifierade `Eon EN25Q32(A/B)`, 4096 KiB.
- Verbos probe gav ID1 `0x1c`, ID2 `0x3016` (`1c 30 16`).
- Tre läsningar producerade vardera exakt 4 194 304 byte.

### Underkänt

Läsningarna var inte identiska. Första skillnaden låg vid `0x5000` och varje
filpar hade cirka 95 000 avvikande byte. Lokala SHA-256:

```text
39ac357b55dda439053da6dc607a4371eaf45b8fa7ea3298c02f0263a5974b27  read-1
88e8e18733655fbb560d6835f85965ac8d8ca45f04985e764d826a91b76c7ea7  read-2
54cca3ba96d584d67c54de609a8cfdb94ca866ae426c19878b1e7454f8afd4a6  read-3
```

Ingen fil betraktas som en giltig backup och ingen skrivning har utförts.

### Nästa fysiska steg

Koppla ur USB, sätt om kretsen i sockeln med verifierad pin 1, kontrollera och
mät 3,3 V-matningen och gör därefter tre nya avläsningar.

## 2026-10-18 — avläsning efter omsättning

JEDEC-ID:t var åter stabilt som `1c 30 16`, men statusregistret var fortfarande
`0xff`. Tre nya 4-MiB-läsningar gav följande lokala SHA-256:

```text
a865c10f26593403382ed3317a7442d620009e353d4823994bd6af5155c06f45  reseat-1
9bb8c64f9115f08148c51804b73ebeab3377ac4b45bf72a07e8bb08a089f7e9b  reseat-2
2a013f7122a352310266c5ff1384b813f808969525c8a22c373b4ce96a858fdf  reseat-3
```

Filparens avvikelser var 4 094, 20 425 respektive 24 519 byte. En körning
rapporterade dessutom `Block protection could not be disabled!`. Regioner
växlade mellan plausibla firmwaredata, `ff` och bitmönster, vilket talar för
instabil fysisk kontakt, matning eller signalväg. Ingen fil godkänns som backup
och ingen skrivning har utförts.

Nästa steg är att kontrollera programmerarkortets 25xx-position, pin 1,
sockel/adapter, rena kretsben samt mäta VCC mellan pin 8 och pin 4 under läsning.

## 2026-10-18 — andra omsättningen

Statusregistret ändrades till `0xfc`, men tre nya läsningar var fortfarande
olika. Första avvikelsen uppstod vid `0x1000` respektive `0x1`, och filparen
skilde sig med 17 566–21 700 byte. SHA-256:

```text
044ae13bff87de11965fa11ae123cbb446d2b354201ccc030752e1e8535969c3  reseat2-1
84c35d352f34750fc9d62081cb412c4cee2a2241656784b2f9947eb5bb3beccc  reseat2-2
d5612dd0af1acae09eccce2900744ddc0f0a1b9176348a523f2b97f3c7738189  reseat2-3
```

Över samtliga nio CH341A-läsningar var 952 av 1024 fyrakilobytesblock identiska
i alla nio filer. Resterande 72 block hade alla en unik exakt majoritet på minst
5 av 9 observationer. Detta räcker för en härledd analyskopia, men inte för att
godkänna CH341A-läsningen som återställningsbackup.

En lokal, Git-ignorerad analyskopia skapades genom exakt majoritet per 4-KiB-
block. SHA-256 är
`d715d21dfb4dc36f0f10ca27fc6ef03fc2f4dacee187396f504683948f30dde0`.
Blockens röststyrka var 5/9 för 7 block, 6/9 för 37, 7/9 för 10, 8/9 för 18
och 9/9 för 952. Filen är uttryckligen härledd och får inte användas för
skrivning innan TL866A-resultatet har verifierat den.

Nästa korskontroll görs med en TL866A och `minipro`, som stöder både TL866A och
EN25Q32A/B. Tre identiska TL866A-läsningar krävs innan dumpen godkänns.

## 2026-10-18 — TL866A verifierar originaldumpen

### Utrustning

- Programmerare: TL866A, firmware `03.2.86`.
- Verktyg: `minipro` 0.7.4, profil `EN25Q32A@SOP8`.
- Chip-ID vid varje läsning: `0x1C3016 OK`.

### Resultat

Tre separata 4-MiB-läsningar var byte-identiska:

```text
d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2
```

Dumpen innehåller identifierarna `KONNWEI`, `KW520` och version `1.0.1`.
En skrivskyddad lokal kopia finns som
`dumps/original/kw520-1.0.1-original-d369a860.bin`; `dumps/` är Git-ignorerad.

CH341A-konsensusfilen matchade endast 1017 av 1024 exakta 4-KiB-block och
skilde sig med 16 788 byte. Den är underkänd som både backup och skrivunderlag.

### Nästa grind

Identifiera processorarkitektur, kod-/resursregioner och kontrollsummor från
den verifierade TL866A-dumpen innan någon patch definieras. Originalkretsen får
inte raderas eller skrivas under analysfasen.

## 2026-10-18 — språkformat, Studio 0.1 och svensk image

Åtta språkbanker identifierades med 162 poster vardera. Varje bank består av
en big-endian 32-bitars pekartabell relativ till `0x3200` och poster med
big-endian 16-bitars längd följd av NUL-terminerad text. Samtliga 1 296 poster
validerar strukturellt. Den ryska banken använder en ännu okänd teckenkodning
och är därför skrivskyddad.

EutherCharge Studio 0.1 byggdes som en lokal, beroendefri webbapp med:

- filstorleks- och SHA-256-kontroll;
- texteditor med fast allokering och överflödesskydd;
- rågrafikvisare för 1-, 2-, 4-, 8-bpp- och RGB565-hypoteser;
- fyra temaprototyper, ELDRÄNG MODE och Fan Hymn i simulatorn;
- export av ny image och JSON-manifest.

En svensk ersättning för samtliga 162 semantiska poster i English-banken har
byggts lokalt. 142 poster och totalt 1 912 byte skiljer sig från originalet.
Imageformat, pekartabeller, längdprefix och alla andra områden är oförändrade.

```text
Original: d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2
Svenska:  c484052b5b9f1ad51ede0672b28b96de289d82b48fd882b730be6311322419ae
Storlek:  4 194 304 byte för båda
```

Rådata vid `0x000000–0x0001FF` identifierades efter ytterligare dimensionstest
som en komplett `128×32` KONNWEI-startlogga i 1-bpp, kolumnvis LSB-format.
En EUTHERCHARGE-logga har byggts och återavkodats i exakt samma 512-byteformat.
Den integrerade svenska/logo-imagen har SHA-256
`4a4947e116dc405e577c97e965c342cc89f7f8b3f517babee9a8105e400d0329`
och skiljer sig med 2 269 byte, enbart inom loggan och English-bankens
strängpayloads. Ingen ytterligare bildruta eller animationstabell är verifierad.

Fyra 52-byteposter med `0xA5`-markör identifierades vid `0x383000`. Fält vid
`+0x24`, `+0x26`, `+0x28` och `+0x2C` ger plausibla spännings-, procent- och
resistansvärden, men presenteras uttryckligen som hypoteser tills de har
jämförts mot apparatens Review-skärm. En skrivskyddad parser finns både i
Studio och `kw520_resources.py history`.

Nio Python-test och sju JavaScript-test passerar. Den integrerade imagen
byggdes om från originaldumpen och blev byte-identisk med den tidigare lokala
artefakten. Webbvyn renderades i Firefox. Den svenska imagen är ännu inte
programmerad eller provad på fysisk hårdvara.
