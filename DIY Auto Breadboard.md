#electronics #project

*[[DIY Auto]] · [[DIY Auto Elektronica|Elektronica]] · [[DIY Auto Breadboard|Breadboard]] · [[DIY Auto Firmware|Firmware]] · [[DIY Auto Mechanisch|Mechanisch]] · [[DIY Auto BOM|BOM]] · [[Taken DIY-Auto|Taken]]*

## Breadboard: voeding + TB6612-module + servo

Getekend in Fritzing. Het bestand `Fritzing/DIY-Auto.fzz` opent in Fritzing (Flatpak). Eén breadboard: voeding, TB6612-module over de gleuf, ESP32, servo en twee motoren, in zeven bouwstappen. Wat in een vorige stap al op het bord zat, is grijs weggevaagd. De oude tekening met de eigen H-bruggen staat in `Fritzing/DIY-Auto_hbrug.fzz` (beelden `DIY-Auto_breadboard_v3g.png`).

![[DIY-Auto_breadboard_v4.png]]

Alles in één beeld: ![[DIY-Auto_breadboard-overzicht_v4.png]]

Bouwvolgorde, telkens eerst testen voor je verder gaat:

1. Accu met de rode JST-stekker op de bovenste rails: + in Y3, − in Z3 (Y = +7,4 V, Z = GND). Test je eerst zonder accu, zet dan de labvoeding op 7,4 V met een stroombegrenzing van 0,5 A. C1 en C2 over die rails. GND-rails rechts verbinden. Spanning meten tussen +7,4 V en GND: 6,0–8,4 V. Op het breadboard zit geen zekering; op de print komt F1 (5 A) ertussen.
2. LM2596: IN+ in Y4, IN− in X4. OUT nog los laten en met de trimmer op 5,0 V zetten. Dan OUT+ in W3 (onderste rode rail = +5 V) en OUT− in X3. C7 over W52 en X52. Meten tussen W en X: 5,0 V.
3. Hoge kant: IRF9540N met alle drie de pootjes recht in J13–J15 en J37–J39 (tekst naar jou). Rood draadje van I15 naar Y16 en van I39 naar Y40: dat brengt S naar +7,4 V. 2N3904 in A13–A14 en A37–A38 (platte kant van je weg), de E-poot buig je schuin naar de GND-rail (X17 en X41). Pull-ups en basisweerstanden.
4. Lage kant: IRLZ44N met alle drie de pootjes recht in A21–A23 en A45–A47 (metalen tab naar jou). Zwart draadje van B21 naar X19 en van B45 naar X43: dat brengt S naar GND. Gateweerstanden. Drains naar M+ (kolom 22) en M− (kolom 46).
5. D1 in C4 (kathode, streepje) en C8 (anode). Draad A8 → W9 (+5 V), draad A4 → VIN van de ESP32. Dan de vijf dupontdraden (GPIO25, 27, 26, 13 en GND). USB mag erbij om te programmeren. Testlast: 1 kΩ met een rode en een groene led. Vooruit: rode led brandt. Achteruit: groene led brandt. PWM lager: de led dimt.
   Testlast gat per gat: grijs draadje I22 → I26, 1 kΩ H26 → H30, **rode led** lange poot J30 / korte poot J29, **groene led** andersom: lange poot F29 / korte poot F30, grijs draadje I29 → I46.

   ![[DIY-Auto_testlast_detail_v1.png]]
   **Eerst de massa (2026-09-30):** GND van de ESP32 ↔ GND van het bord mat −0,5 V, dus ze waren niet verbonden.

   ![[DIY-Auto_fixes_massa_v1.png]]

   **Meten als de leds niet branden:** laat `test_hbridge.ino` draaien, zwarte probe op GND, en meet de punten 1–12 in volgorde. Waar de waarde niet klopt, zit de fout tussen dat punt en het vorige. Bouwde je met andere gatnummers, meet dan op hetzelfde **pootje** (bv. "gate van de linker IRF9540N").

   ![[DIY-Auto_meetpunten_v1.png]]

   Brandt de rode led niet terwijl M+ wel 7 V geeft: volg het pad M+ → testlast → M−.

   ![[DIY-Auto_meetpunten_pad_v1.png]]
   **Wat er misliep bij brug A (2026-09-30), om te checken bij brug B:**
   - ESP32 zat niet diep genoeg in het breadboard: pinnen gaven niets door. Doorgangstest pin ↔ gat, of dupontdraden rechtstreeks op de pinnen.
   - GPIO-draden op verwisselde pinnen (D25/D26): de verkeerde kant schakelde.
   - Transistors verkeerd om: IRF9540N tekst naar jou = G D S, IRLZ44N tab naar jou = S D G, 2N3904 plat van je weg = C B E.
   - Rood source-draadje een kolom naast de source: hoge kant ging nooit aan.
   - Drain-draadje van de rechter IRF9540N in de source-kolom van de IRLZ44N (= GND): kortsluiting (CC) zodra HR aanging.
   - Debug-sketch `Firmware/debug_hold/`: start UIT, zet één transistor tegelijk aan ('1'–'4') of een richting ('v', 'a'), zo vind je welke kant kortsluit.

6. Testlast weg, motordraden in J22 (M+) en J46 (M−).
7. Servo: R6 (1 kΩ) van C58 naar C62. GPIO19 → A58, servosignaal → A62, servo + → W61, servo − → X60.
8. H-brug B op bord 2: exact dezelfde onderdelen en gaten als stap 3 en 4. Rails van bord 2 voeden vanaf bord 1: Y61 → Y61 (+7,4 V) en X59 → X61 (GND). De onderste rode rail van bord 2 blijft leeg.
9. GPIO32 → E18, GPIO4 → E27, GPIO33 → E42, GPIO18 → E51 op bord 2. Eerst de testlast van stap 5 tussen D22 en D46 van bord 2, dan motor B in J22 (M+) en J46 (M−).

In de tekening ligt het lijf van elke transistor over de rails. Echt staat hij rechtop in rij J of A. Onderaan: de IRLZ44N met de **metalen tab naar jou** (van links naar rechts S D G), de 2N3904 met de **platte kant van je weg** (C B E). De S- en E-poot gaan schuin naar de GND-rail.

Een breadboardcontact verdraagt ongeveer 1 A. Laat de motor op het breadboard enkel kort en met lage PWM draaien. Voor de wagen zelf ga je naar een [[Perf boards|perfboard]] of je eigen PCB.

Testen na stap 5: sketch `Firmware/test_hbridge/test_hbridge.ino`, zie [[DIY Auto Firmware]].
