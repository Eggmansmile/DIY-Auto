#electronics #project

*[[DIY Auto]] · [[DIY Auto Elektronica|Elektronica]] · [[DIY Auto Breadboard|Breadboard]] · [[DIY Auto Firmware|Firmware]] · [[DIY Auto Mechanisch|Mechanisch]] · [[DIY Auto BOM|BOM]] · [[Taken DIY-Auto|Taken]]*

## Schema

KiCad-project: [DIY-Auto.kicad_pro](KiCad/DIY-Auto.kicad_pro) · schema als PDF: `KiCad/DIY-Auto_schema.pdf`

![[DIY-Auto_kicad-schema.png]]

### H-brug (één per motor) [[H-Brug]]

![[DIY-Auto_hbrug.png]]

## Voeding

Accu: ERYNK 7,4 V 1500 mAh, 2S Li-ion (2× 18650). Rode JST BEC-stekker om te rijden, witte stekker om te laden.

- Eén bron: de accu. Rode stekker → J1 → +BATT (geen zekering sinds rev 5). +BATT voedt de motordriver (TB6612, VM) en de buckconverter.
- Geen schakelaar: de auto staat aan zodra de stekker erin zit. Uitzetten = stekker eruit.
- De buckconverter LM2596 (43 × 21 mm, D-SUN/HW-411-layout) maakt 5 V voor de servo (J4) en, via D1, voor VIN van de ESP32. Sinds rev 7 (2026-11-05) zit hij **op de print**, rechtsonder: 2× M3×10 door het moduul, een geprint afstandsstuk van 3 mm, de print, een M3-moer eronder. De 4 pads (IN+ IN− OUT+ OUT−) soldeer je met stukjes stijve draad aan J6 (IN) en J7 (OUT). **Zet de trimpot eerst op 5,0 V** (hij staat af fabriek vaak op de ingangsspanning), pas daarna op de print.
- USB mag tegelijk ingestoken zijn om te programmeren. D1 laat geen USB-stroom terug naar de buck.
- Laden: rode stekker los, de witte laadstekker aan de meegeleverde USB-kabel. De kabel stopt zelf bij 8,4 V. Nooit laden terwijl de auto aan de accu hangt.
- De motoren zijn 3–6 V-motoren. Bij 7,4 V begrenst de firmware de PWM (standaard 70 %), dan krijgen ze gemiddeld 5–6 V.
- Accumeting: $V_{ADC} = V_{accu} \cdot \frac{5{,}1}{25{,}1}$ (R41 20k, R42 5k1). In code: `analogReadMilliVolts(34) * 25.1 / 5.1`. Stop met rijden onder 6,4 V (3,2 V per cel), dat is 1,30 V op GPIO34. Of het pakket een eigen beveiliging heeft is niet zeker, dus deze stop moet in de code zitten.
- Accu-min en ESP32-GND zitten op dezelfde GND.

```
accu 2S ─ rode JST ─ J1 ─ +BATT ─┬─ TB6612 → motoren
   └─ witte stekker: laden met USB └─ LM2596 → 5 V → ESP32 (via D1) + servo
```

### Eerste keer aanzetten

1. LM2596 los aan de accu of labvoeding: trimpot draaien tot de uitgang **5,0 V** is (5,2 V mag, D1 kost ± 0,3 V voor de ESP32).
2. Moduul op de print, ESP32 en TB6612 nog niet in de headers. Accu aan: +BATT ↔ GND 6,0–8,4 V, J4 pin 2 ↔ pin 1: 5,0 V.
3. TB6612 en ESP32 erin, één motor aansluiten, lage PWM: `test_tb6612`, dan `test_drive`.
4. Na een minuut de TB6612 aanraken: warm mag, heet niet.

## Pinout ESP32

| GPIO | Net | Functie |
|---|---|---|
| 25 | A_HL | Motor A, hoge kant links (aan/uit) |
| 26 | A_HR | Motor A, hoge kant rechts (aan/uit) |
| 27 | A_LL | Motor A, lage kant links (PWM) |
| 13 | A_LR | Motor A, lage kant rechts (PWM) |
| 32 | B_HL | Motor B, hoge kant links (aan/uit) |
| 33 | B_HR | Motor B, hoge kant rechts (aan/uit) |
| 4 | B_LL | Motor B, lage kant links (PWM) |
| 18 | B_LR | Motor B, lage kant rechts (PWM) |
| 34 | VBAT_SENSE | Accuspanning (ADC, enkel ingang) |
| 19 | SERVO_PWM | Stuurservo, via R6 (1 kΩ) naar J4 |
| VIN | VIN | 5 V van de buck via D1 (1N5819) |
| GND | GND | Gedeelde massa |

Niet gebruiken: GPIO 0, 2, 12, 15 (strapping pins), 6–11 (flash), 14 (geeft PWM tijdens het opstarten).

