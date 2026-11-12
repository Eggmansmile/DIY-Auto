"""Build one SolidCraft part and check it against the old build123d STEP.

    python sc_build.py <part>            # e.g. body, knuckle_R
    python sc_build.py --params          # only rewrite CAD/solidcraft/params.json

CAD/solidcraft/scripts/<part>.json is a SolidCraft command script ({"commands": [...]}) without parameters;
the parameters from params.py are put in front of it, so every part file carries the same named dimensions.
Output: CAD/solidcraft/parts/<part>.sc and a volume/bbox comparison with CAD/parts/*/<part>.step.
"""
import ast, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent.parent / "CAD"
SC = ROOT / "solidcraft"
CLI = ["flatpak", "run", "--command=solidcraft-cli", "io.tangencylabs.solidcraft"]
UNITLESS = {"Z_PIN", "Z_GEAR"}
DEGREES = {"LOCK"}


def unit(name, expr):
    if name in UNITLESS:
        return expr
    return f"{expr} deg" if name in DEGREES else f"{expr} mm"


def params():
    """params.py → parameters.add commands. Tuples/dicts become NAME_0 / NAME_key; strings and point lists are skipped."""
    src = (HERE / "params.py").read_text()
    lines = src.splitlines()
    out = []

    def add(name, node, comment):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return
        expr = ast.get_source_segment(src, node)
        # expressions name other parameters; plain numbers get their unit
        is_num = isinstance(node, ast.Constant) or (isinstance(node, ast.UnaryOp) and isinstance(node.operand, ast.Constant))
        p = {"name": name, "expression": unit(name, expr) if is_num else expr, "comment": comment}
        if name in UNITLESS:
            p["unit"] = ""
        out.append({"command": "parameters.add", "params": p})

    for n in ast.parse(src).body:
        if not isinstance(n, ast.Assign):
            continue
        comment = lines[n.lineno - 1].partition("#")[2].strip()[:200]
        tgt, val = n.targets[0], n.value
        if isinstance(tgt, ast.Tuple):                      # A, B = 1, 2
            for t, v in zip(tgt.elts, val.elts):
                add(t.id, v, comment)
        elif isinstance(val, ast.Tuple):                    # BATT = (13, 93, ...)
            for i, v in enumerate(val.elts):
                add(f"{tgt.id}_{i}", v, comment)
        elif isinstance(val, ast.Call) and getattr(val.func, "id", "") == "dict":
            for kw in val.keywords:
                if isinstance(kw.value, ast.Tuple):
                    for i, v in enumerate(kw.value.elts):
                        add(f"{tgt.id}_{kw.arg}_{i}", v, comment)
                else:
                    add(f"{tgt.id}_{kw.arg}", kw.value, comment)
        elif isinstance(val, ast.List):
            continue                                        # point lists (outline, holes): coordinates go in the sketch
        else:
            add(tgt.id, val, comment)
    (SC / "params.json").write_text(json.dumps({"commands": out}, indent=1))
    return out


def cli(*args):
    r = subprocess.run(CLI + list(args), capture_output=True, text=True, cwd=SC)
    err = "\n".join(l for l in r.stderr.splitlines() if not l.startswith("F: "))
    return r.returncode, r.stdout, err


def measure(*paths, only=None):
    bodies = []
    for path in paths:
        code, out, err = cli("eval", str(path))
        if code:
            sys.exit(f"eval {path} failed:\n{err}")
        bodies += [b for b in json.loads(out)["bodies"] if only is None or b["name"] in only]
    vol = sum(b["volume_mm3"] for b in bodies)
    lo = [min(b["bbox"]["min"][i] for b in bodies) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in bodies) for i in range(3)]
    return vol, lo, hi, len(bodies)


def build(part, cmds):
    """Run scripts/<part>.json and compare with the old STEP(s). A thin design (first command component.insert_design: links
    its source and mirrors it) gets no parameters of its own, and only its body <part> is measured (the linked source body
    is in the file too)."""
    own = json.loads((SC / "scripts" / f"{part}.json").read_text())["commands"]
    thin = own[0]["command"] == "component.insert_design"
    full = SC / "scripts" / f".{part}.full.json"
    full.write_text(json.dumps({"commands": own if thin else cmds + own}))
    code, out, err = cli("run", str(full), "--save", f"parts/{part}.sc", "--param-check", "warn", "--quiet")
    if code:
        sys.exit(f"run failed:\n{err}\n{out}")
    if err:
        print(err)
    new = measure(SC / "parts" / f"{part}.sc", only={part} if thin else None)
    ref = sorted(ROOT.glob(f"parts/*/{part}.step")) or sorted(ROOT.glob(f"parts/*/{part}_[LR].step"))
    return new, ref


def report(label, new, ref):
    print(f"{label}: new vol {new[0]:.1f} mm3, bbox {[round(v, 2) for v in new[1]]} .. {[round(v, 2) for v in new[2]]}, bodies {new[3]}")
    if ref:
        old = measure(*ref)
        dv = (new[0] - old[0]) / old[0] * 100
        db = max(abs(a - b) for a, b in zip(new[1] + new[2], old[1] + old[2]))
        print(f"{label}: old vol {old[0]:.1f} mm3, bbox {[round(v, 2) for v in old[1]]} .. {[round(v, 2) for v in old[2]]}")
        print(f"{'OK' if abs(dv) < 0.5 and db < 0.05 else 'DIFF'} {label}: volume {dv:+.2f} %, bbox max deviation {db:.3f} mm")


def main():
    SC.mkdir(exist_ok=True)
    (SC / "parts").mkdir(exist_ok=True)
    cmds = params()
    if sys.argv[1] == "--params":
        print(f"{len(cmds)} parameters → {SC / 'params.json'}")
        return
    if sys.argv[1] == "--pair":
        # python sc_build.py --pair rim_front [R|L]: build the source (default R; L for knuckle), then the thin design, and
        # compare each side and the sum of both with the old L + R STEPs
        base, src = sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else "R")
        oth = "L" if src == "R" else "R"
        a, ra = build(f"{base}_{src}", cmds)
        b, rb = build(f"{base}_{oth}", cmds)
        report(f"{base}_{src}", a, ra)
        report(f"{base}_{oth}", b, rb)
        tot = (a[0] + b[0], [min(x, y) for x, y in zip(a[1], b[1])], [max(x, y) for x, y in zip(a[2], b[2])], a[3] + b[3])
        report(f"{base} (L+R)", tot, ra + rb)
        return
    new, ref = build(sys.argv[1], cmds)
    report(sys.argv[1], new, ref)


if __name__ == "__main__":
    main()
