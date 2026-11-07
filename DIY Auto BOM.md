---
tags: [project, diy-auto, bom]
---
# DIY Auto — BOM (v4)

Hoort bij [[DIY Auto]]. Status: ✅ heb ik · 🛒 kopen · ⏳ later (vaste versie, niet nodig op het breadboard).

Concept v4 (2026-10-01): 2S Li-ion 7,4 V, geen schakelaar (de JST-stekker is de schakelaar), tandwielen m0,5 10:90 (9:1), servo SM-S2309S **rechtop**, **M5-bouten als assen**, PLA voor de prototypes (later ASA), banden in TPU 90A. Waarom: [[DIY Auto Mechanisch#Waarom deze onderdelen]].

## Aandrijving en sturing

| # | Onderdeel | Spec | Status | Referentie |
|---|---|---|---|---|
| 2 | DC-motor | behuizing 24 × 18,3 mm, as Ø2, 3–6 V | ✅ | M1 M2 |
| 2 | Rondsel | 10 tanden, m0,5, messing, Ø6,0 | ✅ | op de motor |
| 1 | Servo SpringRC SM-S2309S | 22,9 × 12,3 × 22,2 mm, 4,8–6 V, 1,1 kg·cm | ✅ | J4 |
| 10 | Kogellager MR105-2RS | 5 × 10 × 4 mm; 8 nodig | ✅ | 2 per wiel |
| 2 | Inbusbout M5×35 (DIN 912) | achteras | 🛒 | |
| 2 | Nylockmoer M5 (DIN 985) | achter, in de gleuf van de toren | 🛒 | |
| 2 | Inbusbout M5×20 (DIN 912) | vooras, met borgmiddel | 🛒 | |
| 2 | Moer M5 (DIN 934, 4 mm hoog) | voor, in de zeskant van de fusee | 🛒 | |
| 4 | Schijfje 5×7×0,5 inox | tussen boutkop en lager; raakt alleen de binnenring | 🛒 €8,64 (50 st.) | Amazon: B0CSGB2LF3 |
| – | Borgmiddel, middelsterk (blauw) | voorasbouten | 🛒 als je het niet hebt | |

De 4 stelringen Ø5 met M3-stelschroef van v3 zijn niet meer nodig.

## Voeding

| # | Onderdeel | Spec | Status | Link |
|---|---|---|---|---|
| 1 | Accupakket ERYNK 7,4 V 1500 mAh, 2S | gemeten 80 × 41 × 18,72 mm (2026-11-05); ligt 3 mm verzonken in de vloer; rode JST BEC (rood = +), laden met de eigen USB-kabel | ✅ | Amazon: B0DZXH8JNW |
| 1 | Buckconverter LM2596 (Hailege 5-pack) | 7,4 V → 5,0 V voor ESP32 en servo; trimpot op 5,0 V vóór hij op de print gaat; **op de print** (rev 7): 2× M3×10 + geprint afstandsstuk + M3-moer, pads gesoldeerd op J6/J7 | 🛒 (2026-11-02) | Amazon: Hailege 5 stuks 3 A DC-DC |
| – | Zekering | geschrapt (2026-11-02): geen F1 meer op de print, accu+ gaat rechtstreeks naar +BATT | – | – |

Het ERYNK-pakket heeft mogelijk geen beveiligingsprint: de firmware stopt onder 6,4 V (`USE_VBAT_CUTOFF`).

## Elektronica

| # | Onderdeel | Spec | Status | Referentie |
|---|---|---|---|---|
| 1 | ESP32 DevKit v1, 30 pins | Heemol, CH340 | ✅ | J2 J3 |
| 1 | TB6612FNG-motordrivermoduul (Hyuduo 2-pack) | J8, J9; silkscreen-volgorde + rij-afstand 15,24 mm nakijken | 🛒 (2026-11-02) | Amazon-winkelwagen |
| 4 | IRF9540N | P-MOSFET, TO-220 | ✅ | Q101 Q111 Q201 Q211 |
| 4 | IRLZ44N | N-MOSFET logic-level, TO-220 | ✅ | Q103 Q113 Q203 Q213 |
| 4 | 2N3904 | NPN, TO-92 | ✅ | Q102 Q112 Q202 Q212 |
| 1 | 1N5819 | Schottky, 5 V → VIN | ✅ | D1 |
| 8 (+1) | Weerstand 5,1 kΩ (5k1) | gate-pull-up P-FET, basisweerstand 2N3904 (+1 accumeting onder) | ✅ | R1x1, R1x2 (idem R2xx), R42 |
| 8 (+1) | Weerstand 20 kΩ | basis-pull-down, gate-pull-down N-FET (+1 accumeting boven) | ✅ | R1x3, R1x5 (idem R2xx), R41 |
| 5 (+1) | Weerstand 1 kΩ | gates, servosignaal (+1 testlast) | ✅ | R104 R114 R204 R214 R6 |
| 1 | Elco 470 µF / 16 V | buffer op +BATT | ✅ | C1 |
| 5 | Condensator 100 nF | ontkoppeling, over de motoren, op 5 V | ✅ | C2 C6 C7 C150 C250 |
| 2 | Led rood + groen | testlast | ✅ | – |

## Connectoren en bedrading

| # | Onderdeel | Spec | Status | Link |
|---|---|---|---|---|
| 1 set | JST BEC (RCY) 2-polig, man + vrouw, siliconendraad | 20 paar; past op de rode accustekker | ✅ | Amazon: YIXISI B082ZLXSWP |
| – | JST-XH-set | **niet meer nodig** sinds rev 7: de LM2596 zit op de print | – | – |
| 2 | Breadboard 830 gaten | bord 1 = voeding + brug A + servo, bord 2 = brug B | ✅ | – |
| 1 set | Dupontdraden, 240 st. (10 + 20 cm) | breadboardtests | 🛒 (2026-11-02) | Amazon-winkelwagen |
| 1 set | Vrouwelijke pinheaders 2,54 mm (VooGenzek 120 st.) | J2, J3 (1×15), J8, J9 (1×8); J4 (mannelijk 1×3) = reststuk van de TB6612-set | 🛒 (2026-11-02) | Amazon-winkelwagen |
| 3 | Schroefklem 2-polig, raster 5,0 mm (Lyeteung 100 st.) | J1 accu, M1, M2 motoren | 🛒 (2026-11-02) | Amazon-winkelwagen |
| 1 | Print | eigen PCB **rev 8** (PCBWay), `KiCad/DIY-Auto_rev8_gerbers_PCBWay.zip` | ⏳ | – |

## Mechanisch

Uit `CAD/BOM.md` (2026-11-05, v7).

| # | Onderdeel | Waar | Status |
|---|---|---|---|
| 16 | Heat-set insert M3×6 | 8 motorzadels, 4 servotorens, 4 printpaaltjes | ✅ |
| 14 | Inbusbout M3×10 | 8 motorklemmen, 4 servoklemmen, 2 LM2596 | ✅ |
| 4 | Inbusbout M3×6 | print op de paaltjes | ✅ |
| 2 | Moer M3 | onder de print, LM2596 | ✅ |
| 2 + 2 | Inbusbout M5×40 + moer M5 | achteras, moer in de gleuf van de toren | |
| 2 + 2 | Inbusbout M5×20 + moer M5 | vooras, moer in de fusee, borgmiddel | |
| 4 | Schijfje 5×7×0,5 inox | tegen de binnenring van het lager | |
| 2 + 4 | Inbusbout M4×30 + moer M4 | kingpins, kop onder, 2 moeren tegen elkaar | |
| 3 + 6 | Inbusbout M4×20 / ×25 / ×30 + moer M4 | hoornpen, armen; 2 moeren tegen elkaar | |
| 1–2 | Elastiek | accu, over de 4 haakjes | 🛒 |

## Geprinte onderdelen

STL's per assembly in `CAD/parts/<assembly>/print/`. Herdruk v7 (2026-11-05) op de H2D: `CAD/plates/h2d-v7/` (chassis, servoklem, servohoorn, afstandsstukken; ± 6 u, 109 g).

| # | Onderdeel | Materiaal | Opmerking |
|---|---|---|---|
| 1 | chassis (één stuk met de neus) | ASA zwart | vloer 8 mm (neus 3 mm), vloer naar beneden; v7 |
| 2 | motorklem L/R | ASA zwart | deelvlak naar beneden |
| 2 | velg achter L/R met tandwiel 90T m0,5 | PLA | **0,2 mm-nozzle**, buitenkant op het bed |
| 2 | velg voor L/R | PLA | |
| 2 | fusee (knuckle) L/R | ASA zwart | op de platte voetjes |
| 2 | stuurstang L/R | ASA zwart | plat; M4 draait er vrij in |
| 1 | servohoorn | ASA zwart | drukpassing op de spline Ø4,76 (gat 4,78); v7 |
| 2 | servoklem (1 STL) | ASA zwart | plat; drukt de lipjes op de torens; uitsparing voor de ronde servotop; v7 |
| 2 | afstandsstuk LM2596 (1 STL) | ASA zwart | Ø6 × 3, M3-gat; kunststof, want een metalen moer raakt IN+; v7 |
| 4 | band voor + achter | TPU 90A | A1 mini, externe spoel, profiel `TPU 90A @BBL A1M (DIY-Auto).json` |

Printprofiel H2D: "DIY-Auto ASA strong @BBL H2D" (5 wanden, 5 boven/onder, 40 % gyroid, brim buitenkant, support alleen vanaf het bed).

## Nog te kopen, samengevat

- [x] Accu ERYNK 7,4 V 1500 mAh
- [ ] Buckconverter LM2596: trimpot op 5,0 V, meten en vastlakken vóór de ESP32 erin gaat
- [ ] M4-bouten (M4×20, M4×25, 3× M4×30) + 10 M4-moeren, als je die nog niet hebt
- [ ] Vrouwelijke pinheaders, schroefklemmen, TB6612, dupontdraden
- [ ] Schijfjes 5×7×0,5 (€8,64)
- [ ] M5: 2× M5×35, 2× M5×20, 2× M5-nylock, 2× M5-moer, borgmiddel
- [x] M3-bouten, nylocks, inserts
- [x] M3-bouten, nylocks, inserts
- [ ] Elastiek
- [ ] Zekeringhouder mini-blade + 5 A (zie Voeding)
