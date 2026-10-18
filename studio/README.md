# EutherCharge Studio

Studio är en beroendefri, lokal webbapp. Ingen firmware laddas upp eller följer
med projektet.

```sh
python3 -m http.server 8765 -d studio
```

Öppna sedan `http://127.0.0.1:8765` i Firefox och välj en lokal 4 MiB-dump.

Version 0.1 kan:

- verifiera filstorlek, SHA-256 och alla åtta kända språkbanker;
- visa och redigera 162 textposter per bank;
- skapa längdbevarande patchar utan att flytta pekare eller längdprefix;
- visualisera rådata som flera 1-, 2-, 4-, 8-bpp- och RGB565-hypoteser;
- exportera en ny image och en reproducerbar JSON-ändringsrapport;
- köra fyra nya UI-teman, ELDRÄNG MODE och Fan Hymn som ren simulator.

Den ryska banken är skrivskyddad eftersom teckenkodningen ännu inte är löst.
Grafikvisualiseraren är ett undersökningsverktyg; vald råtolkning är inte ett
verifierat bildformat förrän resultatet matchats mot laddarens fysiska LCD.
