"""Builds every approved subassembly, exports STEP + STL per part into CAD/parts/<subassembly>/ (print-oriented copies
in its print/ folder), writes CAD/manifest.json.

Run from Scripts/cad/:
    ~/.local/bin/uv run -p 3.12 --with build123d --with bd_warehouse --with trimesh --with networkx python assemble.py
Then the Blender file:  (from the project folder)  blender --background --python Scripts/cad/blender_assembly.py
"""
import json
from pathlib import Path
from build123d import export_step, export_stl as _export_stl, Rot, Pos
import trimesh
import frame, rear_drive, front_wheels, steering, electronics

SUBASSEMBLIES = [("1 frame", frame), ("2 rear drive", rear_drive), ("3 front wheels", front_wheels), ("4 steering", steering),
                 ("5 electronics", electronics)]
CAD = Path(__file__).resolve().parents[2] / "CAD"



def export_stl(shape, path, **kw):
    """STL export + drop the zero-area triangles build123d leaves at the heat-set insert seams (they show up as open edges)."""
    _export_stl(shape, path, **kw)
    m = trimesh.load(path)
    m.merge_vertices()
    ok = m.nondegenerate_faces()
    if not ok.all():
        m.update_faces(ok)
        m.remove_unreferenced_vertices()
        m.export(path)


def print_orientation(name, shape):
    """Printed parts laid on the bed: body parts floor down, clamps split face down, wheels outer face down,
    knuckles on the side plate, axles on their flat, tie rods flat."""
    if name.startswith(("rim_", "tyre_")):
        shape = Rot(-90 if name.endswith("_L") else 90, 0, 0) * shape
    if name.startswith("tie_rod_"):                            # flat top on the bed: the right rod's boss points down in the car
        shape = Rot(180, 0, 0) * shape
    if name == "servo_horn":                                   # top face on the bed, bore opens upward
        shape = Rot(180, 0, 0) * shape
    if name.startswith("knuckle_"):                            # v5: flat feet (inner side) on the bed, spacer up
        shape = Rot(90 if name.endswith("_L") else -90, 0, 0) * shape
    b = shape.bounding_box()
    return Pos(-b.center().X, -b.center().Y, -b.min.Z) * shape

manifest = []
for label, mod in SUBASSEMBLIES:
    print(f"--- {label}")
    out = CAD / "parts" / label
    (out / "print").mkdir(parents=True, exist_ok=True)
    for name, p in mod.build().items():
        vol = sum(s.volume for s in p.shape.solids())          # Compound.volume is unreliable for nested compounds
        if not name.startswith("motor_"):                         # Blender uses the real motor STL from CAD/ref
            export_step(p.shape, str(out / f"{name}.step"))
            export_stl(p.shape, str(out / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
        if p.kind == "printed":
            pr = print_orientation(name, p.shape)
            export_stl(pr, str(out / "print" / f"{name}.stl"), tolerance=0.02, angular_tolerance=0.1)
            export_step(pr, str(out / "print" / f"{name}.step"))
        manifest.append(dict(name=name, subassembly=label, kind=p.kind, qty=p.qty, material=p.material,
                             colour=p.colour, volume_mm3=round(vol, 1)))
        print(f"{name:22s} {p.kind:9s} x{p.qty:<2d} {vol:10.1f} mm3  {p.material}")
(CAD / "manifest.json").write_text(json.dumps(manifest, indent=1))
# BOM from the manifest (references such as motors and the PCB envelope stay out)
rows = {"printed": [], "bought": [], "fastener": []}
for m in manifest:
    if m["kind"] in rows:
        rows[m["kind"]].append(m)
L = ["# DIY-Auto — BOM uit het CAD-model", "", "Gegenereerd door `Scripts/cad/assemble.py`. Aankoopstatus en links: [[DIY Auto BOM]].", ""]
for kind, title in (("printed", "Geprint"), ("bought", "Gekocht"), ("fastener", "Bevestiging")):
    L += [f"## {title}", "", "| # | Onderdeel | Materiaal / spec | Subassembly |", "|---|---|---|---|"]
    L += [f"| {m['qty']} | {m['name']} | {m['material']} | {m['subassembly']} |" for m in rows[kind]]
    L.append("")
(CAD / "BOM.md").write_text("\n".join(L))
print("OK:", len(manifest), "objects ->", CAD)
