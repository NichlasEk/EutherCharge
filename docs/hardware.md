# Hårdvarunoteringar

## Observerad märkning

Den urplockade kretsen har rapporterats som `032C-104HOP`. Ingen bild eller
kapselmätning finns ännu i repot.

Den 18 oktober 2026 identifierade `flashrom` 1.6.0-devel kretsen som
`Eon EN25Q32(A/B)` med ID `1c 30 16` och kapaciteten 4096 KiB. Det ersätter den
tidigare hypotesen `PM25LQ032C`. EN25Q32A-databladet anger 2,7–3,6 V,
256-byte sidor och 4-KiB sektorer. Exakt A/B/C-revision är ännu inte verifierad
mot märkningen.

Tre första läsningar hade rätt storlek men olika SHA-256 och ungefär 95 000
skilda byte per filpar. Första skillnaden låg vid `0x5000`. Dessa filer är
diagnostik och får **inte** användas som backup eller skrivunderlag.

Efter ytterligare CH341A-försök användes en TL866A med `minipro` 0.7.4 och
profilen `EN25Q32A@SOP8`. Tre kompletta läsningar gav identiskt innehåll och
SHA-256 `d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2`.
Det är den enda godkända originaldumpen. Den identifierar produkten som
`KONNWEI`, `KW520`, firmwareversion `1.0.1`.

Huvudprocessorn har rapporterats vara `AT32F421C8T7` (ARM Cortex-M4), men den
uppgiften är ännu inte verifierad mot ett skarpt kortfoto eller en read-only
debuggeridentifiering. Ingen intern MCU-flash har lästs. Se
[internal-flash-access.md](internal-flash-access.md) för SWD-pinout,
anslutningsordning och stoppvillkor.

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
- Läs statusregistren utan att ändra dem. Första proben rapporterade `0xff`,
  vilket tillsammans med instabila läsningar motiverar kontroll av kontakt och
  matning innan nästa försök.
- Spara programmerarens identifieringsutskrift i en lokal labblogg.

CH341A-kort finns i flera revisioner. Färg eller produktnamn är inte bevis på
att signallogiken och VCC är 3,3 V.

## Återställningsgrind

Radering eller skrivning får inte ske förrän:

1. kretsen är identifierad,
2. tre läsningar är identiska,
3. minst två backupkopior med samma SHA-256 finns på olika lagringsmedia, och
4. en återläsning efter programmering kan göras med samma programmerare.
