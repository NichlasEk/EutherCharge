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

**Första fysiska resultatet:** byteparet `6d 65` i `Huvudmeny` ersattes med
`25 25`. Displayen visade exakt `Huvud%%ny`, alltså literal rendering. Efter
återställning visade den åter `Huvudmeny`. Försök inte få denna resursväg att
läcka data med fler printf-specifierare; nästa diskriminerande prov bör i
stället vara pekaromdirigering eller deklarerad längd.

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

Planen står nu på nivå C och på en smal nivå D: transport, fixerad
sektorskrivning/återställning och konsumtion av ett kontrollerat textfält är
fysiskt bevisade. Literalprovet gav ingen nivå E-primitiv. Pekarföljning,
gränsöverskridande läsning och varje väg från D/E till internflashnivå F är
fortfarande obevisade.

## Referenser

- Lokal formatbeskrivning: `docs/resource-format.md`
- Lokal parseranalys: `docs/kw520-spi-parser-research-20261031.md`
- SWD-isolering: `docs/kw520-debug-isolation-20261031.md`
- SEGGER, direkt och indirekt SPI-programmering:
  <https://kb.segger.com/SPI_Flash>