### Stuurtabel (per motor)

| Beweging | HL | HR | LL | LR |
|---|---|---|---|---|
| Vooruit | 1 | 0 | 0 | PWM |
| Achteruit | 0 | 1 | PWM | 0 |
| Uitrollen | 0 | 0 | 0 | 0 |
| Remmen | 0 | 0 | 1 | 1 |
| **Kortsluiting — nooit** | 1 | – | 1 | – |

- HL en LL nooit samen hoog, HR en LR ook niet.
- Richting wisselen: alles op 0, 1 ms wachten, dan pas de andere kant aan.
- PWM 1–5 kHz. De motor zoemt, dat is normaal.

## MOSFET-keuze

Bij de IRLZ44N komt de gate maar op 3,3 V. Voor motoren tot ongeveer 2 A is dat genoeg. Wordt de MOSFET heet, vervang hem door een IRLB8721.

## KiCad

In deze map: `KiCad/` (schema, project, PDF) en `Scripts/` (generatoren). `uv` haalt de Python-library's zelf op, dus er staat geen venv in de vault.

Schema opnieuw genereren na een aanpassing in `Scripts/gen_schematic.py`:

```
cd ~/Personal-Projects/Second\ brain/Projects/DIY\ Auto\ Project
KICAD_SYMBOL_DIR=/usr/share/kicad/symbols ~/.local/bin/uv run -p 3.12 --with kicad-sch-api python Scripts/gen_schematic.py
kicad-cli sch erc KiCad/DIY-Auto.kicad_sch
```

Breadboardtekening en Fritzing-bestand opnieuw maken (controleert zichzelf tegen de KiCad-netlist):

```
kicad-cli sch export netlist -o KiCad/DIY-Auto.net KiCad/DIY-Auto.kicad_sch
python3 Scripts/gen_fritzing.py KiCad/DIY-Auto.net
```

Het script schrijft `Fritzing/DIY-Auto.fzz`, laat Fritzing (Flatpak `org.fritzing.Fritzing`) de SVG exporteren en maakt daaruit de twee PNG's in `Assets/`. Het faalt als een net afwijkt van KiCad, als een draad of pootje over een verkeerd gat loopt, of als een lijf een gebruikt gat bedekt.

`Scripts/gen_breadboard.py` en `KiCad/DIY-Auto.kicad_bbrd` horen bij de oude layout. Ze kloppen niet meer met de Fritzing-tekening.

Het script overschrijft `DIY-Auto.kicad_sch`. Wat je in KiCad zelf aanpast, gaat dan verloren.

Onderdelen op de print opnieuw plaatsen (systeem-Python, want die heeft `pcbnew`):

```
kicad-cli sch export netlist -o KiCad/DIY-Auto.net KiCad/DIY-Auto.kicad_sch
python3 Scripts/gen_pcb.py
```

`gen_pcb.py` overschrijft `DIY-Auto.kicad_pcb`, dus ook de sporen. Trek sporen pas als het schema vastligt.

## Print rev 7 (2026-11-05)

100 × 70 mm, 2 lagen, GND-vlak op beide lagen, gerouteerd met Freerouting. DRC: **0 fouten, 0 open verbindingen, klopt met het schema**; ERC 0. Motor- en accunetten 1,2 mm, 5 V en VIN 1,0 mm, signalen 0,3 mm.

- **TB6612-module** op J8/J9 (2× 1×8, rijen 15,24 mm uit elkaar, pinnamen op de opdruk).
- **LM2596 op de print** (J6 = IN-kant, J7 = OUT-kant + omtrek): maten uit de [Handsontec-datasheet](https://www.handsontec.com/dataspecs/LM2596S-DC-DC.pdf): pads 39,50 × 17,15 mm, M3-gaten 29,97 × 16,00 mm (diagonaal, naast IN+ en OUT−).
- **Soldeervriendelijk:** GND-pads met thermische spaken (behalve J3 pin 14, J8/J9 pin 8: daar sluiten sporen het koper in).
- **Opdruk:** "ANTENNE"/"USB" bij de ESP32 (180° gedraaid zet VIN op een GPIO), pinnamen bij de TB6612, +/− bij J1, J4, en IN+/IN−/OUT+/OUT− bij de LM2596.
- Geen zekering (F1 weg sinds rev 5).

**Bestellen:** `KiCad/DIY-Auto_rev8_gerbers_PCBWay.zip`, zie [[PCB bestellen en solderen]].

Opnieuw maken na een wijziging: `python3 Scripts/gen_pcb.py` (plaatsing), `python3 Scripts/route_pcb.py` (GND-vlakken + Freerouting), `python3 Scripts/silk_pcb.py` (opdruk), `kicad-cli pcb drc --schematic-parity`, en de Gerbers met `kicad-cli pcb export gerbers` + `export drill`.
