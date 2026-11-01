# KW520: plan för SPI-analys och skyddad firmwareutvinning

## Målet

Målet är att undersöka om KW520:s externa EN25Q32-flash kan användas som en
kontrollerad in- och utkanal för originalprogrammet i AT32F421C8T7. Den önskade
slutkedjan är:

```text
analyserad SPI-struktur
  -> liten reproducerbar resursändring
  -> bevisad parserreaktion
  -> läs- eller exekveringsprimitiv
  -> intern firmware kopieras ut
  -> kopian verifieras byte för byte
```

En krasch, frusen meny eller trasig text är inte i sig en utvinning. Varje steg
måste visa en ny, tydligt avgränsad förmåga innan nästa steg påbörjas.

## Kända utgångspunkter

- MCU:n är AT32F421C8T7 och internflashens lässkydd är aktivt.
- J-Link kan läsa SWD-identitet, men begäran om debugdomänen har försatt
  originalprogrammet i HardFault/lockup. Vanlig OpenOCD-anslutning är därför
  inte en passiv operation.
- Externflashen är EN25Q32(A/B), 4 MiB, JEDEC `1c 30 16`.
- Referensdumpen har SHA-256
  `d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2`.
- Tre TL866A-läsningar var byte-identiska. Denna referens får aldrig skrivas
  över.
- Språkbankernas 1 296 poster och pekartabeller är verifierade. En svensk
  resursimage har tidigare skrivits, lästs tillbaka och startat på apparaten.
- En ändrad logobild syntes inte i det observerade startflödet. Dess aktiva
  användning är därför obevisad.
- J-Link kan nu köra en strikt avgränsad SRAM-rutin via SWD-headern. Den har
  läst EN25Q32-ID `1c 30 16`, matchat 16 kända byte och beräknat hela den
  installerade 4-MiB-imagens CRC-32B `268f3bd7`.
- En fixerad tvåbytesändring i sektor `0x003000` har programmerats, verifierats
  och observerats på verklig LCD som `Huvud%%ny`. Exakt backup återställde
  sektor-CRC `f5c23372`, status `0x18` och normal `Huvudmeny` efter kallstart.
- Provet visar literal textrendering på denna resursväg. Det gav ingen
  formatsträngstolkning och ingen väg till MCU:ns skyddade internflash.
- Ett separat pekarprov ändrade endast tabellpost 1 från `Huvudmeny`-posten
  till den befintliga `Testa`-posten i samma bank. Fysisk kallstart visade
  `Testa`; efter exakt återställning visade apparaten åter `Huvudmeny` och
  knapparna fungerade. Samma-bank-pekarföljning är därmed fysiskt bevisad.
- Samma tabellpost pekades därefter till en giltig `Menu principal`-post i
  Français-banken. Displayen visade exakt den franska texten och återgick till
  fungerande `Huvudmeny` efter exakt återställning. Pekaren begränsas alltså
  inte till den aktiva språkbankens intervall.
- Rubrikpostens deklarerade längd kortades därefter från 10 till 8 utan ändrad
  payload eller pekare. Två separata kallstarter visade exakt `Huvudmen`.
  Originalfirmwaren använder alltså längdvärdet som synlig payloadgräns och
  skannar inte enbart fram till det oförändrade avslutande NUL-tecknet.

## Arbetsordning och beslutspunkter

### Fas 1 – djup offlineanalys av hela SPI-dumpen

Arbetet kan göras nu och påverkar inte hårdvaran.

1. Gör en karta per sektor och block över entropi, fyllnadsbyte, strängar,
   identiska block och återkommande strukturer.
2. Sök efter 16- och 32-bitarsvärden i båda byteordningarna som pekar in i
   använda områden. Gruppera endast sammanhängande serier med rimlig riktning
   och steg; enstaka tal är för svaga som bevis.
3. Sök efter filsignaturer, kompressionshuvuden, checksummefält och kandidater
   till längd–offset–typ-tabeller.
