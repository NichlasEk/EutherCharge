# Hårdvarunoteringar

## Observerad märkning

Den urplockade kretsen har rapporterats som `032C-104HOP`. Ingen bild,
JEDEC-avläsning eller kapselmätning finns ännu i repot.

`032C` stämmer med kapacitetsdelen i artikelnumret `PM25LQ032C`. Den kretsen är
en 32-Mbit (4 MiB) SPI-NOR för 2,7–3,6 V, med 256-byte sidor och 4-KiB sektorer.
Detta är en **arbetshypotes**, inte identifierad hårdvara. Förväntat JEDEC-ID
för kandidaten anges i tillgängliga källor som `9d 00 46` (ibland rapporterat
med en JEP106-fortsättningsbyte eller som `9d 46`).

## Vanlig SOIC-8 SPI-NOR-pinout

Använd endast tabellen efter att kapsel, datablad och pin 1 har verifierats.

| Pin | Vanlig funktion |
|---:|---|
| 1 | `/CS` |
| 2 | `DO` / `IO1` |
| 3 | `/WP` / `IO2` |
| 4 | `GND` |
| 5 | `DI` / `IO0` |
| 6 | `CLK` |
| 7 | `/HOLD` eller `/RESET` / `IO3` |
| 8 | `VCC` |

## Innan första läsningen

- Kontrollera hela märkningen under bra ljus och makrofoto.
- Mät kapselbredd och identifiera pin-1-markeringen.
- Bekräfta programmerarens verkliga VCC med multimeter.
- Börja med låg SPI-klocka om kontakten är osäker.
- Läs statusregistren utan att ändra dem.
- Spara programmerarens identifieringsutskrift i en lokal labblogg.

CH341A-kort finns i flera revisioner. Färg eller produktnamn är inte bevis på
att signallogiken och VCC är 3,3 V.

## Återställningsgrind

Radering eller skrivning får inte ske förrän:

1. kretsen är identifierad,
2. tre läsningar är identiska,
3. minst två backupkopior med samma SHA-256 finns på olika lagringsmedia, och
4. en återläsning efter programmering kan göras med samma programmerare.
