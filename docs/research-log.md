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
