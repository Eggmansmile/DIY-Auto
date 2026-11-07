"""Shared build123d helpers for the DIY-Auto subassemblies."""
import math
from dataclasses import dataclass
from build123d import *
from params import *


@dataclass
class Part:
    shape: object
    colour: str
    kind: str            # "printed" | "fastener" | "bought"
    qty: int = 1
    material: str = ""   # printed: PETG / TPU 95A; fastener/bought: designation for the BOM


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(x1 - x0, y1 - y0, z1 - z0)

def cy(x, y0, y1, z, r):
    """Cylinder along y."""
    return Pos(x, (y0 + y1) / 2, z) * Rot(90, 0, 0) * Cylinder(r, abs(y1 - y0))

def cz(x, y, z0, z1, r):
    """Cylinder along z."""
    return Pos(x, y, (z0 + z1) / 2) * Cylinder(r, z1 - z0)

def bar(p, q, z0, z1, w):
    """Flat bar with round ends from p to q (xy), between z0 and z1."""
    (px, py), (qx, qy) = p, q
    L, ang = math.hypot(qx - px, qy - py), math.degrees(math.atan2(qy - py, qx - px))
    b = Pos((px + qx) / 2, (py + qy) / 2, (z0 + z1) / 2) * Rot(0, 0, ang) * Box(L, w, z1 - z0)
    return b + cz(px, py, z0, z1, w / 2) + cz(qx, qy, z0, z1, w / 2)

def both(shape):
    return shape + mirror(shape, about=Plane.XZ)

def gear_face(m, z, backlash=0.0, n=8):
    """Involute spur gear outline in the XY plane, centred on the origin."""
    a = math.radians(20)
    rp, ra, rf = m * z / 2, m * z / 2 + m, m * z / 2 - 1.25 * m
    rb = rp * math.cos(a)
    inv_a = math.tan(a) - a
    half = math.pi / (2 * z) - backlash / 2 / rp
    t0 = math.sqrt(max((max(rb, rf) / rb) ** 2 - 1, 0))
    t1 = math.sqrt((ra / rb) ** 2 - 1)
    flank = []
    for i in range(n + 1):
        t = t0 + (t1 - t0) * i / n
        x, y = rb * (math.cos(t) + t * math.sin(t)), rb * (math.sin(t) - t * math.cos(t))
        flank.append((math.hypot(x, y), math.atan2(y, x)))
    pol = lambda r, th: (r * math.cos(th), r * math.sin(th))
    pts = []
    for k in range(z):
        c = 2 * math.pi * k / z
        lo = [pol(r, c - half - inv_a + th) for r, th in flank]
        hi = [pol(r, c + half + inv_a - th) for r, th in reversed(flank)]
        a_lo, a_hi = c - half - inv_a + flank[0][1], c + half + inv_a - flank[0][1]
        pts += [pol(rf, a_lo)] + lo + hi + [pol(rf, a_hi), pol(rf, a_hi + (2 * math.pi / z - (a_hi - a_lo)) / 2)]
    return Polygon(*pts, align=None)

def gear_y(m, z, x, y0, zc, width, backlash=0.0, phase=0.0):
    """Gear with its axis along y, from y0 to y0 + width. phase in degrees."""
    f = Rot(0, 0, phase) * gear_face(m, z, backlash)
    return Pos(x, y0 + width, zc) * Rot(90, 0, 0) * extrude(f, width, dir=(0, 0, 1))


def rev_y(pts, x, zc):
    """Revolve a closed (r, y) profile around the y axis through (x, zc)."""
    return Pos(x, 0, zc) * revolve(Polygon(*pts, align=None), Axis.Y)


def to_bed(s):
    """Move a shape so it is centred in x/y and rests on z = 0 (print orientation check)."""
    b = s.bounding_box()
    return Pos(-b.center().X, -b.center().Y, -b.min.Z) * s


def bearing(x, y0, zc):
    """MR105-2RS (5 x 10 x 4) along y from y0: outer ring, seal, inner race (OD 6.6)."""
    outer = cy(x, y0, y0 + BEARING_W, zc, BEARING_D / 2) - cy(x, y0 - 1, y0 + BEARING_W + 1, zc, 4.1)
    inner = cy(x, y0, y0 + BEARING_W, zc, 3.3) - cy(x, y0 - 1, y0 + BEARING_W + 1, zc, 2.5)
    seal = cy(x, y0 + 0.3, y0 + BEARING_W - 0.3, zc, 4.1) - cy(x, y0, y0 + BEARING_W, zc, 3.3)
    return outer + inner + seal


