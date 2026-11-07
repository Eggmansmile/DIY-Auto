# DIY Auto Project — map for Claude

RC car: ESP32 + TB6612 motor driver, 2 rear motors, servo steering, 2S battery. Everything is generated from code; edit the script, not the output.

Git: public repo github.com/Eggmansmile/DIY-Auto (main, tag `v1`). Video frames/stills, `.venv`, Fritzing parts clone, KiCad `.history` and the third-party servo model are in `.gitignore`. Absolute paths are stripped on commit by the `homepath` clean filter (`.gitattributes` + `.git/config`). Licences: MIT (code), CERN-OHL-P-2.0 (hardware).

## Notes (Dutch, Obsidian)
`DIY Auto.md` (hub) · `DIY Auto Elektronica.md` · `DIY Auto Mechanisch.md` · `DIY Auto Firmware.md` · `DIY Auto BOM.md` · `DIY Auto Assemblage.md` · `DIY Auto Breadboard.md` · `PCB bestellen en solderen.md` · `Testblok passingen.md` · `Taken DIY-Auto.md` · `DIY-Auto Project.canvas`

## CAD (build123d, `Scripts/cad/`, run from that folder)
- Dimensions: `params.py` (all in one place); helpers: `lib.py`.
- Subassemblies: `frame.py` (1) · `rear_drive.py` (2) · `front_wheels.py` (3) · `steering.py` (4) · `electronics.py` (5).
- `assemble.py` → STEP + STL per part in `CAD/parts/<n subassembly>/` + `CAD/manifest.json`, `CAD/BOM.md`.
- `check_all.py` = collision/clearance check after every change. `plates.py` → print plates `CAD/plates/*.3mf` (P1S, A1 mini). `test_fit.py` = fit test block. `gen_drawing.py` = A3 drawing. `freecad_assembly.py` / `freecad_export.py` = FreeCAD 1.1 assembly.

## Electronics (`Scripts/`, output in `KiCad/`, `Fritzing/`)
Order: `gen_schematic.py` → `gen_pcb.py` → `route_pcb.py` (Freerouting) → `silk_pcb.py`; gerbers in `KiCad/gerbers/`. `gen_breadboard.py` (checked against the netlist), `gen_fritzing.py` (print version), `gen_fritzing_hbrug.py` (learning version, own H-bridges). How to open the KiCad breadboard: `KiCad/README.md`.

## Firmware (`Firmware/<sketch>/<sketch>.ino`)
Test sketches: `test_drive`, `test_drive_hbrug`, `test_hbridge`, `test_tb6612`, `pintest`, `debug_hold`.
