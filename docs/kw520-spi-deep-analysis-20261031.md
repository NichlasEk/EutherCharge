# KW520: fördjupad analys av externflashen

## Resultat

Analysen kördes läs-only på referensdumpen. Filstorlek och SHA-256 matchar den
verifierade 4-MiB-kopian. Det starkaste nya fyndet är en komplett resursdirectory
vid `0x003200` och ett gemensamt CRC-format för flera andra poster.

Maskinläsbart resultat finns lokalt i
`build/kw520-jlink-20261031/spi-deep-analysis.json`. Det kan återskapas med:

```sh
python3 tools/analyze_kw520_spi.py \
  dumps/original/kw520-1.0.1-original-d369a860.bin \
  --json build/kw520-jlink-20261031/spi-deep-analysis.json
```

## Resursdirectoryn är nu verifierad

`0x003200` innehåller värdet `8`. Efter detta ligger en gles tabell av
19-byteposter, indexerad med språk-ID. De åtta aktiva platserna är ID
`3, 4, 5, 6, 7, 8, 10, 14`; postens första byte är alltid samma som
platsnumret. Oanvända platser är `FF`.

Varje aktiv post innehåller tre offset/count-par:

| Resursklass | Antal per språk | Verifierad tolkning |
|---|---:|---|
| 1 | 162 | fyrabytespekare till vanliga längdprefixerade UI-strängar |
| 2 | 1 | en sjubytes DTC-post: `u24be code` + `u32be string_pointer` |
| 3 | 0 | samma slutoffset `0x821e`; ingen aktiv post att tolka |

Alla offset är relativa till `0x003200`. De åtta klass-1-tabellerna träffar
exakt de redan kända språkbankerna. Samtliga 1 296 poster validerar som
stigande pekare till `u16be length` följt av NUL-terminerad data.

Klass 2 är nu också verifierad. Dess enda 24-bitars kod är noll och pekaren
leder till respektive språks `P0000 ...`-text. Tabellen börjar vid angiven
offset och varje post är exakt sju byte. Detta förklarar området efter den
sista vanliga nederländska strängen; det är en separat DTC-resursklass och inte
åtta lösa specialsträngar.

Klass 3 har antal noll för alla språk. Dess gemensamma offset är därför bäst
tolkad som slutet på den aktiva resursrymden, inte som bevis för en tredje
datatyp. Sex textliknande restbyte efter den sista giltiga DTC-strängen är
orefererade och kan vara kvarlämnad generator- eller redigeringsdata.

## Gemensam integritetskontroll upptäckt

Flera poster utanför språkbankerna börjar med en varierande byte följd av
markören `A5`. Den första byten är CRC-8/SAE-J1850 över resten av posten:

```text
polynom  0x1D
init     0xFF
xorout   0xFF
refin    false
refout   false
```

Följande postgränser validerar exakt:

| Offset | Längd | Förekomst |
|---:|---:|---|
| `0x001000` | 60 | kopia 1 av okänd konfiguration |
| `0x001280` | 20 | kopia 1, andra posttypen |
| `0x002000` | 60 | byte-identisk kopia 2 |
| `0x002280` | 20 | byte-identisk kopia 2 |
| `0x380000` | 10 | okänd metadata/status |
| `0x381000` | 8 | okänd metadata/status |
| `0x383000 + n*52` | 52 | fyra historikposter |

Detta är stark evidens eftersom samma CRC-parametrar validerar tio självständiga
poster med flera olika längder och innehåll. Det bevisar postgränserna, men ännu
inte vad konfigurations- och metadatafälten betyder.

## Negativa fynd

- Bara 15 av 1 024 sektorer innehåller något annat än `FF`.
- De använda sektorintervallen är fortsatt `0x000000–0x00bfff`,
  `0x380000–0x381fff` och `0x383000–0x383fff`.
- Endast sektorerna vid `0x001000` och `0x002000` är identiska bland de använda
  sektorerna.
- Inga signaturer för gzip, xz, zip, 7z, LZ4-frame, SquashFS, ELF, UF2, PNG,
  JPEG eller BMP hittades.
- Ingen normal Cortex-M-vektortabell hittades.
- Ingen vanlig CRC32-tabell hittades.
- Den generella offsetskanningen hittade de åtta verkliga språkbankerna. Övriga
  korta monotona träffar är byteförskjutna vyer genom dessa tabeller och
  validerar inte mot längdprefixerade poster.

Det finns alltså fortfarande inget som pekar på att hela eller delar av
MCU-firmwaren redan ligger paketerad i externflashen. Vägen in är i så fall
originalprogrammets behandling av extern data.

## Vad fynden betyder för en möjlig väg in

Directoryn ger fler kontrollerbara parserfält än vad vi tidigare kunde bevisa:

1. språk-ID och gles plats;
2. tre tabelloffset;
3. tre antal;
4. vanliga fyrabytespekare och stränglängder;
5. DTC-kod, DTC-pekare och DTC-antal.

