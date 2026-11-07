*Zie ook: [[DIY Auto]] · [[DIY Auto Elektronica]] · [[Taken DIY-Auto]]*

# PCB bestellen en solderen

Print **rev 7** (2026-11-05): TB6612-module, LM2596 op de print, geen zekering. Achtergrond: [[DIY Auto Elektronica#Print rev 7 (2026-11-05)]].

## 1. Bestellen bij PCBWay

Upload `KiCad/DIY-Auto_rev8_gerbers_PCBWay.zip` op pcbway.com → *PCB Instant Quote* → *Quick-order PCB*. De maat (100 × 70 mm) en de lagen leest hij zelf uit het bestand.

| Instelling | Kies |
|---|---|
| Layers | 2 |
| Material / dikte | FR-4, 1,6 mm |
| Koper | 1 oz |
| Surface finish | HASL met lood (goedkoopst, soldeert het makkelijkst) |
| Aantal | 5 (de minimumprijs is voor 5) |
| Assembly | **nee**: de onderdelen soldeer je zelf |

## 2. Onderdelen

| # | Onderdeel | Op de print |
|---|---|---|
| 1 | ESP32 DevKit v1, 30 pins (rijen 25,4 mm) | J2, J3 (2× vrouwelijke header 1×15) |
| 1 | TB6612FNG-module (SparkFun-layout) | J8, J9 (2× vrouwelijke header 1×8) |
| 1 | LM2596-buckmodule (43 × 21 mm) | J6 (IN), J7 (OUT) + 2× M3×10, 2× M3-moer, 2 geprinte afstandsstukken |
| 3 | schroefklem 2-polig, raster 5,0 mm | J1 (accu), M1, M2 (motoren) |
| 1 | pinheader 1×3, 2,54 mm (mannelijk) | J4: servo |
| 1 | D1 1N5819 | 5 V → VIN |
| 4 | weerstanden | R6 1k, R7 20k, R41 20k, R42 5k1 |
| 5 | condensator 100 nF | C2, C6, C7, C150, C250 |
| 1 | elco 470 µF 16 V | C1 |

## 3. Solderen: van laag naar hoog

Soldeer eerst de lage onderdelen, zodat het bord plat op tafel blijft liggen terwijl je werkt.

1. **D1 en R6 eerst**: ze liggen onder de ESP32. Het **streepje** van D1 aan de kant van de **K** op de opdruk.
2. R7, R41, R42 (waarde staat op de opdruk; 5k1 = groen-bruin-zwart-bruin, 20k = rood-zwart-zwart-rood, 1k = bruin-zwart-zwart-bruin), dan de 100 nF-condensatoren (richting maakt niet uit).
3. Headers J2/J3 (ESP32) en J8/J9 (TB6612), pinheader J4. Tip: steek de module in de headers terwijl je ze soldeert, dan staan ze recht.
4. Schroefklemmen J1, M1, M2, met de openingen naar de rand.
5. C1 (470 µF): de **streep** op de behuizing weg van de **+** op de opdruk.
6. **LM2596 als laatste**, nadat de trimpot op 5,0 V staat (zie 4.). M3×10 van boven door het moduul, afstandsstuk, print, moer eronder. Dan 4 stukjes stijve draad (afgeknipte weerstandspootjes) door de pads van moduul en print en solderen. IN-kant boven J6, OUT-kant boven J7.

De GND-pinnen hebben thermische spaken, dus ze solderen even makkelijk als de andere pinnen.

## 4. Controle vóór de eerste keer aanzetten

- LM2596 los aan de accu: trimpot op **5,0 V** (af fabriek staat hij vaak op de ingangsspanning, dat zou de ESP32 en de servo opblazen).
- Voeding uit, multimeter in de piepstand: +BATT ↔ GND mag **niet** piepen (kort piepen terwijl C1 oplaadt mag).
- ESP32 en TB6612 nog niet erin, accu aan: J4 pin 2 ↔ pin 1 = 5,0 V.
- ESP32 erin met de **USB-kant naar de opdruk "USB"**, TB6612 met **VM tegenover PWMA** zoals de opdruk. Dan `test_tb6612`, zie [[DIY Auto Firmware]].
