# archive_build123d

The old build123d generators of the printed parts and the assembly (`frame.py`, `rear_drive.py`, `front_wheels.py`, `steering.py`, `electronics.py`, `assemble.py`, `freecad_export.py`). SolidCraft (`CAD/DIY-Auto.sc`) is now the master CAD; `export_sc.py` writes the STEP/STL, `check_all.py` and `gen_drawing.py` read those STEPs.

They still run when copied back into `Scripts/cad/` next to `lib.py` and `params.py` (`assemble.py` then overwrites `CAD/parts/` and `manifest.json` from code, so back up first).