def tyre(x, zc, y0, y1, r_in, r_out, fillet_r, grooves, depth):
    """TPU tyre: rounded shoulders, transverse tread grooves."""
    prof = Pos((r_in + r_out) / 2, (y0 + y1) / 2) * Rectangle(r_out - r_in, y1 - y0)
    outer = [v for v in prof.vertices() if abs(v.X - r_out) < 1e-6]
    prof = fillet(outer, fillet_r)
    t = revolve(prof, Axis.Y)
    for k in range(grooves):
        g = Pos(r_out, (y0 + y1) / 2, 0) * Box(2 * depth, y1 - y0 - 2 * fillet_r, 1.6)
        t -= Rot(0, 360 * k / grooves, 0) * g
    return Pos(x, 0, zc) * t

def rim(x, zc, y0, y1, r, hub_r, web_t, holes_r, holes_at, inner_extra=0.0):
    """Spoked rim: outer ring, web on the outside face, hub with a bearing seat on both ends."""
    ring = cy(x, y0, y1, zc, r) - cy(x, y0 - 1, y1 + 1, zc, r - 2.5)
    web = cy(x, y1 - web_t, y1, zc, r - 1)
    for k in range(5):
        a = math.radians(72 * k + 90)
        web -= cy(x + holes_at * math.cos(a), y1 - web_t - 1, y1 + 1, zc + holes_at * math.sin(a), holes_r)
    hub = cy(x, y0 - inner_extra, y1, zc, hub_r)
    return ring + web + hub

def bore(x, zc, y0, y1):
    """Axle clearance + MR105 seat on both ends."""
    return (cy(x, y0 - 1, y1 + 1, zc, AXLE_FREE / 2) + cy(x, y0 - 1, y0 + BEARING_W, zc, BEARING_D / 2)
            + cy(x, y1 - BEARING_W, y1 + 1, zc, BEARING_D / 2))




def axle_bolt(x, y_head, z, spec, sy=1):
    """Socket head bolt along y: head outside at y_head (underside), shank inwards. sy = +1 left wheel, -1 right."""
    from bd_warehouse.fastener import SocketHeadCapScrew
    b = Pos(x, y_head, z) * Rot(-90, 0, 0) * SocketHeadCapScrew(*spec, "iso4762", simple=True)
    return b if sy > 0 else mirror(b, about=Plane.XZ)


def axle_nut(x, y0, z, h, af=8.0, d=5.0):
    """Hex nut along y from y0 to y0 + h, flats facing ±x (fits a slot of width af). Plain prism: bd_warehouse only has
    ISO 4032 (M5: 4.7 high), the car uses DIN 934 (4.0) and DIN 985 nylock (5.0). Mirror for the right side."""
    return hex_pocket(x, y0, y0 + h, z, af) - cy(x, y0 - 1, y0 + h + 1, z, d / 2)


def shim(x, y0, z):
    """Shim washer on the inner race, from y0 outwards."""
    d_in, d_out, t = SHIM
    return cy(x, y0, y0 + t, z, d_out / 2) - cy(x, y0 - 1, y0 + t + 1, z, d_in / 2)


def hex_pocket(x, y0, y1, z, af):
    """Hexagonal prism along y (flats facing ±x), for a nut pocket."""
    return Pos(x, y0, z) * Rot(-90, 0, 0) * Rot(0, 0, 30) * extrude(RegularPolygon(af / 2, 6, major_radius=False), y1 - y0)


def tyre_keys(x, zc, r, y0, y1, grow=0.0, n=3, w=2.0, h=0.8):
    """n ribs along the axle on the rim surface (radius r, between the lips y0..y1) so the TPU tyre cannot slip.
    grow > 0 gives the matching (larger) grooves to cut from the tyre."""
    ribs = None
    for k in range(n):
        rib = Pos(x, 0, zc) * Rot(0, 90 + 360 * k / n, 0) * Pos(r + (h - 0.5 + grow) / 2, (y0 + y1) / 2, 0) * \
            Box(h + 0.5 + grow, y1 - y0, w + grow)
        ribs = rib if ribs is None else ribs + rib
    return ribs
