*Zie ook: [[DIY Auto]] · [[DIY Auto Mechanisch]] · [[DIY Auto BOM]] · [[Taken DIY-Auto]]*

# DIY Auto: assemblage

Elke stap beschrijft de linkerkant; rechts is het spiegelbeeld.

## Wat je nodig hebt

- **Geprint:** chassis (één stuk met de neus), 2 motorklemmen, 2 fusees, 2 stuurstangen, servohoorn, 2 servoklemmen, 2 afstandsstukken in ASA; 4 velgen in PLA; 4 banden in TPU 90A.
- **Lagers:** 8× MR105-2RS.
- **Bouten en moeren** (uit `CAD/BOM.md`):
  - achter: 2× M5×40, 2× M5-moer; voor: 2× M5×20, 2× M5-moer, borgmiddel (blauw); 4× schijfje 5×7×0,5 (inox);
  - kingpins: 2× M4×30, 4× M4-moer; stuurstangen: M4×20 (hoornpen), M4×25 + M4×30 (armen), 6× M4-moer;
  - motorklemmen: 8× M3×10; servoklemmen: 4× M3×10; print: 4× M3×6; LM2596: 2× M3×10 + 2× M3-moer.
- **Inserts:** 16× M3×6.
- **Rest:** servo SM-S2309S (zonder hoorn: die wordt geprint), 2 motoren met rondsel, accu ERYNK met een elastiek, de print met de LM2596 en de ESP32.
- **Gereedschap:** soldeerbout met insert-tip, inbussleutels 2 / 2,5 / 3 / 4 mm, steeksleutels 5,5 / 7 / 8 mm.

## 1. Inserts in het chassis

Smelt de 16 inserts in met de soldeerbout op ± 240 °C (ASA). Druk recht en stop zodra de insert gelijk ligt met het oppervlak. Zie [[Threaded Inserts 3D Printing]].
- 8× M3 in de oren van de motorzadels;
- 4× M3 in de 2 servotorens;
- 4× M3 bovenop de printpaaltjes.

Een insert verkeerd gezet: draai er een M3-bout 2–3 slagen in, verwarm de bout met de soldeerbout en trek hem recht uit.

## 2. Neus

Niets te doen: sinds v5 is de neus één stuk met het chassis.

## 3. Lagers in de velgen

Elke velg krijgt 2 lagers, één aan elke kant. Pers ze recht in met een bankschroef en een plankje.
- Te los: een druppel secondelijm op de buitenring.
- Te zwaar: print eerst het [[Testblok passingen]] in PLA en pas `SEAT_D` aan.

## 4. Banden

Trek de TPU-band over de velg. De 3 nokken op de velg vallen in de 3 groeven van de band, zodat de band niet rond de velg kan slippen.

## 5. Motoren

Leg de motor in zijn zadel, met het rondsel naar buiten. Zet de klem erop en draai 4× M3×10 in de inserts. De klem ligt 0,2 mm lager dan de motor, zodat hij de motor vastdrukt.

## 6. Achterwielen

1. Laat een M5-moer van boven in de gleuf van de toren vallen, met de platte kanten naar voren en naar achteren.
2. Houd het wiel tegen de toren, met het grote tandwiel naar binnen in het rondsel.
3. Steek de M5×40 met een schijfje 5×7×0,5 door het wiel en de toren in de moer.
4. Draai de moer goed vast: hij klemt de binnenringen, de bout draait niet mee. Het wiel moet vrij draaien op de lagers.

De bout staat stil en het wiel draait op de twee lagers. Het schijfje en de kraag op de toren raken alleen de binnenring, en die staat ook stil. Een grote ring zou tegen de draaiende buitenring wrijven en het wiel afremmen.

## 7. Moer in de fusee

Druk een M5-moer in de zeskantige holte aan de binnenkant van de fusee. Doe dat nu, vóór stap 8. Daarna zit de balk 0,5 mm voor de holte: de moer kan er dan niet meer in, maar ook niet meer uit vallen.

