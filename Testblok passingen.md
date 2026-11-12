*Zie ook: [[DIY Auto]] · [[Passingen en toleranties]] · [[Threaded Inserts 3D Printing]]*

# Testblok passingen

Het testblok toont welke gatmaten passen bij jouw printer en filament. Print het opnieuw bij elk nieuw materiaal: nu in **PLA**, later in ASA. Bestand: `CAD/plates/p1s/plaat0_PLA_testblok.3mf` (P1S, 70 × 78 × 8 mm, plat op het bed, zonder support, ± 45 min). Gebruik dezelfde instellingen als voor de auto.

![[DIYAuto_testblok.png|520]]

Elk gat is een maat uit `Scripts/cad/params.py`. Waar de passing kritisch is, staat er een maat kleiner en een maat groter naast. Het getal onder elk gat is zijn diameter (bij de zeskant de sleutelwijdte).

| Rij | Gat | Wat erin | Goed als… | Maat in het model |
|---|---|---|---|---|
| **A M3 INSERT** | 4.0 · 4.2 · 4.4 | M3-insert, soldeerbout op ± 200 °C (PLA) | de insert rechtop op het gat blijft staan, recht inzakt en vlak eindigt zonder bult plastic erboven | `M3_INSERT`: chassis ↔ neus, print, buck |
| **A M3 VRIJ** | 3.5 | M3-bout | de bout er met de hand door schuift en weinig wiebelt | `M3_FREE`: kingpin, doorlopende M3-gaten |
| **B M2 INSERT** | 3.0 · 3.2 · 3.4 | M2-insert | zoals bij M3 | `M2_INSERT`: motorklemmen |
| **B M2 VRIJ** | 2.4 | M2-bout | de bout vrij draait en weinig wiebelt | stuurstangen, armbus, hoorn |
| **C LAGER** | 10.05 · 10.15 · 10.25 | MR105-lager, met de duim of in een bankschroef | het lager er met duwen in gaat en er niet vanzelf uitvalt | `SEAT_D`: lagerzittingen in de velgen |
| **C M5 PAS** | 5.1 | M5-bout | hij er met wat duwen door gaat en niet wiebelt | `AXLE_PRESS`: M5-as in toren en fusee |
| **C M5 VRIJ** | 5.4 | M5-bout | hij er vrij door gaat | `AXLE_FREE`: gat door de velg |
| **D M5 MOER** | 8.0 · 8.2 · 8.4 | M5-moer (DIN 934) | de moer er met de vinger in gaat en niet kan meedraaien | zeskant in de fusee |
| **D NYLOCK** | 8.2 × 5.4 | M5-nylock, plat | hij erin valt en niet kan draaien | gleuf in de toren |

**Terugmelden**, bv.: "M3 4.2 goed · lager 10.05 te krap, 10.15 perst goed · 5.1 wiebelt · moer 8.0 te krap, 8.2 goed". Dan pas ik `params.py` aan, en `export_sc.py --apply` maakt alle onderdelen opnieuw met die maten.