4. Jämför de åtta språkbankerna strukturellt. Variation i postlängd och avstånd
   kan avslöja om tabellen beskriver allokering, faktisk textlängd eller båda.
5. Analysera de två lika sektorerna vid `0x001000` och `0x002000`, området
   `0x003200–0x0035ff`, metadata vid `0x380000–0x381fff` och historik vid
   `0x383000` separat.
6. Sök efter versionsfält, uppdateringsmarkörer, hash-/CRC-tabeller och data som
   kan vara kodad eller komprimerad, utan att anta att hög entropi är kod.
7. Spara analysen som maskinläsbar JSON och ett kort dokument med evidens,
   motexempel och nästa diskriminerande test.

**Gå vidare när:** minst en ny struktur kan beskrivas med exakta offset,
fältbredder och verifierbara samband, eller en känd språkpost har valts för ett
ofarligt parserprov.

**Stanna i denna fas när:** ett fynd bara bygger på utseende eller enstaka
träffar. Det märks då som kandidat och används inte till en skrivimage.

### Fas 2 – transport genom J-Link till externflashen

**Status 2026-10-31: genomförd för kvalificerad läsning.** PA8 är `/CS` och
PB13/PB14/PB15 används av SPI2. SRAM-bryggan och dess återställning är fysiskt
verifierade. Hela 4 MiB har fingeravtryckts mot känd image; en full byte-dump
över denna väg är möjlig men behövs inte för nästa parserprov.

SEGGER beskriver två principiella metoder. Direkt metod kräver anslutning till
SPI-signalerna. Indirekt metod går via SWD och en kort, kortspecifik rutin i
MCU:ns RAM. Den befintliga headern räcker alltså bara om vi får kontrollerad
åtkomst till MCU:ns RAM/periferier under lässkyddet.

Förstahandsförsöket är en egen, liten SWD-brygga:

1. Identifiera MCU-ben och SPI-instans från kretskortets ledningsdragning eller
   försiktiga logiska observationer. Inga GPIO-utgångar får gissas.
2. Testa om MEM-AP kan läsa och skriva ett avgränsat SRAM-ord när CPU:n är i ett
   kontrollerat underhållsläge. Spara och återställ ordet.
3. Om SRAM-exekvering fungerar, bygg en minimal rutin med kommandon för
   `JEDEC-ID`, status, läsning, sektor-radering och sidprogrammering. Skrivning
   hålls avstängd i första versionen.
4. Läs JEDEC-ID och några kända signaturer. Läs sedan hela 4 MiB två gånger och
   kräv identiska SHA-256 innan någon skrivfunktion aktiveras.
5. Om RAM-rutinen inte går att köra, prova registerstyrd SPI endast efter att
   korrekt periferienhet och pinmux är bevisade.
6. Om båda vägarna faller stannar J-Link-spåret. Reservvägen blir en enda
   permanent, avlastad anslutning eller klämma till SPI-signalerna; inte
   upprepade varmluftscykler.

Under transportutvecklingen ska batteri och effektsteg vara ur funktion och
kortet ha kontrollerad logikmatning. CPU-lockup räknas inte som bevis för att
alla utgångar är ofarliga.

**Gå vidare när:** aktuell externflash kan läsas två gånger genom den nya vägen
och läsningarna är identiska. Den aktuella installationen sparas separat från
den äldre originaldumpen.

**Stoppvillkor:** oväntad matningsnivå, okänd pinmux, instabil läsning, ändrat
JEDEC-ID, busstrid, eller att en operation skulle kräva upplåsning/massradering
av MCU:n.

### Fas 3 – återställbar skrivning av externflash

**Status 2026-10-31: genomförd för exakt sektor `0x003000`.** EN25Q32(A/B)
startade med status `0x18` och blockskyddsläsning `0xff`. Skyddet öppnades med
statusregisterskrivning `0x00`, provet programmerades, och status `0x18`
återställdes. Återställningsrutinen raderade endast den fixerade sektorn,
programmerade 16 sidor och verifierade original-CRC före normal kallstart.