## 8. Fusee op de balk

1. Schuif de fusee met zijn twee lipjes om het uiteinde van de balk.
2. Steek de kingpin M4×30 van onderen door de lipjes en de balk. De kop zit onderaan, zodat het boutuiteinde niet naar de grond wijst.
3. Draai bovenaan een M4-moer op tot de speling weg is, een achtste toer terug, en zet er een tweede moer tegen vast. De fusee moet vrij draaien.

## 9. Voorwielen

Steek de M5×20 met een schijfje door het voorwiel in de moer van stap 7, met een druppel borgmiddel. Draai aan tot de speling weg is. Er is geen nylock: die zou bij het sturen tegen de balk lopen.

## 10. Servo

1. Zet de servo eerst in het midden: 1500 µs. `test_drive` doet dat bij het opstarten.
2. Steek eerst de servokabel van boven door de uitsparing, leid hem onder de vloer naar achter en weer omhoog door de sleuf achter de achterste toren. De kabel komt laag uit de servo, onder de vloer, dus hij kan nergens anders naar boven. Op de oude chassisprint zonder sleuf: boor daar zelf Ø4, midden, 1 tot 4 mm achter de toren (verder naar achter zit de eindwand van de accu) en haal de 3 pinnetjes uit de stekker om ze erdoor te steken (bruin = −).
3. Laat de servo van boven door de uitsparing in de vloer zakken, met de as naar boven en aan de voorkant. Zijn onderkant komt op 5 mm boven de grond. Plak de kabel plat tegen de onderkant van de vloer.
4. De lipjes rusten op de twee torens. De gaatjes in de lipjes zijn M2 en worden niet gebruikt: leg over elk lipje een geprinte servoklem (de uitsparing aan de kant van de ronde servotop) en zet die vast met 2× M3×10 in de inserts. Doe dat vóór de hoorn erop gaat.

## 11. Hoorn en stuurstangen

1. Druk de geprinte hoorn op de spline (Ø4,76), met de arm recht naar voren. Zit hij los, gebruik dan een druppel secondelijm. Er is geen schroefje: de stangen op de pen houden hem omlaag.
2. Leg de linker stang op de hoorn en op de bus van de linker fusee. De rechter stang komt erbovenop.
3. Bij de hoorn gaat een M4×20 van onderen door de hoorn en beide stangen; bij de armen een M4×25 (links) en M4×30 (rechts). Bovenaan telkens 2 M4-moeren tegen elkaar.
4. Draai de eerste moer aan tot de speling weg is, een achtste toer terug, en zet de tweede ertegen vast: de stangen moeten vrij draaien.

## 12. Accu

De ERYNK-accu (80 × 41 × 18,7 mm) ligt 3 mm verzonken in de vloer, tussen de stops. Span het elastiek over de 4 haakjes. Tussen de accu en de moeren onder de print blijft 2,5 mm voor het elastiek.

## 13. Buck converter (LM2596)

Zit op de print, zie [[PCB bestellen en solderen#3. Solderen: van laag naar hoog]]. **Trimpot eerst op 5,0 V.**

## 14. Print en ESP32

Leg de print op de 4 paaltjes en zet hem vast met 4× M3×6. Steek de ESP32 in de headers, met de USB-kant naar de opdruk "USB". Sluit dan aan: motordraden in M1 en M2, accu in J1, servo op J4 (bruin op −).

## 15. Eerste rit

Zet de auto op een blok zodat de wielen vrij draaien, en begin met een lage PWM.
- Draait een motor verkeerd om: wissel zijn twee draden, of zet `MOTOR_A_INVERT` / `MOTOR_B_INVERT` om in `test_drive`.
- Stuurt de auto de verkeerde kant op: zet `STEER_INVERT` om. De servo staat sinds v4 rechtop in plaats van ondersteboven, dus hij draait in de andere richting dan in het oude ontwerp.
