"""Extra STEP files for the FreeCAD assembly: assemble.py skips the motors (Blender uses the real STL),
FreeCAD gets the solid stand-in from frame.py instead.

Run from Scripts/cad/:
    ~/.local/bin/uv run -p 3.12 --with build123d --with bd_warehouse python freecad_export.py
"""
from pathlib import Path
from build123d import export_step
import frame

STEP = Path(__file__).resolve().parents[2] / "CAD" / "parts" / "1 frame"   # frame.py builds the motors
parts = frame.build()
for name in ("motor_L", "motor_R"):
    export_step(parts[name].shape, str(STEP / f"{name}.step"))
    print("OK", name)
