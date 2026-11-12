import json, math
m, z, bl = 0.5, 90, 0.30
n = 8
a = math.radians(20)
rp, ra, rf = m*z/2, m*z/2+m, m*z/2-1.25*m
rb = rp*math.cos(a); inv_a = math.tan(a)-a
half = math.pi/(2*z) - bl/2/rp
t0 = math.sqrt(max((max(rb, rf)/rb)**2-1, 0)); t1 = math.sqrt((ra/rb)**2-1)
fl = []
for i in range(n+1):
    t = t0+(t1-t0)*i/n
    x, y = rb*(math.cos(t)+t*math.sin(t)), rb*(math.sin(t)-t*math.cos(t))
    fl.append((math.hypot(x, y), math.atan2(y, x)))
pol = lambda r, th: (r*math.cos(th), r*math.sin(th))
lo = [pol(r, -half-inv_a+th) for r, th in fl]
hi = [pol(r, half+inv_a-th) for r, th in reversed(fl)]
a_lo, a_hi = -half-inv_a+fl[0][1], half+inv_a-fl[0][1]
pts = [pol(rf-0.3, a_lo)] + lo + hi + [pol(rf-0.3, a_hi)]
# gear-local (u,v) -> sketch on XZ: (u, -AXLE_Z - v)
sk = [[round(u, 5), round(-35-v, 5)] for u, v in pts]
C = []
def add(c, **p): C.append({"command": c, "params": p})
def prof(name, pl, off="AXLE_Z"):
    add("sketch.create", plane="XY", offset=off, name=name+" sketch")
    add("sketch.line", points=pl, closed=True)
    add("sketch.finish")
def rev(name, pl, op):
    prof(name, pl)
    add("solid.revolve", axis="y", operation=op, name=name)
Y = lambda s: "-(%s)" % s
add("solid.cylinder", radius="MOD*Z_GEAR/2 - 1.25*MOD", height="GEAR_W", base=["0", "-RW_Y0", "AXLE_Z"], axis="Y", operation="new", body_name="rim_rear_R", name="Gear root disc")
add("sketch.create", plane="XZ", offset="-RW_Y0", name="Gear tooth sketch")
add("sketch.line", points=sk, closed=True)
add("sketch.finish")
add("solid.extrude", distance="GEAR_W", operation="join", name="Gear tooth")
add("solid.pattern.circular", features=["Gear tooth"], axis={"origin": ["0", "-RW_Y0", "AXLE_Z"], "dir": [0, 1, 0]}, count="Z_GEAR", name="Gear teeth")
rev("Rim ring", [["26.5","-RW_Y0"],["RIM_R + RIM_LIP","-RW_Y0"],["RIM_R + RIM_LIP","-(RW_Y0+1)"],["RIM_R","-(RW_Y0+1)"],
   ["RIM_R","-(RW_Y1-1)"],["RIM_R + RIM_LIP","-(RW_Y1-1)"],["RIM_R + RIM_LIP","-RW_Y1"],["26.5","-RW_Y1"]], "join")
rev("Cone outer", [[26.6,-61.9],[26.6,-58.4],[20.2,-52],[16.8,-52]], "join")
rev("Cone inner", [[7.4,-51],[19.9,-51],[19.9,-52],[7.4,-64.5]], "join")
add("solid.cylinder", radius=7.5, height="RW_Y1 - GY0", base=["0","-RW_Y1","AXLE_Z"], axis="Y", operation="join", name="Hub")
add("solid.cylinder", radius="AXLE_FREE/2", height="RW_Y1 - GY0 + 2", base=["0","-RW_Y1 - 1","AXLE_Z"], axis="Y", operation="cut", name="Axle bore")
add("solid.cylinder", radius="SEAT_D/2", height="BEARING_W + 1", base=["0","-(GY0 + BEARING_W)","AXLE_Z"], axis="Y", operation="cut", name="Bearing seat gear side")
add("solid.cylinder", radius="SEAT_D/2", height="BEARING_W + 1", base=["0","-RW_Y1 - 1","AXLE_Z"], axis="Y", operation="cut", name="Bearing seat outer side")
rev("Pinion clearance", [[19.5,"-(RW_Y0 - 0.01)"],[28.2,"-(RW_Y0 - 0.01)"],[28.2,"-(RW_Y0 + 0.6)"],[19.5,"-(RW_Y0 + 0.6)"]], "cut")
add("solid.box", length=2, width="RW_Y1 - RW_Y0 - 2", height=1.3, center=["0","-(RW_Y0+RW_Y1)/2","AXLE_Z - RIM_R - 0.15"], operation="join", name="Tyre key")
add("solid.pattern.circular", features=["Tyre key"], axis={"origin": ["0","0","AXLE_Z"], "dir": [0,1,0]}, count=3, name="Tyre keys")
add("solid.mirror", bodies=["rim_rear_R"], plane="XZ", name="Mirror rim")
add("body.rename", body="rim_rear_R (2)", name="rim_rear_L")
json.dump({"commands": C}, open("CAD/solidcraft/scripts/rim_rear.json", "w"), indent=0)
