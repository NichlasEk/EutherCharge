# EutherCharge

Öppen, reproducerbar forskning och verktyg för att analysera och modifiera
firmware i batteriladdaren **KONNWEI KW520**.

Projektet utgår från ett urplockat 8-bens flashminne märkt
`032C-104HOP`. Märkningen är **inte ännu verifierad** som ett komplett
artikelnummer. Den starkaste kandidaten är `PM25LQ032C`, ett 32-Mbit
(4 MiB) SPI-NOR-minne för 2,7–3,6 V. Läs JEDEC-ID från kretsen innan du väljer
krets i programmeraren.

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
- [ ] Foto och kapselmärkning dokumenterade
- [ ] JEDEC-ID verifierat från den fysiska kretsen
- [ ] Tre identiska originaldumpningar arkiverade lokalt
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

# Inspektera storlek, hash, entropi, strängar och tomma områden.
python3 tools/fwtool.py inspect dumps/read-1.bin

# Kontrollera kandidatens JEDEC-ID (exempelvärdet är inte ett mätresultat).
python3 tools/fwtool.py identify 9d0046

# Skapa en ny fil med en kontrollerad, längdbevarande patch.
python3 tools/fwtool.py patch dumps/read-1.bin build/modified.bin \
  --patch 0x1234:01020304:aabbccdd
```

`patch` ändrar aldrig källfilen. Varje patch kräver både förväntade gamla byte
och nya byte, och skapar en JSON-manifestfil med SHA-256 för källa och resultat.

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
- [PM25LQ032C sammanställning och JEDEC-ID](https://spiflash.readthedocs.io/en/latest/chips/9d0046.html)
- [flashrom-dokumentation](https://flashrom.org/)

## Licens

Källkod och dokumentation i detta repo publiceras under [MIT-licensen](LICENSE).
Detta omfattar inte firmware från enheten eller andra filer som ägs av tredje
part.
