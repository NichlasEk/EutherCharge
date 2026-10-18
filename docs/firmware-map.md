# Firmwarekarta — KW520 1.0.1

Analysen bygger på tre byte-identiska TL866A-läsningar av en EN25Q32A/B:

```text
Storlek:  4 194 304 byte
SHA-256: d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2
```

Originalfilen är lokal och Git-ignorerad.

## Kryptering och komprimering

Innehållet är inte helt krypterat. Produktidentifiering, versionsnummer och
stora delar av användargränssnittet ligger som direkt läsbar ASCII. Hela filens
entropi är endast 0,137 bit/byte eftersom den till största delen är tom
`0xff`-flash. De mest informationsrika 4-KiB-blocken ligger på cirka 4,6–6,1
bit/byte, vilket passar rå text, tabeller, typsnitt och grafik bättre än starkt
krypterad data.

Ingen standardcontainer som ELF, ZIP, GZIP, XZ, PNG, JPEG, BMP eller GIF har
identifierats. Avsaknad av signatur är inte ensam ett bevis, men tillsammans
med klartexten, den låga entropin och den glesa layouten finns inget stöd för
att den externa flashen är krypterad.

## Grov minneskarta

| Område | Storlek | Observation |
|---|---:|---|
| `0x000000–0x0001FF` | 512 byte | Verifierad 128×32 KONNWEI-startlogga, 1-bpp kolumn/LSB |
| `0x000200–0x00BFFF` | 47,5 KiB | Tabeller, okänd data och UI-strängar |
| `0x00C000–0x37FFFF` | 3 588 KiB | Helt raderat (`0xff`) |
| `0x380000–0x381FFF` | 8 KiB | Små metadata-/statusposter |
| `0x382000–0x382FFF` | 4 KiB | Helt raderat (`0xff`) |
| `0x383000–0x383FFF` | 4 KiB | Strukturerade mät-/historikposter |
| `0x384000–0x3FFFFF` | 496 KiB | Helt raderat (`0xff`) |

Av 1024 sektorer à 4 KiB är 1009 helt `0xff`. Endast 45 408 byte i hela
kretsen skiljer sig från `0xff`; 27 523 byte skiljer sig från både `0x00` och
`0xff`.

## Identifierade data

Fasta identifierare börjar vid `0x003000`:

```text
0x003000  KONNWEI
0x003010  KW520
0x003020  1.0.1
```

Från `0x003600` finns åtta verifierade pekartabeller och språkbanker med exakt
162 poster per språk. Strängposterna har big-endian längdprefix och
NUL-terminerad text. Bland posterna finns `Battery Repair`, `Battery Charge`,
`Calibration Mode`, `Lithium Iron Phosphate` och temperatur-/säkerhetsvarningar.
Se [resource-format.md](resource-format.md) för exakta offsets och format.

Ett byteglidande småbildssvep över alla okända byte före språkbankerna provade
fem spriteformatstorlekar och fyra 1-bpp-packningar utan att hitta fler
sammanhängande ikoner. Det utesluter inte okänd komprimering, men tillsammans
med den glesa minneskartan talar fyndet för att batteri- och statusgrafiken
ligger i MCU:ns interna flash eller ritas programmatiskt.

Området vid `0x383000` innehåller fyra 52-byteposter med en stabil `0xA5`-markör.
Talserierna korrelerar starkt med batteritesthistorik: kandidatvärdena omfattar
12.52/12.00/12.35/26.77 V, två procentfält och float32-värden som plausibelt
kan vara intern resistans. Betydelserna är inte fysiskt verifierade och visas
därför endast som fälthypoteser. Området är skrivskyddat i verktygen. Se
[resource-format.md](resource-format.md) för offsets och råvärden.

## Tolkning

Den externa EN25Q32-kretsen ser främst ut att lagra resurser, språk, tabeller
och beständig användardata. Det finns ännu inget säkert bevis för att laddarens
exekverbara styrprogram ligger här. Det kan ligga i en separat MCU:s interna
flash.

En fastallokerad UI-patch är implementerad utan att ändra pekare eller
längdprefix. Någon global kontrollsumma har inte identifierats, men fysisk
acceptans återstår. Ändringar av laddningslogik kräver identifiering och separat
granskning av huvudprocessorns interna firmware.
