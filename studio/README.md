# EutherCharge Studio

Studio är en beroendefri, lokal webbapp. Ingen firmware laddas upp eller följer
med projektet.

```sh
python3 -m http.server 8765 -d studio
```

Öppna sedan `http://127.0.0.1:8765` i Firefox och välj en lokal 4 MiB-dump.

Version 0.1 kan:

- verifiera filstorlek, SHA-256 och alla åtta kända språkbanker;
- visa originalets verifierade 128×32 KONNWEI-startlogga och ersätta den med EUTHERCHARGE i samma 512-byteformat;
- visa och redigera 162 textposter per bank;
- skapa längdbevarande patchar utan att flytta pekare eller längdprefix;
- visualisera rådata som flera 1-, 2-, 4-, 8-bpp- och RGB565-hypoteser;
- visa de fyra 52-byteposterna vid `0x383000` skrivskyddat, med alla ännu
  overifierade fält tydligt märkta som hypoteser;
- exportera en ny image och en reproducerbar JSON-ändringsrapport;
- köra fyra nya UI-teman, ELDRÄNG MODE och en hörbar Web Audio-version av Fan Hymn som ren simulator.

Den ryska banken är skrivskyddad eftersom teckenkodningen ännu inte är löst.
Grafikvisualiseraren är ett undersökningsverktyg; vald råtolkning är inte ett
verifierat bildformat förrän resultatet matchats mot laddarens fysiska LCD.