1. Jämför den aktuella flashen mot både originaldumpen och den verifierade
   svenska imagen. Skilj resursändringar från levande historik/metadata.
2. Välj en 4-KiB-sektor som innehåller en känd, icke säkerhetskritisk menyresurs.
   Läs och spara sektorn precis före försöket.
3. Gör en ändring inom befintlig allokering, programmera en sida i taget och
   kontrollera WIP/timeout efter varje kommando.
4. Läs tillbaka hela sektorn och kräv exakt förväntad hash.
5. Starta apparaten, observera en enda förutsagd skillnad och återställ sedan
   sektorn. Gör full av/på-start efter återställning.

Ingen chip erase används. Ett misslyckat sidprogram följs av läsning och
jämförelse; det följs inte automatiskt av fler skrivförsök.

### Fas 4 – kartlägg parserns beteende

**Fysiska resultat:** byteparet `6d 65` i `Huvudmeny` ersattes med
`25 25`. Displayen visade exakt `Huvud%%ny`, alltså literal rendering. Efter
återställning visade den åter `Huvudmeny`. Försök inte få denna resursväg att
läcka data med fler printf-specifierare.

Nästa prov omdirigerade endast tabellpostens 32-bitars relativa pekare
`0x00000692 -> 0x0000069e`; inga payload- eller längdbyte ändrades. Displayen
visade den förutsagda befintliga texten `Testa`. Exakt originalsektor och
statusskydd återställdes, varefter `Huvudmeny` och knappar fungerade normalt.
Punkt 1, 2, 3 och den konservativa förkortningen i punkt 4 är genomförda. En
förlängning av längden eller ogiltig offset är en ny riskklass: det kan få
firmware att läsa utanför postens allokering och kräver separat riskgranskning,
nytt utdataargument och ny återställningsplan.

Tester görs ett i taget i stigande intrångsgrad:

1. **Pekaromdirigering inom samma bank:** två vanliga menytexter delar temporärt
   samma giltiga post. Detta visar om MCU:n verkligen följer tabellpekaren.
2. **Pekaromdirigering mellan banker:** en post pekar på en giltig post i en
   annan bank. Detta testar adressbas och eventuella bankgränser.
3. **Literal- eller formatsträng:** en ofarlig post får ett kort `%`-mönster
   inom sin gamla allokering. Skärmen fotograferas exakt; ingen lång sträng
   används.
4. **Deklarerad längd:** ändra längden med minsta möjliga steg medan fysisk post
   och efterföljande data hålls kända. Börja med kortare längd. Längre längd
   provas först när återställning och felbeteende är säkra.
5. **Gränsvärden för offset:** endast adresser som fortfarande ligger i en
   dedikerad testsektor. `0x08000000` är inte ett giltigt direktförsök eftersom
   resurspekaren hittills är ett externt SPI-offset, inte en CPU-adress.

Varje image får ett manifest med bas-hash, ändrade offset, gamla/nya byte,
förväntad observation och återställnings-hash. Skärmfel utan kontrollerbar data
räknas som parserkarta, inte exploatering.

### Fas 5 – från parserfynd till läsprimitiv

Prioritetsordningen är:

1. kontrollerad läsning från ett valt externt SPI-offset;
2. kontrollerad läsning från SRAM eller periferiregister;
3. kontrollerat skrivmål i externflash;
4. styrd exekvering eller återanvändning av kod som redan körs från internflash;
5. läsning av internflash under dess faktiska skyddsregler.

För varje påstådd primitiv krävs en markör som inte redan finns i resursimagen
och som återkommer på ett förutsägbart sätt. Internflash anses inte läsbar förrän
minst två olika kända adresser ger stabila, rimliga och sinsemellan olika data.

### Fas 6 – verifierad firmwarekopia

Om en verklig intern läsprimitiv uppnås:

1. Inventera och bevisa ett utdataområde i externflashen. Raderat innehåll är
   inte ensamt bevis för att området är ledigt.
