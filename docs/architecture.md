# EutherCharge-arkitektur och experimentgränser

## Vad som är bevisat

- Externflashen är en 4 MiB Eon EN25Q32A/B med JEDEC-ID `1c 30 16`.
- Tre TL866A-läsningar är byte-identiska.
- Externflashen är främst en gles resurs- och datalagring, inte en igenkänd
  körbar ARM-image.
- Åtta språkbanker med totalt 1 296 poster är strukturellt validerade.
- Laddar-, temperatur- och skyddskod har inte lokaliserats i externflashen.

MCU:n har uppgivits vara en Artery AT32F421C8T7. Arterys officiella material
beskriver AT32F421-familjen som Cortex-M4 upp till 120 MHz med upp till 64 KiB
intern flash, 16 KiB SRAM, ADC, timers, SPI, I²C och USART. Den exakta
kortkopplingen, kapselmärkningen och readout-protection-statusen är ännu inte
verifierade i projektet.

Officiell dokumentation: [Artery AT32F421 product page](https://www.arterychip.com/en/product/AT32F421.jsp).

## Trolig systemdelning — ännu en hypotes

```text
AT32F421 intern flash
  ├─ start, huvudloop och UI-rendering
  ├─ mätning, laddreglering och skydd
  ├─ display-/fläktdrivrutiner
  └─ SPI-läsare för externa resurser
              │
              ▼
EN25Q32 extern flash
  ├─ startlogga och språkresurser    [verifierat]
  ├─ övrig färg-/displaydata         [möjligt]
  └─ historik/inställningar          [möjligt]
```

Diagrammet är en arbetsmodell, inte bevis för var varje funktion ligger.

## Plan för intern firmware

Nästa hårdvarufas är read-only kartläggning:

1. dokumentera båda kortsidor, MCU-märkning, testpads och alla kablage;
2. identifiera GND och matning med spänningslöst kort;
3. spåra tänkbara SWDIO/SWCLK/RESET utan att ansluta nätspänning;
4. anslut isolerad debugger och läs endast chip-ID samt option/read-protection;
5. om och endast om skyddsnivån medger icke-destruktiv läsning: gör tre
   interna flashdumpningar och jämför hash;
6. utför aldrig unlock, mass erase eller option-byte-skrivning för att få en dump.

Utan intern MCU-image går det inte att sanningsenligt identifiera displaybuss,
framebuffer, fan-PWM, temperatursampling eller en säker kodhook. De ska hittas
med disassembly och verifieras med logikanalys/oscilloskop på isolerad
testhårdvara.

## UI-strategi

### Nivå A — extern resursersättning, implementerad

- fastallokerad svensk textbank;
- verifierad ersättning av den befintliga 128×32-startloggan;
- fullständig ändringsmanifest och hash;
- ingen ändring utanför startloggan och engelska strängpayloads;
- simulator för teman och nya informationsvyer.

### Nivå B — intern UI-hook, kräver MCU-dump

- hitta displayens initiering och draw/text-rutiner;
- hitta SPI-resursläsaren och dess adressanrop;
- ersätt endast presentationslagret;
- behåll mätning, laddtillstånd, kalibrering och skydd byte-identiska;
- mata UI med observerade mätvärden och märk okända värden som otillgängliga.

### Nivå C — egen UI-task

En egen UI-task är möjlig först om vi kan visa att den får schemaläggas utan
att påverka styrloopens timing, watchdog eller interrupts. Externflashens stora
tomma område kan lagra resurser, men det är inte bevisat att MCU:n kan exekvera
kod därifrån. En realistisk lösning kan kräva en liten intern hook som läser
resurser från SPI-flashen.

## Mätvärdeskontrakt

Simulatorvärden är alltid märkta `SIMULERING`. På fysisk hårdvara får en ruta
bara heta spänning, ström, temperatur eller fläktprocent om källvariabeln har
spårats till motsvarande ADC-/timerkanal och jämförts mot extern mätning.
Härledda värden ska märkas `beräknad`; okända värden visas som `—`.

## Fan Hymn

Nuvarande Fan Hymn använder Web Audio i Studio och styr ingen laddarhårdvara.
En fysisk implementation får endast aktiveras när följande kan bevisas:

- separat, avbrytbart demo-läge utan pågående laddning;
- temperaturregleringen har högre prioritet än musikmönstret;
- övertemperatur ger omedelbar full fläkt och avslutar demon;
- knapptryck, timeout och watchdog avslutar demon;
- PWM-frekvens och tillåtet duty-område är uppmätta på originalfirmware;
- fläkten stannar aldrig i ett termiskt otillåtet område.

## Fysisk teststege

1. Simulator och parsertester.
2. Statisk diff: endast tillåtna UI-byte.
3. Programmera reservkrets eller isolerad testhårdvara och läs tillbaka.
4. Starta med laboratoriematning och strömgräns, utan batteri och nätspänning.
5. Verifiera display, knappar och alla språkposter.
6. Separat granskning innan någon energibärande laddtest sker.

Den nu genererade svenska imagen har inte passerat steg 3–6 och är därför inte
godkänd för installation i den fungerande laddaren.
