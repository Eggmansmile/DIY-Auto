#3d-printen #cad #project

*[[DIY Auto]] · [[DIY Auto Elektronica|Elektronica]] · [[DIY Auto Breadboard|Breadboard]] · [[DIY Auto Firmware|Firmware]] · [[DIY Auto Mechanisch|Mechanisch]] · [[DIY Auto BOM|BOM]] · [[Taken DIY-Auto|Taken]]*

## 3D-model

![[DIYAuto_tekening_v4.png]]
*Tekening v4 (A3, 1:1): projectie van het CAD-model. PDF: `Drawings/DIY-Auto_v4.pdf`.*

Het 3D-model is een SolidCraft-assembly: `CAD/DIY-Auto.sc` (master, vijf mappen: banden, body, PCB, motor en aandrijving, voorkant en sturing) met de printdelen als gelinkte designs in `CAD/solidcraft/`. Alle maten staan in `Scripts/cad/params.py`. Pas een maat aan, bouw de designs opnieuw en exporteer:

```
cd Scripts/cad
python3 sc_build.py <deel>                # één deel bouwen en vergelijken met de STEP
~/.local/bin/uv run -p 3.12 --with build123d --with trimesh --with networkx python export_sc.py --apply              # STEP + STL per deel, manifest.json, BOM.md
~/.local/bin/uv run -p 3.12 --with build123d --with trimesh --with networkx --with bd_warehouse --with rectpack --with lxml python check_all.py   # botsingen, sturen, montagepad servo
for p in p1s p1s-alles a1mini; do ~/.local/bin/uv run -p 3.12 --with trimesh --with rectpack --with networkx --with lxml python plates.py $p; done
~/.local/bin/uv run -p 3.12 --with build123d --with bd_warehouse --with matplotlib python gen_drawing.py   # tekening A3
~/.local/bin/uv run -p 3.12 --with build123d --with bd_warehouse python test_fit.py      # testblok
```

Uitvoer: `CAD/parts/<assembly>/` (STEP + STL per deel, één map per assembly), `CAD/parts/<assembly>/print/` (de printdelen al gedraaid voor het printbed), `CAD/plates/`. `check_all.py` moet overal 0,000 mm³ geven. De oude build123d-generators staan in `Scripts/cad/archive_build123d/`.

De body bestaat uit twee printdelen: het chassis (153 × 94 mm) en de neus (77 × 72 mm). Beide passen op de A1 mini. Ze zitten vast met 2× M3×10 in liggende inserts in de flens van het chassis. De neus draagt de sturing, zodat je bij een nieuwe sturing enkel de neus opnieuw print. Geen enkel deel heeft support nodig. De klem heeft bovenaan een brug van 16,6 mm; die lukt op de Bambu-printers. Het accupakket ligt tussen stops van 8 mm en zit vast met een elastiek over 4 haakjes. In de eindwanden zit een uitsparing voor de draden.

| Onderdeel | Print? | Specificatie |
|---|---|---|
| Chassis, neus, klemmen, fusees, stangen, hoorn, servoklemmen, velgen | Ja (H2D) | PLA voor de prototypes, later ASA; 4 wandlijnen, 30% gyroid |
| Banden | Ja (A1 mini) | TPU 90A, 3 wandlijnen, 15% infill, profiel `CAD/plates/a1mini/TPU 90A @BBL A1M (DIY-Auto).json` |
| Assen | Nee | Bouten: achter M5×35 + M5-nylock, voor M5×20 + M5-moer; schijfje 5×7×0,5 op de binnenring |
| Lagers | Nee | MR105-2RS (5×10×4), 8 stuks (ANGEEK, 10 stuks) |
| Rondsel motoras | Nee | Zit al op de motor: 10 tanden, m0,5 (Ø6,0), geperst. Groot tandwiel 90T m0,5 → 9:1 |
| Bevestiging | Nee | alleen M3 (sinds 2026-10-24) in threaded inserts; draaipunten op een bout met een nylock |

Wiel aan **twee** kanten lageren, niet aan één plaatje.

### Sturing (v4)