2. Skriv manifest först: magi, MCU-adress, längd, blocknummer och CRC/hash.
3. Kopiera små block med återläsning och återupptagning. Förväntad internflash är
   64 KiB, men den effektiva firmwaregränsen bestäms från vektortabell och
   innehåll.
4. Läs ut SPI-flashen via den verifierade transporten två gånger.
5. Kräv identiska firmwarehashar och validera Cortex-M-vektorer, kodtäthet och
   adressreferenser innan resultatet kallas firmwaredump.
6. Återställ externflashens testsektorer och bekräfta normal meny efter kallstart.

## Första konkreta arbetspaketet

Det som kan göras utan mer fysisk mätning är:

1. reproducibel fullständig struktur- och entropikarta över referensdumpen;
2. kandidatsökning efter tabeller, kompression, checksummor och redundans;
3. val av en enda icke säkerhetskritisk menytext för pekarprov;
4. generator för testimage och maskinläsbart ändringsmanifest, men ingen fysisk
   skrivning ännu;
5. därefter läs-only J-Link/SPI-brygga med JEDEC-ID som första acceptanskriterium.

## Resultatnivåer

| Nivå | Vad som är bevisat |
|---|---|
| A | Dumpformatet innehåller en ny verifierad struktur |
| B | J-Link kan stabilt läsa externflashen genom kortets MCU |
| C | En extern sektor kan ändras, verifieras och återställas |
| D | Originalfirmwarens parser följer ett kontrollerat fält |
| E | Kontrollerad läsning eller skrivning utanför den normala resursen |
| F | Internflash kan läsas trots skyddet |
| G | Full firmwaredump är dubbel-läst och strukturellt validerad |

Planen står nu på nivå D: transport, fixerad sektorskrivning/återställning,
literal payloadkonsumtion samt pekarföljning inom och mellan språkbanker är
fysiskt bevisade. Deklarerad längd styr dessutom den synliga payloadgränsen vid
förkortning. Proven gav ingen nivå E-primitiv. Längdförlängning, ogiltig offset,
extern gränsöverskridande läsning och varje väg från D/E till internflashnivå F
är fortfarande obevisade.

## Fysisk allokeringsserie och slutåterställning 2026-11-01

Den fixerade testposten provades med allokeringarna 114, 128, 160, 192, 224 och
240 byte. Samtliga renderades av originalfirmwaren och motsvarande SRAM-payload
kontrollerades; 240-byteprovet slutade exakt vid `0x20003a68`, följdes av tre
nollbyte och lämnade den efterföljande kända SRAM-datan oförändrad. Detta är en
fysiskt verifierad övre punkt, inte bevis för obegränsad längd eller en
internflash-läsprimitiv.

Vid den avslutande återställningen hann värdens ursprungliga femsekundersfönster
halvera en sektoroperation. MCU:n hölls därför haltad och apparaten startades
inte. En separat GPIO-bitbang-läsare på PA8/PB13/PB14/PB15 verifierade först
JEDEC `1c3016` och den partiella sektor-CRC:n `33e293e2`. Nästa värdtimeout
inträffade efter åtta färdiga sidor och del av nästa sida; den nya exakta CRC:n
var `559db759` med flashstatus `0x02`. Den slutliga räddningshjälparen var låst
till både denna CRC och status, började med Write Disable och använde ett
40-sekunders övervakningsfönster.

Slutbeviset för pekarsektor `0x003000` var 16 programmerade sidor, CRC
`f5c23372`, status `0x18`, blockskydd `0xff` och noll SPI-fel. Den orefererade
testsektorn `0x00c000` återställdes därefter från CRC `aba2265e` till originalets
all-FF-CRC `f154670a`, också med 16 sidor, status `0x18` och noll SPI-fel. Efter
kallstart visade apparaten `Huvudmeny` och knapparna svarade normalt. Detta är
den fysiska acceptansen för att båda berörda externflashsektorerna är återställda.

## Förberedd stack-frontier efter 240 byte

