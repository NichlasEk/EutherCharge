# KW520 1.0.1 — verifierat resursformat

Detta dokument gäller referensdumpen med SHA-256
`d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2`.
Alla tal är byteoffset i externflashen och big-endian där inget annat anges.

## Produktfält

| Offset | Innehåll |
|---:|---|
| `0x003000` | `KONNWEI\0` |
| `0x003010` | `KW520\0` |
| `0x003020` | `1.0.1\0` |

## Språkbanker

Varje bank har exakt 162 fyrabytespekare följda av strängposter. Pekarna är
32-bitars big-endian och relativa till `0x003200`.

| Bank | Pekartabell | Första strängpost | Status |
|---|---:|---:|---|
| English | `0x003600` | `0x003888` | Latin-1 verifierad |
| Français | `0x004356` | `0x0045DE` | Latin-1 verifierad |
| Español | `0x00546D` | `0x0056F5` | Latin-1 verifierad |
| Deutsch | `0x006443` | `0x0066CB` | Latin-1 verifierad |
| Russian-custom | `0x007415` | `0x00769D` | egen teckenkodning, skrivskyddad |
| Italiano | `0x00843F` | `0x0086C7` | Latin-1 verifierad |
| Português | `0x009414` | `0x00969C` | Latin-1 verifierad |
| Nederlands | `0x00A3F2` | `0x00A67A` | Latin-1 verifierad |

En strängpost är:

```text
u16be allocation_including_nul
u8     payload[allocation_including_nul]
```

Sista nyttolastbyten är NUL. Alla 1 296 poster validerar mot denna struktur.
Exempel: första engelska pekaren är `0x00000688`, vilket ger absolut offset
`0x003200 + 0x0688 = 0x003888`. Där ligger `00 08 45 6e 67 6c 69 73 68 00`,
alltså längd 8 och `English\0`.

## Fastallokerad patchmodell

EutherCharge Studio 0.1 flyttar inga poster. En ersättning måste rymmas i
postens befintliga allokering minus slut-NUL. Verktyget:

1. lämnar pekartabellen orörd;
2. lämnar tvåbyteslängden orörd;
3. skriver ny Latin-1-text och NUL direkt efter texten;
4. nollfyller resten av den gamla nyttolasten;
5. skriver alltid en ny image och en manifestfil.

Den medföljande svenska startbanken översätter samtliga 162 semantiska poster
i English-banken. 142 poster får ändrade byte; standardnamn som `CCA`, `DIN`
och `SAE` förblir identiska. Säkerhetsmeddelanden är sakliga, inte humoristiska.

## Verifierad startlogga

`0x000000–0x0001FF` är en komplett `128×32` monokrom bitmap. Byten ligger
kolumnvis i fyra åttapixelsidor och bitarna är LSB först inom varje byte:

```text
offset = page_y * 128 + x
pixel  = (byte[offset] >> (y % 8)) & 1
```

Avkodningen visar ordmärket `KONNWEI` med ramlinjer. EutherCharge ersätter
samtliga 512 byte med en `EUTHER / CHARGE`-logga i exakt samma format och
adress. Originalfirmware behöver därför ingen ny resursläsare för denna patch.

Ingen ytterligare bildruta eller animationstabell är ännu verifierad.

En atlas av samtliga 512-byteblock i det använda resursområdet
`0x000000–0x00BFFF` avkodades med samma 128×32-format. Endast blocket vid
`0x000000` gav en sammanhängande bild. Områdena från `0x003600` och uppåt är
pekartabeller och textbanker, inte fler bilder i detta format.

För att inte missa små eller ojusterade sprites gjordes dessutom ett glidande
svep med start på **varje byte** i det ännu okända intervallet
`0x000200–0x0035FF`. Storlekarna 8×8, 12×12, 16×16, 24×24 och 32×32 provades
som rad- och kolumnpackad 1-bpp, vardera med MSB- och LSB-bitordning. De högst
rankade kandidaterna var endast fragment av de kända parameter- och
pekartabellerna; ingen sammanhängande batteri-, blixt- eller menyikon hittades.
Detta är starkare negativ evidens än enbart den tidigare 512-byteatlasen, men
utesluter inte ett ännu okänt komprimerat eller flerfärgat format.

`0x001000` och `0x002000` innehåller två byte-identiska, mycket glesa
4-KiB-sektorer. De första 48 byten ser ut som parametrar eller tabellvärden;
ytterligare sex värdebyte ligger vid `0x001280`/`0x002280` och resten är noll.
De 48 första bytena provades som alla naturliga 24×16-, 16×24- och 48×8-
monokromformat utan att bilda en sammanhängande ikon. Sektorerna behandlas som
okänd redundant konfigurationsdata och patchas inte.

Det finns inga identifierade PNG-, JPEG-, BMP- eller GIF-signaturer och ingen
bevisad bildresurstabell utöver startloggan. Det är fullt möjligt att ikoner och
typsnitt ligger i MCU:ns interna flash eller ritas som primitiver. Studio märker
därför alla övriga råpixeltolkningar som **hypoteser**.

Efter Nederlands-bankens sista ordinarie post vid `0x00B30B` följer åtta
språkspecifika `P0000`-felkodstexter till och med `0x00B423`. De har pekare och
längdprefix och är textdata, inte en dold ikonregion.

## Skrivskyddad historik vid `0x383000`

Fyra tätt packade poster finns vid `0x383000`, `0x383034`, `0x383068` och
`0x38309C`; nästa postplats vid `0x3830D0` är raderad. Varje post är 52 byte
och har `0xA5` som andra byte. Detta ger en verifierad poststorlek och markör,
men ännu inte verifierade betydelser för alla fält.

Följande korrelation är stark men fortfarande en **fälthypotes**:

| Relativ offset | Typ | Fyra observerade värden | Kandidatbetydelse |
|---:|---|---|---|
| `+0x0F` | u8 | `0, 0, 0, 2` | läge/flaggbyte, möjligen 12/24 V |
| `+0x18` | u16le | `400, 400, 400, 400` | angivet referensvärde |
| `+0x22` | u16le | `505, 110, 502, 1198` | uppmätt testvärde |
| `+0x24` | u16le / 100 | `12.52, 12.00, 12.35, 26.77` | volt |
| `+0x26` | u16le | `100, 27, 100, 100` | hälsa i procent |
| `+0x28` | u16le | `90, 25, 69, 100` | laddning i procent |
| `+0x2C` | float32le | `5.77, 26.51, 5.81, 9.74` | intern resistans i mΩ |

Kombinationen liknar batteritestresultat och stämmer semantiskt med UI-posten
`Review`, men det är inte fysisk bekräftelse. Studio och kommandot
`kw520_resources.py history` visar därför frågetecken/candidate-namn och gör
inga skrivningar i området. Nästa verifiering är att fotografera Review-skärmen
och jämföra en post fält för fält.

## Områden som inte får patchas ännu

- `0x003200–0x0035FF`: blandad strukturerad data före språkbankerna.
- `0x380000–0x381FFF`: gles metadata/status.
- `0x383000–0x383FFF`: historikposterna får läsas men inte patchas innan
  fältbetydelserna har korrelerats mot apparaten.

Särskilt `0x383000` hålls helt utanför UI-patchar tills fälten har korrelerats
mot kontrollerade ändringar på apparaten.
