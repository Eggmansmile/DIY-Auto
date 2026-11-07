# DIY-Auto — KiCad

Schema van de RC-auto: accu, ESP32 DevKit-headers en twee H-bruggen met losse MOSFETs.
Volledige uitleg staat in de note `../DIY Auto.md`.

## Breadboard openen (dit vergeet je telkens)

Het breadboard zit **niet** in de projectlijst van KiCad, want die toont `.kicad_bbrd` niet.

1. `DIY-Auto.kicad_pro` openen → **PCB Editor**.
2. Breadboard-icoon in de rechtse werkbalk.
3. In **dat venster** (onderdelenlade links, "Binding posts" rechts): **File → Load session… (Ctrl+L)**.
4. `DIY-Auto.kicad_bbrd` kiezen → **Validate**.

Controle: de statusbalk zegt `Session loaded from …`. Staat er `Loaded 40 component(s) from DIY-Auto.net`, dan heb je de netlist geladen in plaats van de sessie, en blijft het bord leeg.

Let op: het File-menu van de projectmanager heeft geen *Load session*. Dat menu-item bestaat alleen in het breadboard-venster.

## Legenda van de breadboardtekening

Twee beelden in `../../../Assets/`:

- `DIY-Auto_breadboard.png` — vier bouwstappen onder elkaar. Elke stap toont enkel wat er bijkomt; het vorige werk staat grijs weggevaagd.
- `DIY-Auto_breadboard-overzicht.png` — alles in één beeld.

Alles staat op ware grootte: 1 gat = 2,54 mm.

Bouwvolgorde: 1) voedingsrails en condensatoren, 2) hoge kant, 3) lage kant en motorgaten, 4) draden naar de ESP32 en de testlast. De accu sluit je als laatste aan.

### Draden

| Kleur | Betekenis |
|---|---|
| Rood | +11,1 V van de accu |
| Zwart | GND, de min van de accu |
| Blauw | signaal van de ESP32 naar een gate of basis |
| Grijs | verbinding tussen twee gaten op het bord |

### Onderdelen

| Vorm | Wat | Maat |
|---|---|---|
| Beige blokje | weerstand | 6,3 × 2,5 mm |
| Oranje schijfje | keramische condensator 100 nF | 5 mm |
| Blauwe cilinder met witte streep | elco 470 µF, streep = min | 10 mm |
| Grijs blok met lichte strip boven | TO-220 MOSFET, strip = metalen tab | 10 × 15 mm |
| Zwarte halve cilinder | TO-92 2N3904 | 5 mm |
| Rode of groene bol | led van de testlast | 5 mm |

De TO-220's zijn half doorzichtig getekend, anders zie je de gaten en draden eronder niet meer.

### Tekens

| Teken | Betekenis |
|---|---|
| Gekleurd bolletje met tekstlabel | gat waar een draad van de ESP32 in komt, met het GPIO-nummer erbij |
| Streepjescirkel met M+ of M− | hier komen de twee motordraden |
| Geel bolletje links | accudraad, via de zekering en de schakelaar |
| `G D S` onder een TO-220 | gate, drain, source, van links naar rechts |
| `C B E` onder een TO-92 | collector, basis, emitter, van links naar rechts |
| Schaalbalk onderaan | 10 gaten = 25,4 mm |

### Richting van de onderdelen

- **TO-220 (IRF9540N, IRLZ44N):** tekstkant naar jou, metalen tab naar rij a.
- **TO-92 (2N3904):** platte kant van je weg, naar rij a. Dan staan de pootjes C B E, net als op de tekening.
- **Elco:** de witte streep is de min en gaat naar GND.

### Verbindingen op het bord

- Rijen a–e en f–j: elke rij van 5 gaten is onderling verbonden. De gleuf in het midden scheidt boven en onder.
- De + en − rails zijn halverwege onderbroken. Leg daar een draadje over, anders staat de rechterhelft dood.

## Bestanden

| Bestand | Wat |
|---|---|
| `DIY-Auto.kicad_sch` | Schema. **Wordt overschreven door het script** |
| `DIY-Auto.net` | Netlist, invoer voor de breadboardtekening |
| `DIY-Auto.kicad_bbrd` | Breadboardsessie voor de plugin Breadboard Builder |
| `DIY-Auto_schema.pdf` | Export om af te drukken |
| `.history/` | Automatische back-ups van KiCad zelf |

## Opnieuw genereren

Alles gebeurt vanuit de projectmap één niveau hoger:

```
cd ~/Personal\ Projects/Second\ brain/Projects/DIY\ Auto\ Project
```

Schema:

```
KICAD_SYMBOL_DIR=/usr/share/kicad/symbols ~/Personal\ Projects/DIY-Auto/.venv/bin/python Scripts/gen_schematic.py
kicad-cli sch erc KiCad/DIY-Auto.kicad_sch
kicad-cli sch export netlist -o KiCad/DIY-Auto.net KiCad/DIY-Auto.kicad_sch
kicad-cli sch export pdf -o KiCad/DIY-Auto_schema.pdf KiCad/DIY-Auto.kicad_sch
```

Breadboardtekening en sessiebestand:

```
~/Personal\ Projects/DIY-Auto/.venv/bin/python Scripts/gen_breadboard.py KiCad/DIY-Auto.net ../../Assets/DIY-Auto_breadboard.png KiCad/DIY-Auto.kicad_bbrd
```

Dat script controleert zichzelf tegen de netlist en moet `OK: 14 netten identiek aan KiCad` printen.

**Sluit KiCad voor je het schema opnieuw genereert.** Het script overschrijft `DIY-Auto.kicad_sch`, dus wat je in KiCad zelf tekende, is dan weg.

## Bekende waarschuwingen

4× `lib_symbol_mismatch` bij de 2N3904. Die komen doordat het script afgeleide symbolen anders inbedt dan KiCad. Elektrisch verandert er niets. Opruimen kan met **Tools → Update Symbols from Library**, maar doe dat pas als je niets meer genereert.
