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

## Grafik- och färgdata

`0x000000–0x0001FF` är ett strukturerat 512-bytesblock med mönster som passar
färg-, test- eller pixeldata. Tolkningar som 1-bpp, 4-bpp och RGB565 har
visualiserats, men ingen har ännu gett en säker match mot en fysisk skärmbild.
Blocket får därför inte kallas en verifierad ikonatlas eller palett.

`0x001000` och `0x002000` innehåller två byte-identiska, mycket glesa
4-KiB-sektorer. De första 48 byten ser ut som parametrar eller tabellvärden;
resten är noll. Deras funktion är okänd.

Det finns inga identifierade PNG-, JPEG-, BMP- eller GIF-signaturer och ingen
bevisad bildresurstabell. Det är fullt möjligt att ikoner och typsnitt ligger i
MCU:ns interna flash eller ritas som primitiver. Studio visar därför alla
råpixeltolkningar som **hypoteser**, aldrig som extraherade originalbilder.

## Områden som inte får patchas ännu

- `0x003200–0x0035FF`: blandad strukturerad data före språkbankerna.
- `0x380000–0x381FFF`: gles metadata/status.
- `0x383000–0x383FFF`: beständiga poster, möjligen resultat, inställningar
  eller kalibrering.

Särskilt `0x383000` hålls helt utanför UI-patchar tills fälten har korrelerats
mot kontrollerade ändringar på apparaten.
