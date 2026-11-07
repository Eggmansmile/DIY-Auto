# DIY Auto — V1

RC car: ESP32 + TB6612FNG motor driver, two rear DC motors, servo steering, 2S Li-ion battery.
Everything is generated from code. Edit the script, not the output.

| Folder | What |
|---|---|
| `Scripts/cad/` | build123d CAD. Dimensions in `params.py`, `assemble.py` writes STEP/STL to `CAD/parts/`, `check_all.py` checks collisions, `plates.py` makes print plates. |
| `CAD/` | Generated STEP/STL per subassembly, print plates (`.3mf`), FreeCAD assembly, `BOM.md`. |
| `Scripts/` | `gen_schematic.py` → `gen_pcb.py` → `route_pcb.py` → `silk_pcb.py` (KiCad), breadboard and Fritzing generators. |
| `KiCad/` | Schematic, PCB, gerbers (`DIY-Auto_rev8_gerbers_PCBWay.zip` is the version to order). |
| `Fritzing/` | Breadboard views. |
| `Firmware/` | Arduino test sketches (`test_drive`, `test_tb6612`, ...). |
| `Video/` | Assembly animation (Blender script + Remotion). |
| `*.md` | Build notes (Dutch, Obsidian): electronics, mechanics, BOM, assembly, firmware. |

The servo reference model (SpringRC SM-S2309S, Thingiverse 2835648) is not included.

## Licence

- Code (`Scripts/`, `Firmware/`, `Video/` scripts): [MIT](LICENSE)
- Hardware design (`CAD/`, `KiCad/`, `Fritzing/`, `Drawings/`) and notes: [CERN-OHL-P-2.0](LICENSE-HARDWARE)
