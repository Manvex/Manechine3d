"""Reconstruieste aparatele din primitive (cutii + cilindri) in piese cu aspect realist.

Pastreaza neschimbate nodurile anchor_* / joint_* (nume, pozitii, extras) si impartirea pe
piese mobile; inlocuieste doar geometria:
  - profile de cadru cu colturi rotunjite si capace
  - perne tapitate bombate, role cu capete rotunjite, mansoane de prindere
  - greutati cu etichete, cui selector, carcasa turnului de greutati
  - tija de reglaj a sezutului cu buton galben, capace pe axele pivotilor

Rulare:  python3 tools/upgrade_machines.py <nume_asset> [--render]
Sursa este echipamente/glb_src/<nume>.glb (copia modelului original).
"""
import bpy, bmesh, sys, os, math, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from mathutils import Vector, Matrix

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'echipamente')
I3 = np.eye(3)

MATS = {  # culoare, metalic, rugozitate
    'powder': ((0.040, 0.042, 0.047, 1), 0.25, 0.42),
    'shroud': ((0.46, 0.47, 0.49, 1), 0.55, 0.36),
    'label':  ((0.86, 0.86, 0.84, 1), 0.0, 0.55),
    'accent': ((0.85, 0.52, 0.02, 1), 0.0, 0.40),
    'vinyl':  ((0.014, 0.014, 0.016, 1), 0.0, 0.50),
    'steel':  ((0.72, 0.72, 0.73, 1), 1.0, 0.22),
    'plastic': ((0.022, 0.022, 0.024, 1), 0.0, 0.40),
}


# ---------------------------------------------------------------- geometrie
class Geo:
    """Acumulator de varfuri/fete in coordonate lume."""
    def __init__(self):
        self.v = []; self.f = []

    def loft(self, rings, cap0=True, cap1=True):
        n = len(rings[0]); base = len(self.v)
        for r in rings:
            self.v.extend([tuple(p) for p in r])
        for k in range(len(rings) - 1):
            a = base + k * n; b = a + n
            for i in range(n):
                j = (i + 1) % n
                self.f.append((a + i, a + j, b + j, b + i))
        if cap0: self.f.append(tuple(base + i for i in reversed(range(n))))
        if cap1:
            a = base + (len(rings) - 1) * n
            self.f.append(tuple(a + i for i in range(n)))

    def quad(self, pts):
        b = len(self.v); self.v.extend([tuple(p) for p in pts]); self.f.append((b, b + 1, b + 2, b + 3))