Det mest lovande är inte att skriva en internflashadress i en SPI-pekare.
Pekarna är uttryckligen relativa externflashoffset. Det lovande är att tabellens
offset och antal kan visa hur noggrant originalprogrammet kontrollerar sina
gränser. Om ett antal används utan kontroll kan programmet börja tolka en
närliggande struktur som tabellposter. Det kan i bästa fall ge kontrollerad
läsning eller styrning; i sämsta fall bara en krasch.

CRC-fyndet visar dessutom att konfigurations-, status- och historikposterna har
en gemensam serialiseringsrutin. Att kunna skapa en giltig CRC gör framtida
fältförsök mer diskriminerande: ett avvisat prov kan då inte lika lätt förklaras
av trasig kontrollsumma. Dessa poster kan påverka mät- eller laddlogik och är
därför senare och känsligare testytor än språkdirectoryn.

## Rangordnade fysiska testkandidater

1. Omdirigera en vanlig, ofarlig menytexts pekare till en annan giltig text i
   samma bank. Detta bevisar tabelluppslag och återställningskedjan med liten
   risk.
2. Omdirigera samma pekare till en giltig post i en annan språkbank. Detta
   verifierar att offsetbasen är global och inte bankbegränsad.
3. Visa `P0000` och ändra bara dess DTC-pekare till en annan giltig sträng. Det
   bevisar den nya sjubytes DTC-tolkningen på apparaten.
4. Öka DTC-antalet från ett till två först när DTC-sidan kan aktiveras
   reproducerbart och flashen kan återställas via J-Link. Den andra sjubytes
   posten ska då placeras uttryckligen i en testsektor; befintlig efterföljande
   text får inte användas som slumpmässig tabellpost.
5. Antal- och längdgränser i klass 1 provas sist. Ett fruset gränssnitt ger bara
   en felgräns; en användbar väg kräver att kontrollerad data kan observeras.

## Slutsats

En djupare dumpanalys gav faktiskt en bättre väg framåt. Vi har nu en bevisad
överordnad parserstruktur och en kontrollsummealgoritm, vilket gör riktade tester
möjliga. Vi har ännu ingen läsprimitiv, kodexekvering eller intern firmwaredump.
Nästa tekniska spärr är stabil läsning och återställbar skrivning av EN25Q32 via
den befintliga J-Link/SWD-anslutningen.

## Fysisk parserstatus 2026-11-01

Den spärren är nu passerad för den externa EN25Q32-flashen. J-Link kan köra en
CRC-låst SRAM-hjälpare, läsa/skriva exakt sektor `0x003000`, verifiera hela
sektorn och återställa statusregistret. Följande har dessutom bekräftats på den
fysiska laddaren med full återställning efter varje prov:

- samma-bank-pekaren gav `Testa`;
- en giltig pekare över språkbankgränsen gav `Menu principal`;
- deklarerad längd 8 på `Huvudmeny\0` gav exakt `Huvudmen`;
- en isolerad post i verifierad nollpadding gav först `SAFE` vid längd 4 och
  sedan `SAFEWXYZ` vid längd 8, när endast längdbyten ändrades mellan stegen.

Det sista provet visar att en måttlig längdökning inom en helt kontrollerad,
giltig externflashpost fungerar. Det visar inte att pekare eller längder får gå
utanför EN25Q32, och det är fortfarande ingen läsning av FAP-skyddad intern
flash. Nästa prov måste därför skapa en ny observerbar skillnad utan att anta
att en krasch eller frysning är en läsprimitiv. Den befintliga DTC-posten är
fortsatt en bättre kandidat än en godtycklig ogiltig pekare.

En efterföljande read-only-jämförelse av två fulla 16 KiB-SRAM-bilder kartlade
dessutom strängvägen. `Huvudmeny` och `SAFEWXYZ` använder samma källbuffert
`0x20003978` och renderkopia `0x20003728`. Slutpekaren vid `0x20003710` ändras
exakt `0x20003981 -> 0x20003980`, i takt med nio respektive åtta synliga byte.
Råa SRAM-bilder ligger bara lokalt; publicerad evidens innehåller hash, adresser
och minimala skillnadsintervall. Detta ger fasta mål för vidare gränsmätning,
men bevisar ännu inte buffertstorlek eller overflow.

Den befintliga största giltiga posten användes sedan utan någon payload- eller
längdändring. Titelpekaren flyttades till Russian-custom post 111 vid `0x007ec2`:
allokering 113, 112 payloadbyte plus NUL. På LCD:n syntes en lång klippt rad med
tecken medan resten av huvudmenyn ritades normalt. En read-only-SRAM-fångst
hittade hela payloaden plus NUL exakt en gång, vid samma beständiga källbuffert
`0x20003978`. Den tidigare korttitelkopian vid `0x20003728` var nollställd vid
denna fångst och ska därför behandlas som övergående. Detta kvalificerar den
kända legitima formatmaxgränsen på källvägen, men säger fortfarande inget om
säkerheten över 113 byte.
