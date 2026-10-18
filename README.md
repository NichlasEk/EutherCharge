# EutherCharge

Öppen, reproducerbar forskning och verktyg för att analysera och modifiera
firmware i batteriladdaren **KONNWEI KW520**.

Projektet utgår från ett urplockat 8-bens flashminne märkt
`032C-104HOP`. `flashrom` identifierar det som **Eon EN25Q32(A/B)** via
JEDEC-ID `1c 30 16`: ett 32-Mbit (4 MiB) SPI-NOR-minne. Revisionen behöver
fortfarande bekräftas mot ett skarpt foto av hela märkningen.

> [!CAUTION]
> KW520 är nätansluten och laddar bly-/litiumbatterier med hög energi. En
> felaktig firmwareändring kan slå ut temperatur-, spännings- eller
> strömbegränsning och orsaka brand, explosion eller elchock. Arbeta endast på
> den urplockade, spänningslösa kretsen. Första tester ska göras med isolerad
> laboratoriematning, strömgräns och konstlast — aldrig med nätspänning och ett
> riktigt batteri.

## Projektstatus

- [x] Säker arbetsgång för dump, jämförelse och spårbar patchning
- [x] Lokalt analysverktyg utan externa Python-beroenden
- [ ] Foto och fullständig kapselmärkning dokumenterade
- [x] JEDEC-ID `1c 30 16` läst från den fysiska kretsen
- [x] Tre identiska originaldumpningar från TL866A arkiverade lokalt
- [ ] Firmwareformat och processor identifierade
- [ ] Första patch definierad och testad på bänk
- [ ] Verifierad återläsning efter programmering
- [ ] Test i fysisk KW520

Ingen originalfirmware eller modifierad firmware ingår i repot.

## Snabbstart

Krav: Python 3.10 eller senare.

```sh
# Kontrollera att tre separata läsningar är identiska.
python3 tools/fwtool.py compare dumps/read-1.bin dumps/read-2.bin dumps/read-3.bin

# Vid instabil läsning: skapa endast en lokal analyskopia från exakt
# 4-KiB-blockmajoritet. Detta ersätter inte en verifierad rådump.
python3 tools/fwtool.py consensus build/consensus.bin dumps/read-*.bin

# Inspektera storlek, hash, entropi, strängar och tomma områden.
python3 tools/fwtool.py inspect dumps/read-1.bin

# Kontrollera det uppmätta JEDEC-ID:t.
python3 tools/fwtool.py identify 1c3016

# Skapa en ny fil med en kontrollerad, längdbevarande patch.
python3 tools/fwtool.py patch dumps/read-1.bin build/modified.bin \
  --patch 0x1234:01020304:aabbccdd
```

`patch` ändrar aldrig källfilen. Varje patch kräver både förväntade gamla byte
och nya byte, och skapar en JSON-manifestfil med SHA-256 för källa och resultat.
`consensus` kräver strikt majoritet för varje block och skapar också ett
manifest, men resultatet får inte användas för återställningsskrivning förrän
det har verifierats mot en stabil programmerare.

## Hårdvaruflöde

1. Fotografera kretsens ovansida, undersida, orienteringsmarkering och kortets
   placering innan mer arbete görs.
2. Använd en 3,3 V-kompatibel SPI-programmerare med SOIC-8-adapter. Mät VCC
   innan kretsen sätts i sockeln.
3. Läs JEDEC-ID. Välj inte kretsmodell enbart från kortmärkningen.
4. Gör minst tre separata dumpningar, gärna efter att kretsen satts om i sockeln.
5. Kör `compare`. Fortsätt endast om alla filer är byte-identiska.
6. Spara minst en orörd backup utanför arbetskatalogen och notera dess SHA-256.
7. Analysera och patcha en kopia. Skriv aldrig över den enda originaldumpen.
8. Programmera, läs tillbaka till en ny fil och jämför mot den avsedda filen.

För den dokumenterade enheten gav CH341A instabila data trots korrekt JEDEC-ID.
Tre läsningar med TL866A och `minipro` blev byte-identiska och är därför
projektets referens. Ett korrekt chip-ID ensamt bevisar inte en korrekt dump.

Se [docs/hardware.md](docs/hardware.md) och
[docs/research-log.md](docs/research-log.md) innan kretsen ansluts.

## Exempel med flashrom

Kommandona nedan är endast mallar. Kontrollera programmerare, matningsspänning
och det identifierade kretsnamnet på din egen arbetsstation.

```sh
flashrom -p ch341a_spi
flashrom -p ch341a_spi -r dumps/read-1.bin
flashrom -p ch341a_spi -r dumps/read-2.bin
flashrom -p ch341a_spi -r dumps/read-3.bin
python3 tools/fwtool.py compare dumps/read-*.bin
```

Lägg aldrig till `dumps/`, `build/` eller firmwarebinärer i Git.

## Avgränsning

EutherCharge är ett reverse-engineering-projekt för egen hårdvara. Det är inte
en officiell KONNWEI-produkt och har ingen koppling till tillverkaren. Bidrag får
inte innehålla proprietära firmwaredumpningar, nycklar eller personuppgifter.

## Källor

- [KONNWEI KW520 användarmanual (TME)](https://www.tme.eu/Document/502a00441a3463319fa611c9cafbe740/KW520.pdf)
- [EN25Q32A datablad](https://www.alldatasheet.com/datasheet-pdf/pdf/313132/EON/EN25Q32A.html)
- [flashrom-dokumentation](https://flashrom.org/)

## Licens

Källkod och dokumentation i detta repo publiceras under [MIT-licensen](LICENSE).
Detta omfattar inte firmware från enheten eller andra filer som ägs av tredje
part.
