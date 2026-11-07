---

kanban-plugin: board

---

## To-Do

- [ ] Print v7 starten op de H2D (Bestanden → `DIYAuto_v7_ASA_H2D.gcode.3mf`, ASA zwart, ± 6 u)
- [ ] Print rev 8 bestellen: `KiCad/DIY-Auto_rev8_gerbers_PCBWay.zip` → [[PCB bestellen en solderen#1. Bestellen bij PCBWay]]
- [ ] LM2596: trimpot op 5,0 V vóór hij op de print gaat → [[PCB bestellen en solderen#4. Controle vóór de eerste keer aanzetten]]
- [ ] TB6612FNG-motordrivermodule kopen (breakout met 2× 8 pinnen, VM tot 13,5 V) + 2× vrouwelijke header 1×8 → [[DIY Auto Elektronica]]
- [ ] Meten TB6612-module: afstand tussen de twee pinrijen (nu 15,24 mm) en pinvolgorde (nu SparkFun: VM VCC GND AO1 AO2 BO2 BO1 GND / PWMA AIN2 AIN1 STBY BIN1 BIN2 PWMB GND) → `MOD_ROW` in `Scripts/gen_pcb.py`
- [ ] Optioneel: blokkeerstroom van één motor bij 6 V op de labvoeding (TB6612 max 3,2 A piek)
- [ ] TB6612 op het breadboard testen met `test_tb6612`: beide richtingen, remmen, labvoeding mag niet in CC → [[DIY Auto Firmware]]
- [ ] Onderdelen v4 kopen: M5-bouten en -moeren, schijfjes 5×7×0,5, M3×25, M2×12/×18 + M2-nylocks, AOLIKES-pakket → [[DIY Auto BOM#Nog te kopen, samengevat]]
- [ ] Print solderen → [[PCB bestellen en solderen#4. Solderen: van laag naar hoog]]
- [ ] Print testen vóór de ESP32 erin gaat → [[PCB bestellen en solderen#5. Controle vóór de eerste keer aanzetten]]
- [ ] Breadboard: CC bij rood met PWM oplossen: `debug_hold` stand `p` opnieuw testen → [[DIY Auto Breadboard]]
- [ ] Breadboard stap 6: motor A op M+ en M− → [[DIY Auto Breadboard]]
- [ ] Breadboard stap 7: servo op GPIO19 → [[DIY Auto Breadboard]]
- [ ] Breadboard stap 8–9: H-brug B op bord 2 (checklist van brug A gebruiken) → [[DIY Auto Breadboard]]
- [ ] Xbox-controller koppelen met `test_drive` (Bluepad32) → [[DIY Auto Firmware]]
- [ ] Testblok v4 printen in **PLA** vóór de echte delen (`CAD/plates/p1s/plaat0_PLA_testblok.3mf`) en de passingen terugmelden → [[Testblok passingen]]
- [ ] Printen v4: PLA-platen op de P1S (`CAD/plates/p1s/`), banden op de A1 mini (`CAD/plates/a1mini/`, eerst het TPU 90A-profiel importeren) → [[DIY Auto Mechanisch#Printen]]
- [ ] Auto monteren → [[DIY Auto Assemblage]]
- [ ] Eerste rit: wielen van de grond, lage PWM; stuurrichting controleren (`STEER_INVERT`, de servo staat nu rechtop) → [[DIY Auto Assemblage#15. Eerste rit]]
- [ ] Servo-saver tussen hoorn en stangen: beslissen na de eerste ritten (SM-S2309S heeft plastic tandwielen)
- [ ] TPU-banden testen op grip
- [ ] Opschrijven wat misgaat bij het rijden → input voor v5


## In Progress



## Done

- [x] 2026-11-05: chassis v7 (vloer 8 mm, accuvak 80 × 41, servo uit het GitHub-model, LM2596 van het chassis naar de print), print rev 7 (LM2596 op de print volgens Handsontec, thermische spaken, USB/ANTENNE-opdruk); v7 staat op de H2D; FreeCAD-assembly opnieuw gebouwd
- [x] Ontwerp v4 (2026-10-01): servo rechtop (v3b was niet te monteren), M5-bouten als assen, M2-nylocks op de stuurstangen, kingpin M3×25 kop onder, nokken velg ↔ band, AOLIKES-bak; `check_all.py` 0 botsingen → [[DIY Auto Mechanisch#Waarom deze onderdelen]]
- [x] Vergeleken met 4 andere geprinte RC-auto's → [[DIY Auto Mechanisch#Vergelijking met andere geprinte RC-auto's (2026-10-01)]]
- [x] Montagenote met beelden per stap en een overzicht → [[DIY Auto Assemblage]]
- [x] FreeCAD-assembly v4 opnieuw gemaakt (FreeCAD 1.1.4 op de desktop): lost op, Sim_rijden en Sim_sturen erin
- [x] Tekening v4 uit het CAD-model (`Drawings/DIY-Auto_v4.pdf`) → [[DIY Auto Mechanisch]]
- [x] Testblok v4: M5-pas en -vrij, M5-moerzeskant, nylock-gleuf, maten rond `params.py` → [[Testblok passingen]]
- [x] TPU 90A-profiel voor de A1 mini; platen: P1S = PLA, A1 mini = TPU
- [x] Print rev 3: waarden in de weerstanden, +/− bij J1, J4, J6, J7; nieuwe Gerbers (koper identiek) → [[PCB bestellen en solderen]]
- [x] ESP32 gemeten: 25,6 mm tussen de pinrijen → 25,4 mm, de print klopt (2026-09-30)
- [x] Print rev 4 (2026-10-02): eigen H-bruggen vervangen door een TB6612FNG-module (H-brug blijft op het breadboard als leerproject); DRC 0 fouten, Gerbers klaar; `test_drive` omgezet, oude versie = `test_drive_hbrug` → [[DIY Auto Elektronica]]
- [x] **Bestellen fase 0**: componentenkit, IRLZ44N + IRF9540N, 2× ESP32 USB-C CH340 (Heemol, 30 pins)
- [x] Motor bepaald: TT-motor 3–6 V, rondsel 10 tanden Ø5,88 → module 0,5 (2026-09-28)
- [x] Concept v3 gekozen: 2S-pakket 7,4 V (ERYNK), geen schakelaar, 9:1 met m0,5, servo SM-S2309S, geprinte assen
- [x] BOM-note gemaakt → [[DIY Auto BOM]]
- [x] KiCad-schema rev 3 (2S, zonder SW1), ERC en netlistcontrole OK
- [x] Fritzing-breadboard met beide H-bruggen in 9 stappen, plus meetpunten en testlast-figuren
- [x] CAD v3: frame, achteraandrijving, voorwielen, sturing, elektronica (build123d)
- [x] Sturing v3b: hoorn naar voren, geen dode punt meer (gevonden met de FreeCAD-simulatie)
- [x] FreeCAD-assembly met joints + simulaties en GIFs
- [x] Testblok geprint; lagerzitting 10,0 → 10,15, gaten volgens bronnen aangepast → [[Passingen en toleranties]]
- [x] Breadboard brug A gebouwd en doorgemeten: vooruit en achteruit werken (statisch) (2026-09-30)
- [x] Firmware geflasht: `test_hbridge`, `debug_hold`, `pintest`
- [x] Print rev 3 gerouteerd: DRC 0 fouten, Gerbers klaar → [[DIY Auto Elektronica]]
- [x] Printplaten gemaakt voor P1S en A1 mini (`Scripts/cad/plates.py`)
- [x] Kennisnotes: inserts, vrijheidsgraden, tandwielen, motoren/servo's, lagers, passingen, printrichting, H-brug, DC-motor




%% kanban:settings
```
{"kanban-plugin":"board","list-collapse":[false,false,false]}
```
%%