Nästa serie är avsiktligt fixerad till 256, 320, 384, 448, 480 och 512 byte och
körs aldrig automatiskt. Varje synlig payload består av ett cykliskt
De Bruijn-mönster av ordning fyra med enbart gemener och siffror, utan `%` eller
inre NUL. Alla fyrabytesfönster är unika genom 512 och inget sådant ord ligger i MCU:ns SRAM-, internflash- eller
periferadressintervall. Ett eventuellt PC/LR-värde kan därför mappas tillbaka
till exakt payloadoffset utan att provet avsiktligt tillhandahåller en användbar
hoppadress.

En read-only-baslinje från normal `Huvudmeny` gav SRAM-hash
`89e5cba18e7940ee6ed0b4a72371d0408590f5233599e85a264c552db6e5a18d`.
J-Link-anslutningen utlöste den kända FAP/debug-faulten: MSP `0x20003b88`,
stackad LR `0x08008037` och PC `0x08010000`. Avståndet från den verifierade
källbufferten `0x20003978` till detta MSP-värde är 528 byte. En 512-bytepost
slutar därför 16 byte före den fångade undantagsramen och en 480-bytepost 48
byte före. Detta är ett prioriteringsmått, inte bevis för var den normala
funktionens stackobjekt eller returadress låg före debugfaulten.

Varje steg börjar från all-FF i `0x00c000`, fångar hela SRAM plus kärn- och
faultregister, återställer alltid pekaren först genom en separat GPIO-bitbang-
hjälpare och kallstartar normalmenyn innan datasektorn rensas. Serien stoppas
vid första cykliska kontrollvärdet, ofullständig payloadkopia eller misslyckad
återställning. Verktyg och körordning finns i
`tools/kw520_stack_frontier/README.md`.

### Fysiskt frontierresultat: stopp vid 320 byte

256-byteprovet kopierades byteexakt till `0x20003978`; en andra kopia av
mönstermarkören fanns vid `0x2000059b`. Inget cykliskt fyrabytesvärde fanns i
kärnregistren eller den fångade undantagsramen och
`control_candidate=false`. Pekarsektor och datasektor återställdes därefter
exakt, följt av normal `Huvudmeny` och fungerande knappar.

320-byteprovet gav den diskriminerande gränsen. Displaytexten rullade och
knapparna svarade, men SRAM matchade endast nyttolastens byte 0--255. Byte 256
vid `0x20003a78` var NUL; den efterföljande befintliga SRAM-strukturen började
direkt därefter i stället för de återstående 64 testbytena. Inga cykliska
värden nådde PC, LR, MSP, PSP, MMFAR, BFAR eller undantagsramen och
`control_candidate=false`. Fångstens SRAM-SHA-256 var
`f7548bc9baadf1b2469d1429c75ec27b815565079f92acc5909796d4d5917fcc`.

Återställningen utfördes i säker ordning medan kärnan var stoppad: pekarsektor
`0x003000` gick från test-CRC `6f68933f` till original-CRC `f5c23372`, därefter
gick den orefererade datasektorn `0x00c000` från `41b76a28` till exakt all-FF
`f154670a`. Båda operationerna programmerade 16 sidor, slutade med status
`0x18` och noll SPI-fel. Slutlig kallstart gav normal `Huvudmeny` och fungerande
knappar.

Detta stänger just denna stack-frontier: resursvägen terminerar kopian vid 256
byte och större deklarerade allokeringar 384--512 skulle därför inte föra
kontrollgränsen närmare stacken. Resultatet bevisar inte att alla parser- eller
resursvägar har samma gräns och det ger fortfarande ingen nivå E- eller
internflash-läsprimitiv. Nästa firmwareutvinningsspår måste använda en annan
primitiv än att enbart öka denna posts deklarerade längd.

## Referenser

- Lokal formatbeskrivning: `docs/resource-format.md`
- Lokal parseranalys: `docs/kw520-spi-parser-research-20261031.md`
- SWD-isolering: `docs/kw520-debug-isolation-20261031.md`
- SEGGER, direkt och indirekt SPI-programmering:
  <https://kb.segger.com/SPI_Flash>
