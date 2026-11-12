# Brief: rebuild a DIY-Auto part natively in SolidCraft

Project: `~/Personal Projects/Second brain/Projects/DIY Auto Project/` (call it P). The car's CAD is build123d code in `P/Scripts/cad/` (`params.py` dimensions, `lib.py` helpers, one script per subassembly). You rebuild your part(s) as a SolidCraft command script so the owner can later edit it feature by feature in the SolidCraft GUI.

## What you write
Only `P/CAD/solidcraft/scripts/<part>.json`: `{"commands": [ {"command": "...", "params": {...}}, ... ]}`. Do not write parameters in it: `sc_build.py` puts all 139 parameters from `params.py` in front (see `P/CAD/solidcraft/params.json` for the exact names: tuples/dicts became `NAME_0`, `NAME_key`, e.g. `BATT_0`, `BUCK_cx`, `HOOK_x_0`). Touch no other file.

## Build and check (run from `P/Scripts/cad/`)
`python3 sc_build.py <part>` runs the script headless, saves `P/CAD/solidcraft/parts/<part>.sc` and compares volume + bounding box with the old STEP(s) in `P/CAD/parts/*/`. Iterate until it prints `OK` (volume within 0.5 %, bbox within 0.05 mm). Inspect the old STEP with `flatpak run --command=solidcraft-cli io.tangencylabs.solidcraft eval "<path.step>"` (bodies, faces, face_types, bbox) if you need it. Run snapshots with `... snapshot "<P>/CAD/solidcraft/parts/<part>.sc" --out /tmp/sc/<part>.png --view iso` and look at them with Read.

## Rules
- Same coordinates as the assembly STEP in `P/CAD/parts/<subassembly>/<part>.step` (NOT the `print/` copy). The part is inserted into the master at its own origin.
- Every dimension that comes from `params.py` is an expression with the parameter name (`"RW_R - RIM_LIP"`), not a number. Numbers only for constants that are literal in the build123d script.
- Follow the build123d script's feature order: one SolidCraft feature per build123d operation where possible, every feature named (`name`) in plain English ("Rim web", "Bearing seat L"). Prefer primitives (`solid.box`, `solid.cylinder`, `solid.hole`) over sketches when the shape is a box/cylinder; sketch + extrude/revolve otherwise.
- Left/right pairs: ONE file holds both bodies. Build the R side, then `solid.mirror` (plane XZ, the car is symmetric about y = 0, check against the L STEP) so one edit changes both. Body names must equal the old part names (`rim_rear_R`, `rim_rear_L`).
- If a feature truly cannot be made in SolidCraft 0.40, leave it out, finish the rest, and report exactly which feature and the volume it accounts for. Do not approximate silently.
- Docs: `P/CAD/solidcraft/docs/skill_index.md` (command shapes, plane axes, traps: READ FIRST), `P/CAD/solidcraft/docs/skill_SKILL.md` (workflow), `P/CAD/solidcraft/docs/instructions.md`. Full command list (6000 lines JSON): `P/CAD/solidcraft/docs/commands.json`; grep it by id, e.g. `python3 -c "import json;[print(c['params']) for c in json.load(open('P/CAD/solidcraft/docs/commands.json')) if c['id']=='solid.revolve']"`.

## Report (max 10 lines)
Part(s), last `sc_build.py` result line(s), features you could not reproduce, anything the owner must know. No dumps.
