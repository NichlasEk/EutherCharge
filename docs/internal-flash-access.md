# Icke-destruktiv åtkomst till AT32F421C8T7

Detta är en read-only-plan för att identifiera och, om skyddsnivån tillåter
det, läsa huvudprocessorns interna flash. MCU-märkningen `AT32F421C8T7` är
ännu användarrapporterad och måste bekräftas med ett skarpt kortfoto innan
något ansluts.

## Utrustning

- AT-Link-EZ rekommenderas; Arterys eget startdokument anger AT-Link och J-Link
  som stödda debugverktyg för AT32F421.
- Multimeter med kontinuitetsläge.
- Pogo-pinnar eller tunn tråd till befintliga testpunkter.
- Isolerad, strömbegränsad laboratoriematning om logikkortet behöver extern
  3,3 V. Nätspänning och batteri ska vara bortkopplade.

TL866CS används för den lösa SPI-flashen men ger inte SWD-åtkomst till den
monterade Cortex-M4-processorn.

## Relevanta pinnar i LQFP48

Följande gäller endast om kapseln verkligen är `AT32F421C8T7` i LQFP48:

| LQFP48-pin | Signal | Användning |
|---:|---|---|
| 34 | `PA13 / SWDIO` | seriell debugdata |
| 37 | `PA14 / SWCLK` | debugklocka |
| 7 | `NRST` | anslutning under reset, rekommenderad |
| 23, 47 | `VSS` | digital jord |
| 8 | `VSSA` | analog jord |
| 1, 24, 48 | `VDD` | digital 3,3 V-rail |
| 9 | `VDDA` | analog 3,3 V-rail |

PA13 och PA14 startar som SWDIO respektive SWCLK efter reset. Identifiera
först pin 1 från kapselns markering och använd databladets vy uppifrån; gissa
inte utifrån kortets orientering.

## Kartlägg testpunkter utan spänning

1. Koppla bort nätkabel, batteri och alla programmerare.
2. Fotografera båda kortsidorna rakt uppifrån i hög upplösning.
3. Kontrollera kontinuitet från MCU-pin 34, 37, 7 och VSS till närliggande
   testpunkter eller kontaktpads.
4. Märk resultaten `SWDIO`, `SWCLK`, `NRST` och `GND` på ett kopierat foto.
5. Mät motstånd mellan 3,3 V-rail och GND innan någon extern matning provas.

Löd helst inte direkt på 0,5-mm-benen om användbara testpads finns.

## Första SWD-sessionen

Anslut i ordningen GND, SWDIO, SWCLK och NRST. Anslut aldrig debugproben till
ett kort som samtidigt matas från laddarens nätaggregat. Använd inte 5 V.
Extern 3,3 V får inte anslutas förrän det är verifierat att den inte bakmatar
eller överbelastar kortets regulator och övriga kretsar.

Första försöket ska använda låg SWD-klocka, exempelvis 50–100 kHz, och
"connect under reset". Tillåtna första operationer är endast:

1. identifiera debugport och MCU;
2. läsa chip-ID;
3. läsa och rapportera skyddsstatus utan att ändra option/user-system-data;
4. om huvudflashen är läsbar: spara `0x08000000–0x0800FFFF` (64 KiB) till en
   ny fil;
5. koppla från, återanslut och gör totalt tre läsningar;
6. jämför filerna byte för byte och med SHA-256.

Originaldumpen ska lagras lokalt under `dumps/` och aldrig läggas i Git.

## Omedelbara stoppvillkor

Avbryt utan ytterligare kommandon om:

- verktyget erbjuder `unlock`, `disable access protection`, `recover`,
  `unprotect`, `erase` eller `mass erase`;
- flashläsningen rapporteras som skyddad;
- anslutning endast lyckas efter att verktyget vill skriva option bytes;
- kortets spänning eller strömförbrukning avviker från förväntad 3,3 V-logik;
- någon del av kortet fortfarande är förbunden med nätspänning.

AT32F421 har både vanlig access protection och en separat sLib-region. En
övergång från lågnivåskydd till oskyddat läge kan massradera huvudflashen.
Skyddet ska därför aldrig avaktiveras på originalprocessorn.

## Adresser för senare analys

| Område | Adress | Storlek | Hantering |
|---|---:|---:|---|
| Huvudflash C8T7 | `0x08000000` | 64 KiB | läs endast om oskyddad |
| SRAM | `0x20000000` | 16 KiB | inte en firmwarebackup |
| Boot-ROM | `0x1FFFE400` | 4 KiB | behöver inte läsas nu |
| User system data | `0x1FFFF800` | 512 byte | rapportera skyddsstatus; skriv aldrig |

## Officiella källor

- [AT32F421 Series Datasheet](https://www.arterychip.com/download/DS/DS_AT32F421_V2.02_EN.pdf)
- [AT32F421 product page](https://www.arterytek.com/en/product/AT32F421.jsp)
- [AT-Link User Manual](https://arterychip.com/download/TOOL/UM0004_AT-Link_User_Manual_EN_V2.1.2.pdf)
- [Artery programming and debug tools](https://arterytek.com/en/support/tools.jsp?index=0)
