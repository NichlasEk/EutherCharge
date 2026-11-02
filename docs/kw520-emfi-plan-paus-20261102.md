# KW520: EMFI-plan och paus — 2026-11-02

## Beslut

Vi arbetar med möjligheter och drömmar, inte krav på garantier. Målet är att
bevara och läsa originalfirmware och använda kunskapen för egen firmware.
Experimenten ska dokumenteras så att vi kan skilja fungerande metoder från
antaganden.

**Användaren pausar denna del av projektet tills den nya utrustningen finns
på plats.** Inga fler hårdvaru-, SWD- eller felinjiceringsförsök inom detta
spår under pausen. Övriga delar av EutherCharge är inte automatiskt pausade.

## Köpt utrustning enligt användaren

- **Faulty Cat V2.1**, EMFI-verktyg baserat på PicoEMP, köpt från
  **Neven i Tjeckien**.
- **AT-START-F421 V1.2**, utvecklingskort med **AT32F421C8T7**,
  samma MCU-modell som identifierats i laddaren.

När Faulty Cat anländer ska faktisk hårdvarurevision och installerad firmware
kontrolleras **innan styrprogram och anslutningar väljs**. Verifiera även
utvecklingskortets revision och MCU-märkning. Inköpsuppgifterna ovan är ännu
inte kontrollerade mot de fysiska exemplaren.

## Forskningsspår

Användaren anger publikationen *Unlock the Door to my Secrets, but don’t
Forget to Glitch*, **CHES/TCHES 2024**, och **CVE-2024-21740**.
Enligt användarens sammanfattning lyckades forskarna med **EMFI på
AT32F421C8T7**, medan deras **spänningsglitchförsök inte lyckades**.

Uppgifterna är sparade som ett forskningsuppslag, inte som en självständigt
verifierad litteraturgenomgång i denna anteckning. Granska originalpublikation
och tillhörande artefakter vid återstart. Skilj forskarnas resultat från
utrustningens faktiska stöd och våra egna resultat.

## Arbetsplan efter leverans

1. Inventera hårdvara, revisioner, firmware och kompatibla styrprogram.
   Dokumentera märkningar och välj anslutningar efter verifierad dokumentation.
2. Börja på **utvecklingskortet med egen firmware**. Spara källkod,
   bygginställningar, exakt programmerad bild och återställningsförfarande.
   Kontrollera normal programmering, läsning och körning först.
3. Skapa ett känt referensinnehåll för **hela flashområdet**, även områden
   utanför programmet. Läs tillbaka och spara bytes samt hash innan
   skydds-/felinjiceringsförsök. Dokumentera skydds- och konfigurationsstatus
   separat från huvudflashens innehåll.
4. Öva **flash erase suppression** enligt granskad forskning och dokumenterad
   utrustning. Målet är att få läsåtkomst med bevarat innehåll.
5. Efter ett möjligt lyckat försök: läs hela flashområdet och jämför
   **byte för byte** mot referensen. Spara hash, eventuella avvikande adresser,
   försökslogg, skyddsstatus och uppstartsresultat. Återställd läsåtkomst
   eller ett fungerande program bevisar inte att alla flashbytes överlevt.
6. Samla erfarenhet från lyckade och misslyckade försök på utvecklingskortet.
   Använd sedan resultaten för en separat försöksplan på laddarens logikkort.
   Inga EMFI-parametrar eller anslutningar för laddaren är beslutade nu.

## Läget när vi pausar

- Intern originalfirmware är **inte säkerhetskopierad**. Skyddade
  flashläsningars nollresultat är inte firmwaredumpar.
- Extern SPI-flash har en tidigare separat dump. Den ersätter inte en kopia
  av MCU:ns interna flash.
- Egen RAM-kod har tidigare körts och berörda SRAM-fönster återställts.
  SRAM, framebuffer och ADC-fönster har kunnat läsas med etablerad debugmetod,
  men originalprogrammet har då låst sig.
- Senaste uppställning: effektkort bortkopplat, separat logikmatning
  **3,30 V**, strömgräns **0,10 A**, förbrukning omkring **0,04 A** enligt
  användaren. J-Link SWD, serienummer **69401338**.
- Senaste CSW-testet startade med ren DP-status efter full strömcykling.
  Systemdomänen aktiverades utan debugdomänen; AP0 CSW lästes som noll.
  CSW-skrivning `00000002` fick ACK=1, men nästa DP-status blev `c0000060`
  mot tidigare `c0000040`: **ny STICKYERR**.
- Det granskade verktyget stoppade före fler AP-operationer. Ingen RAM- eller
  flashåtkomst gjordes i detta test. Användaren bekräftade därefter att
  **menyn fortfarande svarade**. Senare full strömcykling är inte bekräftad.
- Ingen fungerande SRAM-åtkomst utan debugdomänen är etablerad. Det är ett
  resultat för de testade vägarna, inte ett bevis att alla vägar är stängda.

## Filer och versionsstatus

- [Övergripande handoff](../HANDOFF.md).
- [Prob, knappkarta och försöksresultat](../firmware/kw520-probe/README.md).
- [Tidigare probhandoff](kw520-probe-handoff-20261101.md).
- [Debugisolering](kw520-debug-isolation-20261031.md).
- Lokala råartefakter i `build/kw520-board-probe/` och
  `build/kw520-jlink-20261031/`. Bevara dessa. Privata firmware- och
  minnesdumpar ska inte följa med i publika commits.
- Senast i sessionen bekräftade push: **6bc7003**, prob och knappkarta.
  ADC-/CSW-arbete, tester och pausdokumentation ingår i den efterföljande
  checkpoint som användaren begärt att committa och pusha. Rådumpningar
  förblir lokala.
- Git används med `git --git-dir=.git-local --work-tree=.`. Repot har många
  orelaterade ändringar; välj filer avgränsat vid nästa commit.

## Återstart

När användaren meddelar att utrustningen kommit: börja med inventering och
originalpublikationen. Gör inte ett automatiskt återförsök av gammal
CSW-skrivning. Kontrollera då aktuell fysisk koppling och matning; dagens
uppställning ska inte antas vara oförändrad.
