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