def rr(a, b, r, seg=4):
    """Dreptunghi rotunjit a x b, raza r, CCW."""
    r = max(min(r, a / 2 - 1e-4, b / 2 - 1e-4), 1e-4)
    pts = []
    for cx, cy, a0 in ((a / 2 - r, b / 2 - r, 0), (-a / 2 + r, b / 2 - r, 90),
                       (-a / 2 + r, -b / 2 + r, 180), (a / 2 - r, -b / 2 + r, 270)):
        for i in range(seg + 1):
            t = math.radians(a0 + 90 * i / seg)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def circle(r, seg):
    return [(r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]


def ring(c, R, pts2, w, iu=0, iv=1, iw=2):
    """Plaseaza un profil 2D in cadrul (c, R): axele iu, iv in plan, iw de-a lungul."""
    out = []
    for (u, v) in pts2:
        p = np.zeros(3); p[iu] = u; p[iv] = v; p[iw] = w
        out.append(c + R @ p)
    return out


def axes_perm(d, long_axis):
    iw = long_axis
    iu, iv = [i for i in range(3) if i != iw]
    return iu, iv, iw


def tube(g, c, R, d, radius_k=0.28, rmax=0.02, seg=4):
    iw = int(np.argmax(d)); iu, iv, iw = axes_perm(d, iw)
    if (np.cross(R[:, iu], R[:, iv]) @ R[:, iw]) < 0: iu, iv = iv, iu
    r = min(radius_k * min(d[iu], d[iv]), rmax)
    prof = rr(d[iu], d[iv], r, seg); L = d[iw]
    g.loft([ring(c, R, prof, -L / 2, iu, iv, iw), ring(c, R, prof, L / 2, iu, iv, iw)])
    return iu, iv, iw, r


def tube_caps(g, c, R, d, iu, iv, iw, r):
    """Capace de plastic la capetele profilului."""
    prof = rr(d[iu] - 0.008, d[iv] - 0.008, max(r - 0.004, 0.002), 4); L = d[iw]
    for s in (-1, 1):
        a = ring(c, R, prof, s * (L / 2 - 0.001), iu, iv, iw); b = ring(c, R, prof, s * (L / 2 + 0.002), iu, iv, iw)
        g.loft([a, b] if s > 0 else [b, a])


def plate(g, c, R, d, rc=0.008, ch=0.0015):
    iw = int(np.argmin(d)); iu, iv, iw = axes_perm(d, iw)
    if (np.cross(R[:, iu], R[:, iv]) @ R[:, iw]) < 0: iu, iv = iv, iu
    t = d[iw]; ch = min(ch, t * 0.3)
    rings = []
    for o, h in ((ch, -t / 2), (0, -t / 2 + ch), (0, t / 2 - ch), (ch, t / 2)):
        rings.append(ring(c, R, rr(d[iu] - 2 * o, d[iv] - 2 * o, rc - o, 4), h, iu, iv, iw))
    g.loft(rings)
    return iu, iv, iw


def cushion(g, c, R, d, up=None):
    """Perna tapitata. up = +1/-1: fata de contact pe partea respectiva a axei subtiri; None = simetrica."""
    iw = int(np.argmin(d)); iu, iv, iw = axes_perm(d, iw)
    if (np.cross(R[:, iu], R[:, iv]) @ R[:, iw]) < 0: iu, iv = iv, iu
    a, b, t = d[iu], d[iv], d[iw]
    rc = min(0.30 * min(a, b), 0.07); seg = 6
    k = min(1.0, min(a, b) / 0.16)   # pernele mici au rotunjiri mai mici
    top = [(0.0, 0.50), (0.003 * k, 0.72), (0.010 * k, 0.88), (0.022 * k, 0.965), (0.045 * k, 1.0)]
    def R_(o, h):
        return ring(c, R, rr(a - 2 * o, b - 2 * o, rc - o, seg), (h - 0.5) * t, iu, iv, iw)
    def inner(s, h):
        base = rr(a - 0.09 * k, b - 0.09 * k, rc - 0.045 * k, seg)
        return ring(c, R, [(u * s, v * s) for u, v in base], (h - 0.5) * t, iu, iv, iw)
    crown = 0.004 / t
    upper = [R_(o, h) for o, h in top] + [inner(0.6, 1 + crown * 0.7), inner(0.15, 1 + crown)]
    if up is None:
        lower = [inner(0.15, -crown), inner(0.6, -crown * 0.7)] + [R_(o, 1 - h) for o, h in reversed(top)]
        rings = lower + upper
    else:
        lower = [R_(0.010, 0.0), R_(0.0, 0.10)]
        rings = lower + upper
        if up < 0:
            # oglindeste pe axa subtire
            rings = [[2 * (c + (np.array(p) - c) - ((np.array(p) - c) @ R[:, iw]) * R[:, iw]) - np.array(p) + 0 * c
                      for p in rg] for rg in rings]
            rings = [list(reversed(rg)) for rg in rings]
    g.loft(rings)
    return iu, iv, iw


def lathe(g, c, axis, prof, seg=20):
    """prof = [(z, r)] de-a lungul axei."""
    axis = axis / np.linalg.norm(axis)
    t = np.cross(axis, [0, 0, 1.0])
    if np.linalg.norm(t) < 1e-3: t = np.cross(axis, [1.0, 0, 0])
    t /= np.linalg.norm(t); b = np.cross(axis, t)
    rings = []
    for z, r in prof:
        rings.append([c + axis * z + (t * math.cos(2 * math.pi * i / seg) + b * math.sin(2 * math.pi * i / seg)) * r
                      for i in range(seg)])
    g.loft(rings)


def cyl(g, p0, p1, r, seg=14):
    p0 = np.array(p0, float); p1 = np.array(p1, float)
    L = np.linalg.norm(p1 - p0)
    lathe(g, p0, (p1 - p0) / L, [(0, r), (L, r)], seg)


def box(g, c, R, d):
    g.loft([ring(c, R, rr(d[0], d[1], 0.0015, 1), -d[2] / 2), ring(c, R, rr(d[0], d[1], 0.0015, 1), d[2] / 2)])



# ---------------------------------------------------------------- kit pentru cadre
def fillet_path(pts, r, seg=8):
    """Polilinie cu colturile inlocuite de arce de raza r."""
    pts = [np.array(p, float) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        la = np.linalg.norm(a - b); lc = np.linalg.norm(c - b)
        u = (a - b) / la; v = (c - b) / lc
        ang = math.acos(max(-1, min(1, u @ v)))
        ri = r[i] if isinstance(r, (list, tuple)) else r
        if ang > math.pi - 0.03 or ri <= 0:
            out.append(b); continue
        d = min(ri / math.tan(ang / 2), 0.48 * la, 0.48 * lc)
        rad = d * math.tan(ang / 2)
        bis = (u + v) / np.linalg.norm(u + v)
        cen = b + bis * (rad / math.sin(ang / 2))
        s0 = b + u * d - cen; s1 = b + v * d - cen
        th = math.acos(max(-1, min(1, (s0 @ s1) / (rad * rad))))
        for k in range(seg + 1):
            t = k / seg
            w = (math.sin((1 - t) * th) * s0 + math.sin(t * th) * s1) / math.sin(th)
            out.append(cen + w)
    out.append(pts[-1])
    return out


def sweep(g, pts, w, h, r=0.12, up=(0, 0, 1), round_=False, corner=None, seg=8):
    """Teava indoita: sectiune w (lateral) x h (in planul indoirii), de-a lungul traseului pts."""
    P = fillet_path(pts, r, seg)
    n = len(P); T = []
    for i in range(n):
        t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]; T.append(t / np.linalg.norm(t))
    up = np.array(up, float)
    nrm = up - (up @ T[0]) * T[0]
    if np.linalg.norm(nrm) < 1e-3:
        alt = np.array([0, 1.0, 0]); nrm = alt - (alt @ T[0]) * T[0]
    nrm /= np.linalg.norm(nrm)
    if round_: prof = circle(w / 2, 14)
    else: prof = rr(w, h, corner if corner else min(0.3 * min(w, h), 0.022), 4)
    rings = []
    for i in range(n):
        nrm = nrm - (nrm @ T[i]) * T[i]; nrm /= np.linalg.norm(nrm)
        b = np.cross(T[i], nrm)
        rings.append([P[i] + b * u + nrm * v for (u, v) in prof])
    g.loft(rings)
    return P, T


class Kit:
    """Unelte pentru retetele de cadru (coordonate lume, Z in sus, utilizatorul priveste spre +Y)."""
    def __init__(self, name, parts, empties, G, towers, wpos):
        self.name, self.parts, self.empties, self.G, self.towers, self.wpos = name, parts, empties, G, towers, wpos

    @staticmethod
    def _j(joint, sx):
        return joint[0 if sx > 0 else 1] if isinstance(joint, tuple) else joint

    def A(self, n): return self.wpos('anchor_' + n)
    def J(self, n): return self.wpos('joint_' + n)
    def lim(self, n): return list(self.empties['joint_' + n]['limits'])

    def ends(self, i):
        p = self.parts[i]; il = int(np.argmax(p['d'])); ax = p['R'][:, il] * p['d'][il] / 2
        return p['c'] - ax, p['c'] + ax

    def drop(self, *idx):
        for i in idx: self.parts[i]['dropped'] = True

    def drop_frame(self, keep=(), mats=('powder',), joint=None):
        """Scoate toate piesele de cadru (cutii si piese atipice) ale unei articulatii."""
        for i, p in enumerate(self.parts):
            if p['kind'] == 'box' and min(p['d']) < 0.02: continue     # placile subtiri raman
            if p['joint'] == joint and p['mat'] in mats and i not in keep and p['kind'] in ('box', 'other'):
                p['dropped'] = True

    def sweep(self, pts, w=0.10, h=0.05, r=0.12, mat='powder', joint=None, up=(0, 0, 1), round_=False,
              mirror=False, caps=True, corner=None):
        for sx in ((1, -1) if mirror else (1,)):
            pp = [np.array(p, float) * np.array([sx, 1, 1]) for p in pts]
            upv = np.array(up, float) * np.array([sx, 1, 1])
            j = self._j(joint, sx)
            P, T = sweep(self.G(j, mat), pp, w, h, r, upv, round_, corner)
            if caps:
                for q, t in ((P[0], -T[0]), (P[-1], T[-1])):
                    lathe(self.G(j, 'plastic'), q - t * 0.001, t,
                          [(0, min(w, h) * 0.36), (0.003, min(w, h) * 0.34)], 12)

    def tube(self, p0, p1, w=0.08, h=0.05, **kw):
        self.sweep([p0, p1], w, h, r=0, **kw)

    def rod(self, p0, p1, d=0.03, mat='steel', joint=None, mirror=False):
        for sx in ((1, -1) if mirror else (1,)):
            m = np.array([sx, 1, 1])
            cyl(self.G(self._j(joint, sx), mat), np.array(p0, float) * m, np.array(p1, float) * m, d / 2, 14)

    def foot(self, p, size=(0.13, 0.085), mirror=False):
        for sx in ((1, -1) if mirror else (1,)):
            c = np.array([p[0] * sx, p[1], 0.007])
            plate(self.G(None, 'rubber'), c, I3, np.array([size[0], size[1], 0.014]), rc=0.02, ch=0.003)

    def hub(self, p, axis=(1, 0, 0), r=0.045, L=0.07, mat='powder', joint=None, mirror=False):
        """Lagar / butuc de pivot."""
        for sx in ((1, -1) if mirror else (1,)):
            c = np.array(p, float) * np.array([sx, 1, 1]); ax = np.array(axis, float); ax /= np.linalg.norm(ax)
            ax = ax * np.array([sx, 1, 1]); j_ = self._j(joint, sx)
            lathe(self.G(j_, mat), c, ax, [(-L / 2, r * 0.9), (-L / 2 + 0.004, r), (L / 2 - 0.004, r), (L / 2, r * 0.9)], 20)
            for s_ in (-1, 1):
                lathe(self.G(j_, 'plastic'), c + ax * s_ * (L / 2 - 0.001), ax * s_, [(0, r * 0.62), (0.006, r * 0.55)], 16)

    def disc(self, p, axis=(1, 0, 0), r=0.12, t=0.02, mat='plastic', joint=None):
        """Disc / cama."""
        ax = np.array(axis, float); ax /= np.linalg.norm(ax)
        lathe(self.G(joint, mat), np.array(p, float), ax, [(-t / 2, r - 0.004), (-t / 2 + 0.004, r), (t / 2 - 0.004, r), (t / 2, r - 0.004)], 28)

    def block(self, c, d, mat='powder', joint=None, rc=0.012, R=None):
        plate(self.G(joint, mat), np.array(c, float), I3 if R is None else R, np.array(d, float), rc=rc, ch=0.002)

    def knob(self, p, axis=(1, 0, 0), joint=None):
        """Buton galben de reglaj."""
        X = np.array(axis, float); X /= np.linalg.norm(X); k0 = np.array(p, float)
        cyl(self.G(joint, 'steel'), k0 - X * 0.005, k0 + X * 0.02, 0.006, 10)
        lathe(self.G(joint, 'accent'), k0 + X * 0.02, X, [(0, 0.011), (0.004, 0.017), (0.026, 0.017), (0.031, 0.012)], 16)

    def seat_post(self, i=None, base=None, top=None, size=0.07, knob=(1, 0, 0)):
        """Tija telescopica de sezut: manson + tija cromata + buton."""
        if i is not None:
            p = self.parts[i]; self.drop(i)
            base = p['c'] - np.array([0, 0, p['d'][2] / 2]); top = p['c'] + np.array([0, 0, p['d'][2] / 2])
        base = np.array(base, float); top = np.array(top, float); mid = base + (top - base) * 0.6
        self.sweep([base, mid], size, size, r=0, up=(0, 1, 0))
        self.sweep([mid - (top - base) * 0.05, top], size * 0.7, size * 0.7, r=0, mat='steel', up=(0, 1, 0), caps=False, corner=0.008)
        X = np.array(knob, float)
        self.knob(mid - (top - base) / np.linalg.norm(top - base) * 0.045 + X * size / 2, X)

    def tower(self, k=0, top=None, col=(0.055, 0.16), front=True, base=True):
        """Turn de greutati carcasat: doua coloane, panou spate, panou frontal sus, capac, soclu."""
        T = self.towers[k]; S, Wd, Dd = T['S'], T['W'], T['D']
        for p in T.get('ups', []) + T.get('tops', []): p['dropped'] = True
        ztop = top if top else T['ztop']
        hw = T['a'] / 2 + 0.022 + col[0] / 2
        Rc = np.stack([Wd, Dd, np.array([0, 0, 1.0])], axis=1)
        g = self.G(None, 'powder')
        for s_ in (-1, 1):
            c0 = S + Wd * s_ * hw
            sweep(g, [(c0[0], c0[1], 0.02), (c0[0], c0[1], ztop)], col[0], col[1], 0, up=Dd, corner=0.022)
        W_ = 2 * hw + col[0]
        # capac rotunjit
        cc = S.copy(); cc[2] = ztop + 0.03
        tube(g, cc, Rc, np.array([W_ + 0.012, col[1] + 0.012, 0.075]), radius_k=0.4, rmax=0.03)
        if base:
            cb = S.copy(); cb[2] = 0.03
            plate(g, cb, Rc, np.array([W_ + 0.07, col[1] + 0.12, 0.05]), rc=0.03, ch=0.006)
            for s_ in (-1, 1):
                for t_ in (-1, 1):
                    cf = S + Wd * s_ * (W_ / 2 - 0.02) + Dd * t_ * (col[1] / 2 + 0.02); cf[2] = 0.004
                    plate(self.G(None, 'rubber'), cf, Rc, np.array([0.09, 0.06, 0.008]), rc=0.015, ch=0.002)
        Rp = np.stack([Wd, np.array([0, 0, 1.0]), -Dd], axis=1); ww = 2 * hw - col[0] + 0.012
        def panel(z0, z1, side, mat='shroud'):
            c = S + Dd * side * (col[1] / 2 - 0.012); c[2] = (z0 + z1) / 2
            plate(self.G(None, mat), c, Rp, np.array([ww, z1 - z0, 0.004]), rc=0.004, ch=0.001)
            return c
        panel(0.05, ztop, -1)
        lim = max(abs(x) for x in self.empties[T['joint']]['limits'])
        zt = max(p['c'][2] for p in T['plates']) + lim + 0.22
        T['zwin'] = zt
        if front and ztop - zt > 0.12:
            c = panel(zt, ztop, +1); h = ztop - zt
            if h > 0.26:
                pc = c + Dd * 0.0028; pw = min(ww * 0.6, 0.15); ph = min(h * 0.5, 0.20)
                u = Wd * pw / 2; v = np.array([0, 0, ph / 2])
                self.G(None, 'label').quad([pc + u - v, pc - u - v, pc - u + v, pc + u + v])
                ac = pc + np.array([0, 0, ph / 2 + 0.028]); v2 = np.array([0, 0, 0.007])
                self.G(None, 'accent').quad([ac + u - v2, ac - u - v2, ac - u + v2, ac + u + v2])
        return dict(hw=hw + col[0] / 2, hd=col[1] / 2, top=ztop + 0.0675)


# ---------------------------------------------------------------- analiza pieselor
def box_frame(faces):
    """Axele unei cutii din normalele fetelor (ponderate cu aria)."""
    dirs = []
    for f in faces:
        n = np.array(f.normal); a = f.calc_area()
        for d in dirs:
            dot = d[0] @ n
            if abs(dot) > 0.995:
                d[1] += a; break
        else:
            dirs.append([n, a])
    dirs.sort(key=lambda x: -x[1])
    n1 = dirs[0][0]
    n2 = None
    for d in dirs[1:]:
        if abs(d[0] @ n1) < 0.05: n2 = d[0]; break
    if n2 is None: return None
    n2 = n2 - (n2 @ n1) * n1; n2 /= np.linalg.norm(n2)
    R = np.stack([n1, n2, np.cross(n1, n2)], axis=1)
    # aliniaza cu axele lumii cand se poate
    for i in range(3):
        j = int(np.argmax(np.abs(R[:, i])))
        if abs(R[j, i]) > 0.9999:
            R[:, i] = 0; R[j, i] = 1
    out = np.zeros((3, 3)); used = []
    # ordoneaza coloanele ca fiecare sa fie cat mai aproape de axa lumii cu acelasi indice
    order = [None] * 3
    cols = list(range(3))
    for w in range(3):
        best = max(cols, key=lambda i: abs(R[w, i])); cols.remove(best); order[w] = best
    R = R[:, order]
    for i in range(3):
        if R[i, i] < 0: R[:, i] *= -1
    if np.linalg.det(R) < 0: R[:, 2] *= -1
    return R


def analyze(obj):
    off = np.array(obj.matrix_world.translation)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.normal_update(); bm.verts.ensure_lookup_table()
    seen = set(); parts = []
    for v in bm.verts:
        if v.index in seen: continue
        st = [v]; comp = []; seen.add(v.index)
        while st:
            x = st.pop(); comp.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen: seen.add(y.index); st.append(y)
        faces = list({f for x in comp for f in x.link_faces})
        P = np.array([x.co for x in comp]) + off
        mv = abs(sum(f.calc_center_median().dot(f.normal) * f.calc_area() for f in faces) / 3)
        kind = 'other'; R = I3; c = P.mean(0); d = P.max(0) - P.min(0)
        Rb = box_frame(faces)
        if Rb is not None:
            q = P @ Rb; mn = q.min(0); mx = q.max(0)
            if mv / np.prod(mx - mn + 1e-9) > 0.90:
                kind = 'box'; R = Rb; d = mx - mn; c = Rb @ ((mn + mx) / 2)
        if kind == 'other':
            Q = P - P.mean(0); w, vec = np.linalg.eigh(np.cov(Q.T) + 1e-12 * I3)
            # axa cilindrului = vectorul propriu cu valoarea proprie distincta
            ia = 0 if abs(w[1] - w[2]) < abs(w[0] - w[1]) else 2
            ax = vec[:, ia]
            for j in range(3):
                if abs(ax[j]) > 0.9999: ax = np.zeros(3); ax[j] = 1.0
            z = Q @ ax; rad = np.linalg.norm(Q - np.outer(z, ax), axis=1)
            L = z.max() - z.min(); r = rad.max()
            if L > 1e-4 and 0.90 < mv / (math.pi * r * r * L) <= 1.02 and len(comp) >= 30:
                kind = 'cyl'; c = P.mean(0) + ax * (z.max() + z.min()) / 2
                R = ax; d = np.array([r, L, 0])
        parts.append(dict(obj=obj, mat=obj.data.materials[0].name, kind=kind, c=c, R=R, d=d,
                          verts=comp, nv=len(comp), joint=obj.parent.name if obj.parent else None))
    return bm, parts


# ---------------------------------------------------------------- reconstructie
def upgrade(name, do_render=False, dump=False, preview=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, 'glb_src', name + '.glb'))
    objs = [o for o in bpy.data.objects if o.type == 'MESH']
    empties = {o.name: o for o in bpy.data.objects if o.type == 'EMPTY'}
    for o in bpy.data.objects:
        assert np.allclose(np.array(o.matrix_world.to_3x3()), I3, atol=1e-5), o.name
    wpos = lambda n: np.array(empties[n].matrix_world.translation)

    bms = {}; parts = []
    for o in objs:
        bm, ps = analyze(o); bms[o.name] = bm; parts += ps

    import machine_recipes
    recipe = machine_recipes.RECIPES.get(name)
    geo = {}      # (joint, material) -> Geo
    def G(joint, mat):
        return geo.setdefault((joint, mat), Geo())
    def drop(p):
        p['dropped'] = True

    static = [p for p in parts if p['joint'] is None]
    if dump:
        for n_, e_ in sorted(empties.items()):
            print('E %-22s %s %s' % (n_, np.round(wpos(n_), 3), dict(kind=e_.get('kind'), lim=list(e_['limits'])) if 'kind' in e_.keys() else ''))
        for i, p in enumerate(parts):
            d = p['d']; il = int(np.argmax(d)); ex = ''
            if p['kind'] == 'box':
                ax = p['R'][:, il] * d[il] / 2; ex = 'ends %s %s' % (np.round(p['c'] - ax, 3), np.round(p['c'] + ax, 3))
            elif p['kind'] == 'cyl': ex = 'axis %s' % np.round(p['R'], 2)
            else:
                P_ = np.array([v.co for v in p['verts']]) + np.array(p['obj'].matrix_world.translation)
                ex = 'bbox %s %s' % (np.round(P_.min(0), 3), np.round(P_.max(0), 3))
            print('P%-3d %-10s %-7s %-5s nv=%-4d c=%s d=%s %s' % (i, p['joint'] or '-', p['mat'], p['kind'], p['nv'], np.round(p['c'], 3), np.round(d, 3), ex))
        return
    allc = np.array([p['c'] for p in parts]); centroid = allc.mean(0)

    # --- turnuri de greutati -------------------------------------------------
    stack_joints = [n for n in empties if n.startswith('joint_stack')]
    has_carriage = any(n.startswith('joint_carriage') for n in empties)
    stack_iron = [p for p in parts if p['mat'] == 'iron' and p['kind'] == 'box' and 0.015 < min(p['d']) < 0.04
                  and max(p['d']) < 0.45]
    towers = []
    for sj in stack_joints:
        S = wpos(sj)
        mine = [p for p in stack_iron if np.linalg.norm((p['c'] - S)[:2]) < 0.08]
        if not mine: continue
        p0 = mine[0]; iw_ = int(np.argmax(p0['d'][:2]))       # axa lata a placii (in plan)
        Wd = p0['R'][:, iw_].copy(); Wd[2] = 0; Wd /= np.linalg.norm(Wd)
        Dd = np.array([-Wd[1], Wd[0], 0.0])
        mine_ids = {id(p) for p in mine}
        others = [p['c'] for p in parts if id(p) not in mine_ids and np.linalg.norm((p['c'] - S)[:2]) > 0.25]
        oc = np.mean(others, axis=0) if others else centroid
        if (oc - S) @ Dd < 0: Dd = -Dd                         # Dd arata spre utilizator
        towers.append(dict(joint=sj, S=S, W=Wd, D=Dd, plates=mine, a=max(p0['d'][:2]), b=min(p0['d'][:2])))

    for T in towers:
        S, Wd, Dd = T['S'], T['W'], T['D']
        for p in T['plates']:
            drop(p)
            g = G(p['joint'], 'iron'); plate(g, p['c'], p['R'], p['d'], rc=0.007, ch=0.002)
            gl = G(p['joint'], 'label')
            for s in (1, -1):   # eticheta pe ambele fete late
                cc = p['c'] + Dd * s * (T['b'] / 2 + 0.0006) + Wd * s * (T['a'] / 2 - 0.035)
                u = Wd * 0.016 * s; v = np.array([0, 0, 0.007])
                gl.quad([cc - u - v, cc + u - v, cc + u + v, cc - u + v] if s > 0 else
                        [cc - u - v, cc + u - v, cc + u + v, cc - u + v])
        # cui selector pe placa de jos a pachetului mobil
        mov = [p for p in T['plates'] if p['joint'] == T['joint']]
        if mov:
            low = min(mov, key=lambda p: p['c'][2])
            f0 = low['c'] + Dd * (T['b'] / 2)
            cyl(G(T['joint'], 'steel'), f0 - Dd * 0.01, f0 + Dd * 0.022, 0.0045, 10)
            lathe(G(T['joint'], 'accent'), f0 + Dd * 0.022, Dd,
                  [(0, 0.008), (0.003, 0.012), (0.024, 0.012), (0.028, 0.009)], 14)
        # carcasa: montantii verticali de langa greutati
        ups = [p for p in static if p['mat'] == 'powder' and p['kind'] == 'box'
               and int(np.argmax(p['d'])) == 2 and abs(p['R'][2, 2]) > 0.99 and p['d'][2] > 0.9
               and abs((p['c'] - S) @ Wd) < 0.36 and abs((p['c'] - S) @ Dd) < 0.12]
        T['ups'] = ups
        T['ztop'] = max([p['c'][2] + p['d'][2] / 2 for p in ups], default=1.8)
        T['tops'] = [p for p in static if p['mat'] == 'powder' and p['kind'] == 'box' and abs(p['c'][2] - T['ztop']) < 0.12
                     and np.linalg.norm((p['c'] - S)[:2]) < 0.12 and p['d'][2] < 0.12]
        if len(ups) >= 2 and not has_carriage and recipe is None:
            def ext(p, ax):
                return sum(abs(p['R'][:, i] @ ax) * p['d'][i] for i in range(3)) / 2
            wmin = min((p['c'] - S) @ Wd - ext(p, Wd) for p in ups); wmax = max((p['c'] - S) @ Wd + ext(p, Wd) for p in ups)
            dh = max(abs((p['c'] - S) @ Dd) + ext(p, Dd) for p in ups)
            ztop = max(p['c'][2] + p['d'][2] / 2 for p in ups)
            zbot = min(p['c'][2] for p in T['plates']) - 0.03
            lim = max(abs(x) for x in empties[T['joint']]['limits'])
            ztravel = max(p['c'][2] for p in T['plates']) + lim + 0.20
            wc = (wmin + wmax) / 2; ww = wmax - wmin - 0.012
            Rp = np.stack([Wd, np.array([0, 0, 1.0]), -Dd], axis=1)   # u=lat, v=sus, w=grosime
            def panel(z0, z1, side, mat='shroud'):
                cc = S + Wd * wc + Dd * side * (dh + 0.003); cc[2] = (z0 + z1) / 2
                plate(G(None, mat), cc, Rp, np.array([ww, z1 - z0, 0.005]), rc=0.012, ch=0.001)
                return cc
            panel(zbot, ztop - 0.004, -1)
            if ztop - ztravel > 0.18:
                cc = panel(ztravel, ztop - 0.004, +1)
                h = ztop - ztravel
                if h > 0.34:   # placuta cu instructiuni
                    pc = cc + Dd * 0.0034; pw = min(ww * 0.55, 0.15); ph = min(h * 0.45, 0.20)
                    u = Wd * pw / 2; v = np.array([0, 0, ph / 2])
                    G(None, 'label').quad([pc + u - v, pc - u - v, pc - u + v, pc + u + v])
                    ac = pc + np.array([0, 0, ph / 2 + 0.03]); v2 = np.array([0, 0, 0.008])
                    G(None, 'accent').quad([ac + u - v2, ac - u - v2, ac - u + v2, ac + u + v2])


    # --- reteta de cadru scrisa de mana (daca exista) ----------------------------
    if recipe is not None:
        recipe(Kit(name, parts, empties, G, towers, wpos))

    # --- tija sezutului cu buton de reglaj ------------------------------------
    seat_posts = []
    for an in [n for n in empties if n.startswith('anchor_seat') and recipe is None]:
        if empties[an].parent is not None: continue
        A = wpos(an)
        for p in static:
            if p.get('dropped') or p['mat'] != 'powder' or p['kind'] != 'box': continue
            if any(p is q for q in seat_posts): continue
            if int(np.argmax(p['d'])) != 2 or abs(p['R'][2, 2]) < 0.99: continue
            top = p['c'][2] + p['d'][2] / 2
            if np.linalg.norm((p['c'] - A)[:2]) < 0.07 and 0 < A[2] - top < 0.16 and p['d'][2] > 0.2:
                seat_posts.append(p)
    for p in seat_posts:
        drop(p)
        c, R, d = p['c'], p['R'], p['d']
        hs = d[2] * 0.62
        cs = c.copy(); cs[2] = c[2] - d[2] / 2 + hs / 2
        iu, iv, iw, r = tube(G(None, 'powder'), cs, R, np.array([d[0], d[1], hs]))
        tube_caps(G(None, 'plastic'), cs, R, np.array([d[0], d[1], hs]), iu, iv, iw, r)
        ci = c.copy(); ci[2] = c[2] + hs / 2
        tube(G(None, 'steel'), ci, R, np.array([d[0] * 0.72, d[1] * 0.72, d[2] - hs + 0.01]), rmax=0.012)
        k0 = cs + np.array([d[0] / 2, 0, hs / 2 - 0.045]); X = np.array([1.0, 0, 0])
        cyl(G(None, 'steel'), k0 - X * 0.005, k0 + X * 0.02, 0.006, 10)
        lathe(G(None, 'steel'), k0, X, [(0, 0.013), (0.008, 0.013)], 14)
        lathe(G(None, 'accent'), k0 + X * 0.02, X, [(0, 0.011), (0.004, 0.017), (0.026, 0.017), (0.031, 0.012)], 16)

    # --- restul pieselor ------------------------------------------------------
    backing = [p for p in parts if p['mat'] == 'plastic' and p['kind'] == 'box' and min(p['d']) < 0.02]
    for p in parts:
        if p.get('dropped'): continue
        mat, kind, c, R, d, j = p['mat'], p['kind'], p['c'], p['R'], p['d'], p['joint']
        if kind == 'box':
            dm = float(min(d)); ds = sorted(d)
            if mat == 'vinyl':
                n = R[:, int(np.argmin(d))]; up = None; best = 0.12
                for b in backing:
                    if b['joint'] != j: continue
                    dv = c - b['c']; dist = np.linalg.norm(dv)
                    if abs(dv @ n) > 0.6 * dist and dist < best:
                        best = dist; up = 1 if dv @ n > 0 else -1
                if up is None and ds[0] > 0.6 * ds[1]:
                    tube(G(j, 'vinyl'), c, R, d, radius_k=0.3, rmax=0.03, seg=5)   # bloc gros, nu perna plata
                else:
                    cushion(G(j, 'vinyl'), c, R, d, up)
                drop(p)
            elif mat == 'powder':
                if dm < 0.016:
                    plate(G(j, 'powder'), c, R, d, rc=min(0.012, ds[1] * 0.2))
                elif ds[1] > 0.6 * ds[2] and ds[2] < 0.2:
                    tube(G(j, 'powder'), c, R, d, radius_k=0.2, rmax=0.01)
                else:
                    # profile mai groase, ca la aparatele comerciale; talpa ramane pe podea
                    d = d.copy(); c = c.copy(); il = int(np.argmax(d))
                    for i in range(3):
                        if i == il or d[i] > 0.13: continue
                        grow = min(d[i] * 0.22, 0.016); zc = abs(R[2, i])
                        lowz = c[2] - sum(abs(R[2, k]) * d[k] for k in range(3)) / 2
                        d[i] += grow
                        if zc > 0.9 and lowz < 0.05 and j is None: c[2] += grow / 2
                    iu, iv, iw, r = tube(G(j, 'powder'), c, R, d)
                    tube_caps(G(j, 'plastic'), c, R, d, iu, iv, iw, r)
                drop(p)
            elif mat == 'plastic' and dm < 0.02 and ds[1] > 0.1:
                plate(G(j, 'plastic'), c, R, d, rc=min(0.3 * ds[1], 0.07) - 0.004, ch=0.002); drop(p)
            elif mat == 'rubber' and ds[2] < 0.3:
                if dm < 0.02: plate(G(j, 'rubber'), c, R, d, rc=min(0.012, ds[1] * 0.3), ch=0.003)
                else: tube(G(j, 'rubber'), c, R, d, radius_k=0.25, rmax=0.012)
                drop(p)
        elif kind == 'cyl':
            ax = R; r, L = d[0], d[1]
            if mat == 'vinyl' and r > 0.03:      # rola de burete
                e = min(0.018, r * 0.35)
                prof = [(-L / 2, r * 0.5), (-L / 2 + 0.003, r - e), (-L / 2 + e * 0.45, r - e * 0.3), (-L / 2 + e, r),
                        (L / 2 - e, r), (L / 2 - e * 0.45, r - e * 0.3), (L / 2 - 0.003, r - e), (L / 2, r * 0.5)]
                lathe(G(j, 'vinyl'), c, ax, prof, 24)
                for s in (-1, 1):
                    lathe(G(j, 'plastic'), c + ax * s * (L / 2 - 0.001), ax * s, [(0, r * 0.52), (0.005, r * 0.48)], 20)
                drop(p)
            elif mat == 'rubber' and 0.012 < r < 0.03 and L > 0.07:   # manson de prindere
                f = 0.004
                prof = [(-L / 2, r + f), (-L / 2 + 0.008, r + f), (-L / 2 + 0.011, r + 0.0008), (0, r + 0.0018),
                        (L / 2 - 0.011, r + 0.0008), (L / 2 - 0.008, r + f), (L / 2, r + f)]
                lathe(G(j, 'rubber'), c, ax, prof, 16); drop(p)

    # --- capace pe axele pivotilor ---------------------------------------------
    for jn, je in empties.items():
        if not jn.startswith('joint_') or je.get('kind') != 'rotary': continue
        P = wpos(jn); ag = np.array(je['axis_gltf']); ax = np.array([ag[0], -ag[2], ag[1]]); ax /= np.linalg.norm(ax)
        for p in parts:
            if p['kind'] != 'cyl' or p['mat'] != 'steel': continue
            if abs(p['R'] @ ax) < 0.995: continue
            dv = P - p['c']; perp = dv - (dv @ p['R']) * p['R']
            if np.linalg.norm(perp) > 0.02: continue
            r, L = p['d'][0], p['d'][1]
            for s in (-1, 1):
                a_ = p['R'] * s
                lathe(G(p['joint'], 'plastic'), p['c'] + a_ * (L / 2 - 0.004), a_,
                      [(0, r * 1.55), (0.010, r * 1.55), (0.016, r * 1.2)], 18)
            break

    # --- materiale ------------------------------------------------------------
    def material(mn):
        m = bpy.data.materials.get(mn)
        if m is None:
            m = bpy.data.materials.new(mn); m.use_nodes = True
        m.use_backface_culling = False
        if mn in MATS:
            col, met, rough = MATS[mn]
            b = m.node_tree.nodes['Principled BSDF']
            b.inputs['Base Color'].default_value = col; b.inputs['Metallic'].default_value = met
            b.inputs['Roughness'].default_value = rough
        return m
    for mn in MATS:
        if bpy.data.materials.get(mn): material(mn)

    # --- scrie mesh-urile -----------------------------------------------------
    by_key = {}
    for o in objs:
        by_key[(o.parent.name if o.parent else None, o.data.materials[0].name)] = o
        bm = bms[o.name]
        dead = [v for p in parts if p['obj'] is o and p.get('dropped') for v in p['verts']]
        bmesh.ops.delete(bm, geom=dead, context='VERTS')
    for key in list(geo) + [k for k in by_key if k not in geo]:
        j, mn = key
        o = by_key.get(key)
        if o is None:
            me = bpy.data.meshes.new(name + '_' + mn)
            o = bpy.data.objects.new(f"{name}__{j[6:] + '__' if j else ''}{mn}", me)
            bpy.context.scene.collection.objects.link(o)
            if j: o.parent = empties[j]
            me.materials.append(material(mn)); bm = bmesh.new(); by_key[key] = o
        else:
            bm = bms[o.name]
        g = geo.get(key)
        if g and g.v:
            off = np.array(empties[j].matrix_world.translation) if j else np.zeros(3)
            tmp = bpy.data.meshes.new('_tmp')
            tmp.from_pydata([tuple(np.array(v) - off) for v in g.v], [], g.f)
            bm.from_mesh(tmp); bpy.data.meshes.remove(tmp)
        if len(bm.verts) == 0:
            bpy.data.objects.remove(o); continue
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces: f.smooth = True
        me = o.data; me.clear_geometry(); bm.to_mesh(me); bm.free()
        me.set_sharp_from_angle(angle=math.radians(38))
        me.update()

    # --- export ---------------------------------------------------------------
    out = os.path.join(ROOT, 'glb', name + '.glb')
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_extras=True, export_yup=True,
                              export_animations=False, export_texcoords=False, export_apply=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'blend', name + '.blend'))
    mn_ = np.array([1e9] * 3); mx_ = -mn_; tris = 0
    for o in bpy.data.objects:
        if o.type != 'MESH': continue
        for v in o.data.vertices:
            w = np.array(o.matrix_world @ v.co); mn_ = np.minimum(mn_, w); mx_ = np.maximum(mx_, w)
        tris += sum(len(pl.vertices) - 2 for pl in o.data.polygons)
    info = dict(name=name, size_mm=[round(float(x) * 1000, 1) for x in (mx_ - mn_)], tris=tris,
                glb_kb=round(os.path.getsize(out) / 1024, 1))
    print('@@INFO ' + json.dumps(info))

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import render_lib
    def pose_end():
        for jn, je in empties.items():
            if not jn.startswith('joint_') or 'adjust' in jn or 'kind' not in je.keys(): continue
            lim = list(je['limits']); val = lim[1] if abs(lim[1]) >= abs(lim[0]) else lim[0]
            ag = np.array(je['axis_gltf']); ax = Vector((ag[0], -ag[2], ag[1]))
            if je['kind'] == 'linear': je.location = je.location + ax * val
            elif je['kind'] == 'rotary':
                if abs(val) >= 360: val = 90
                je.rotation_mode = 'QUATERNION'
                je.rotation_quaternion = Matrix.Rotation(math.radians(val), 4, ax).to_quaternion()
    if preview:
        pv = os.environ.get('PREVIEW_DIR', '/tmp')
        render_lib.setup(res=520, samples=20, az=-38)
        render_lib.render(os.path.join(pv, name + '_a.png'))
        render_lib.set_view(az=145, el=18); render_lib.render(os.path.join(pv, name + '_b.png'))
        render_lib.set_view(az=-90, el=6); render_lib.render(os.path.join(pv, name + '_c.png'))
        pose_end(); render_lib.set_view(az=-38, el=22); render_lib.render(os.path.join(pv, name + '_d.png'))
    if do_render:
        render_lib.setup(res=640, samples=48)
        render_lib.render(os.path.join(ROOT, 'renders', name + '.png'))
        pose_end()
        bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = 448
        render_lib.render(os.path.join(ROOT, 'renders_max', name + '.png'))


if __name__ == '__main__':
    args = sys.argv[1:]
    upgrade(args[0], '--render' in args, '--dump' in args, '--preview' in args)