De servo staat rechtop op 2 paaltjes, met de as naar boven. Zijn lijf zakt door een uitsparing in de vloer van de neus, tot 5,0 mm boven de grond; de hoorn ligt op z = 32–36. Servomaten (2026-11-05) uit het model [servo-s2309s.scad](https://github.com/GlenSearle/SpaceBaseStationForAndroid/blob/master/Printables/servo-s2309s.scad): lijf 23 × 12,3 × 22, lipjes 31,8 × 2,3 op 15,5, ronde top Ø12,3 tot 25,5, spline-top 29,5, as 5,0 van het lijfeinde; spline Ø4,76 gemeten. Er bestaat geen officiële maattekening. De stuurarmen zitten op het bovenste lipje van de fusee, met een bus tot op dezelfde hoogte als de hoorn. Eén hoornarm wijst naar voren (gat op r = 15,2 mm, ontwerpmaat van de geprinte hoorn), en beide stuurstangen zitten op dezelfde M3-pen: de rechter ligt op de linker. De stangen lopen bijna evenwijdig aan de as, dus loodrecht op de stuurarmen. Waarom deze vorm: zie [[Motoren en servo's koppelen]]. De eerste versie liep na 8° vast; de simulatie toonde dat.

In v3b hing de servo ondersteboven, met de hoorn tussen de vloer en een brug. Dat ontwerp was niet te monteren: de hoorn kon er niet meer op als de servo vastzat, en een servo mét hoorn botste tegen de brug (`mount_check()` in `check_all.py` controleert dit nu). De geometrie in het bovenaanzicht bleef gelijk, dus de stuurhoeken ook.

![[DIYAuto_sturing_iso.gif|420]] ![[DIYAuto_sturing_onder.gif|360]]
*Sturing (v3b, ondersteboven; de hoeken gelden ook voor v4): hoorn ±17,5° → binnenwiel 30°, buitenwiel 26° (rechts: onderaanzicht, links en rechts gespiegeld).*

![[DIYAuto_aandrijving_9to1.gif|380]]
*Aandrijving: rondsel 10T op de motor, tandwiel 90T in de velg. Eén toer van het rondsel is 40° van het wiel.*

### Beweging in SolidCraft

`CAD/DIY-Auto.sc` heeft revolute joints op de wielen en de fusees. De kingpin-joints lopen van −30° tot +30° (`LOCK`). Sleep een joint in SolidCraft om te sturen; de banden en velgen draaien mee.

### Maten in dit model

Alle maten staan in `Scripts/cad/params.py`. De maten komen uit de bronnen in [[Passingen en toleranties]] (2026-09-30); het lager is bijgesteld na het [[Testblok passingen]]. Waarom deze getallen: [[Passingen en toleranties]], [[Threaded Inserts 3D Printing]], [[Lagers]].

| Wat | In `params.py` | Nu |
|---|---|---|
| Gat M3-insert (Hilitchi, OD 5,0) | `M3_INSERT` | Ø4,2 |
| Doorlopend gat M3 | `M3_FREE` | Ø3,5 |
| Lagerzitting MR105 | `SEAT_D` | Ø10,15 (perspassing; 10,0 was te krap) |
| M5-asbout in toren en fusee / vrij in de velg | `AXLE_PRESS` / `AXLE_FREE` | Ø5,1 / Ø5,4 |
| Gleuf M5-nylock (toren), zeskant M5-moer (fusee) | `NUT_M5`, `REAR_NUT_Y0`, `FRONT_NUT_Y1` | sleutelwijdte 8,0 + 0,2 |
| M3 vrij (stangen, armbus, hoorn) | `ROD` in `steering.py` | Ø3,5, nylock eronder |

De passingen zijn gemeten met een testblok in PETG. Voor PLA en later ASA print je het [[Testblok passingen]] opnieuw.

### Waarom deze onderdelen

| Onderdeel | Wat het doet | Zonder |
|---|---|---|
| Schijfje 5×7×0,5 en kraag Ø6,5 op toren en fusee | duwt alleen op de binnenring van het lager, die met de as stilstaat | een grotere ring wrijft tegen de draaiende buitenring en remt het wiel |
| M5-bout als as | stijve stalen as, geklemd in toren of fusee | een geprinte as plooit; dan verschuift de tandwielgrijping (m0,5) |
| Nylock in een gleuf (achter), moer in een zeskant (voor) | de moer kan niet meedraaien; met de nylock stel je de speling in | de bout draait los door de trillingen |
| Lagers aan beide kanten van de velg | het wiel kan niet kantelen | het wiel slingert en de tanden lopen uit elkaar |
| Tandwielplaat tussen motorzadel en toren | houdt de hartafstand van 25 mm vast | de motor kan wegkantelen van het tandwiel |
| Klem 0,2 mm lager dan de motor | drukt de motor vast in zijn zadel | de motor trilt los |
| Nokken op de velg | de TPU-band kan niet rond de velg slippen | de band slipt bij optrekken |
| Kingpin met de kop onder, nylock boven | de fusee draait op een stalen pen; het boutuiteinde wijst omhoog | met de kop boven hing het boutuiteinde 3,4 mm boven de grond |
| Servo rechtop, hoorn bovenop | hoorn en schroeven bereik je van boven | ondersteboven was het niet te monteren |
| M3-bout + nylock op de draaipunten | de stang draait op staal, niet op plastic draad | een bout die zijn eigen draad tapt in PLA slijt en komt los |
| Servoklem over de lipjes, M3 in inserts | de servo heeft alleen M2-gaatjes en er zijn geen M2-bouten | M3 door het lipje opboren laat te weinig plastic over |
| Geprinte hoorn, drukpassing Ø4,7 op de spline Ø4,68 | er was geen hoorn bij de servo | — |

### Vergelijking met andere geprinte RC-auto's (2026-10-01)

| Project | Wat ze doen | Wat wij overnamen |
|---|---|---|
| [TommyB, 3D Printed RC car](https://www.printables.com/model/415497-3d-printed-rc-car) (ESP32, Ackermann) | stalen assen 3 mm met stelringen; servo rechtop op het dek, hoorn bovenop; M3-nylocks met ringen op alle draaipunten | servo rechtop, nylocks op de draaipunten |
| [Prism08, RC Car V2](https://www.printables.com/model/281110-rc-car-v2-almost-fully-printed) | in V1 hing de servo ondersteboven, in V2 niet meer; "the screw itself is the axle"; een geprint deel van Ø4,8 brak tot hij het Ø6,8 maakte | bout als as, geen dunne geprinte assen |
| [Logan57, 3D Printed RC Car](https://www.instructables.com/3D-Printed-RC-Car/) | servo met hoorn eerst op een eigen beugel; voorwiel op een M3×30-bout met ring en nylock; stuurstangen op M3, niet vastgedraaid | wiel op een bout + nylock |
| [Prusa: tips voor geprinte RC-auto's](https://blog.prusa3d.com/cool-tips-and-tricks-for-3d-printed-rc-cars_68368/) | tandwielen best in nylon of PC; PLA gaat voor trage auto's; PETG slijt als tandwiel | PLA voor de prototypes; een beter tandwiel komt later |

Nog niet overgenomen: een servo-saver tussen hoorn en stangen. De SM-S2309S heeft plastic tandwielen, en een klap op een voorwiel gaat nu recht naar de servo. Na de eerste ritten beslissen.

### Printen

- **H2D v8 (2026-11-07), ASA zwart:** `CAD/plates/h2d-v8/DIYAuto_v8_ASA_H2D_project.3mf` (chassis met vloer én neus 8 mm, servoklem, servohoorn, afstandsstukken LM2596), profiel "DIY-Auto ASA strong" (5 wanden, 40 % gyroid). Vervangt v7: die had een neus van 3 mm. De STL van de body heeft 12 open randen bij de insertgaten; Bambu Studio herstelt dat bij het importeren.
- **H2D (2026-10-24):** `CAD/plates/h2d/plaat1_PLA_0.4.3mf` (alle PLA behalve de achtervelgen), `plaat2_PLA_0.2-nozzle.3mf` (achtervelgen, 0,2 mm nozzle), `plaat3_TPU.3mf` (banden, externe spoel). Rond de insertgaten minstens 3 wanden.
- **P1S, PLA:** `CAD/plates/p1s/plaat1_PLA_0.4.3mf` (0,4 mm nozzle) en `plaat2_PLA_0.2-nozzle.3mf` (achtervelgen, m0,5-tanden). Of alles op `CAD/plates/p1s-alles/` met de 0,2 mm nozzle.
- **A1 mini, TPU 90A:** `CAD/plates/a1mini/plaat3_TPU.3mf`, van de externe spoel. Importeer eerst het profiel in Bambu Studio: *File → Import → Import Configs…* → `TPU 90A @BBL A1M (DIY-Auto).json`. Het erft van *Generic TPU @BBL A1M* en verandert alleen: max. volumetrische snelheid 1,8 mm³/s (90A knikt in de extruder bij meer), nozzle 225 °C, retractie 0,2 mm aan 20 mm/s, geen wipe of z-hop, bed 35 °C.
- TPU trekt vocht aan: droog de spoel 6–8 u op 50–55 °C. De spoel moet vrij kunnen draaien; elke weerstand in de toevoer laat zachte TPU knikken.

### Tandwielen

Rondsel 10T en tandwiel 90T, module 0,5 (`MOD`, `Z_PIN`, `Z_GEAR`): overbrenging 9:1, hartafstand 0,5 · (10 + 90) / 2 = 25 mm (`X_MOT = −25`). Speling: de tand is 0,30 mm dunner op de steekcirkel (`BACKLASH`), wat ± 0,13 mm tussen de flanken geeft. Printen met een 0,2 mm nozzle, plat op het bed. Theorie: [[Tandwielen ontwerpen]].
