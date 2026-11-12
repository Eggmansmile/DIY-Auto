"""Export the SolidCraft parts (CAD/solidcraft/parts/*.sc) to the STEP/STL tree in CAD/parts.

    ~/.local/bin/uv run -p 3.12 --with build123d --with trimesh --with networkx python export_sc.py [--dry|--apply|--manifest] [part ...]

--dry (default) writes to CAD/parts_sc/, --apply overwrites CAD/parts/. Assembly-coordinate STEP + STL come straight from
SolidCraft (file.export_step / file.export_stl); print/ copies are made like assemble.py: the exported STEP is re-read with
build123d, put through print_orientation (from the old assemble.py, now in archive_build123d/) and written again.
--apply also rewrites CAD/manifest.json + CAD/BOM.md; --manifest does only that. The subassembly folder of each file is looked up in the old CAD/parts tree.
"""
import json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
CAD = HERE.parent.parent / "CAD"
SC = CAD / "solidcraft"
CLI = ["flatpak", "run", "--command=solidcraft-cli", "io.tangencylabs.solidcraft"]

# .sc file -> {old file stem: [bodies in that file]}; servo_clamp was one old file holding both clamps.
# wheels/tyres/knuckles: the thin design <part>_<other side>.sc holds both bodies (linked source + mirror), see sc_build.py --pair
FILES = {
    "body": {"body": ["body"]},
    "clamp": {"clamp_L": ["clamp_L"], "clamp_R": ["clamp_R"]},
    "knuckle_R": {"knuckle_L": ["knuckle_L"], "knuckle_R": ["knuckle_R"]},
    "rim_front_L": {"rim_front_L": ["rim_front_L"], "rim_front_R": ["rim_front_R"]},
    "rim_rear_L": {"rim_rear_L": ["rim_rear_L"], "rim_rear_R": ["rim_rear_R"]},
    "tyre_front_L": {"tyre_front_L": ["tyre_front_L"], "tyre_front_R": ["tyre_front_R"]},
    "tyre_rear_L": {"tyre_rear_L": ["tyre_rear_L"], "tyre_rear_R": ["tyre_rear_R"]},
    "tie_rod": {"tie_rod_L": ["tie_rod_L"], "tie_rod_R": ["tie_rod_R"]},
    "servo_horn": {"servo_horn": ["servo_horn"]},
    "servo_clamp": {"servo_clamp": ["servo_clamp_rear", "servo_clamp_front"]},
    "spacer_buck": {"spacer_buck": ["spacer_buck"]},
}


def print_orientation(name, shape):  # copy of assemble.print_orientation
    from build123d import Rot, Pos
    if name.startswith(("rim_", "tyre_")):
        shape = Rot(-90 if name.endswith("_L") else 90, 0, 0) * shape
    if name.startswith("tie_rod_"):
        shape = Rot(180, 0, 0) * shape
    if name == "servo_horn":
        shape = Rot(180, 0, 0) * shape
    if name.startswith("knuckle_"):
        shape = Rot(90 if name.endswith("_L") else -90, 0, 0) * shape
    b = shape.bounding_box()
    return Pos(-b.center().X, -b.center().Y, -b.min.Z) * shape


def export_stl(shape, path):  # copy of assemble.export_stl
    import trimesh
    from build123d import export_stl as _e
    _e(shape, path, tolerance=0.02, angular_tolerance=0.1)
    m = trimesh.load(path)
    m.merge_vertices()
    ok = m.nondegenerate_faces()
    if not ok.all():
        m.update_faces(ok)
        m.remove_unreferenced_vertices()
        m.export(path)


def sc_export(sc, bodies, step, stl):
    cmds = [{"command": "file.export_step", "params": {"path": str(step), "bodies": bodies}},
            {"command": "file.export_stl", "params": {"path": str(stl), "bodies": bodies, "quality": "fine"}}]
    script = SC / "scripts" / ".export.json"
    script.write_text(json.dumps({"commands": cmds}))
    r = subprocess.run(CLI + ["run", str(script), "--in", str(sc), "--quiet"], capture_output=True, text=True, cwd=SC)
    if r.returncode:
        raise RuntimeError("\n".join(l for l in r.stderr.splitlines() if not l.startswith("F: ")) + r.stdout)


def write_manifest():
    """CAD/manifest.json + CAD/BOM.md (was assemble.py). Part metadata (kind, qty, material, colour) stays in the existing
    manifest.json; only volume_mm3 is re-measured from the STEPs in CAD/parts. New parts: add an entry to manifest.json by hand."""
    from build123d import import_step
    mf = CAD / "manifest.json"
    manifest = json.loads(mf.read_text())
    for m in manifest:
        shape = import_step(str(CAD / "parts" / m["subassembly"] / f"{m['name']}.step"))
        m["volume_mm3"] = round(sum(s.volume for s in shape.solids()), 1)     # Compound.volume is unreliable for nested compounds
    mf.write_text(json.dumps(manifest, indent=1))
    rows = {"printed": [], "bought": [], "fastener": []}      # references such as motors and the PCB envelope stay out
    for m in manifest:
        if m["kind"] in rows:
            rows[m["kind"]].append(m)
    L = ["# DIY-Auto — BOM uit het CAD-model", "", "Gegenereerd door `Scripts/cad/export_sc.py`. Aankoopstatus en links: [[DIY Auto BOM]].", ""]
    for kind, title in (("printed", "Geprint"), ("bought", "Gekocht"), ("fastener", "Bevestiging")):
        L += [f"## {title}", "", "| # | Onderdeel | Materiaal / spec | Subassembly |", "|---|---|---|---|"]
        L += [f"| {m['qty']} | {m['name']} | {m['material']} | {m['subassembly']} |" for m in rows[kind]]
        L.append("")
    (CAD / "BOM.md").write_text("\n".join(L))
    print("manifest + BOM:", len(manifest), "objects")


def main():
    args = sys.argv[1:]
    apply = "--apply" in args
    only = [a for a in args if not a.startswith("--")]
    root = CAD / ("parts" if apply else "parts_sc")
    old = CAD / "parts"
    failed = []
    for part, files in FILES.items():
        if only and part not in only:
            continue
        for stem, bodies in files.items():
            hits = sorted(old.glob(f"*/{stem}.step"))
            if len(hits) != 1:
                failed.append((stem, f"old STEP not found uniquely: {hits}"))
                continue
            sub = hits[0].parent.name
            printed = (old / sub / "print" / f"{stem}.step").exists()
            out = root / sub
            (out / "print").mkdir(parents=True, exist_ok=True)
            try:
                sc_export(SC / "parts" / f"{part}.sc", bodies, out / f"{stem}.step", out / f"{stem}.stl")
                if printed:
                    from build123d import import_step, export_step
                    pr = print_orientation(stem, import_step(str(out / f"{stem}.step")))
                    export_step(pr, str(out / "print" / f"{stem}.step"))
                    export_stl(pr, str(out / "print" / f"{stem}.stl"))
                print("ok  ", sub, stem, "(+print)" if printed else "")
            except Exception as e:
                failed.append((stem, str(e)[:300]))
                print("FAIL", stem, str(e)[:300])
    if apply or "--manifest" in args:
        write_manifest()
    print(f"-> {root}; {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
