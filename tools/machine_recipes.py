"""Retete de cadru, cate una pe aparat. Fiecare primeste un Kit (vezi upgrade_machines.py)."""
import numpy as np

RECIPES = {}

def recipe(fn):
    RECIPES[fn.__name__] = fn
    return fn


def drop_feet(K):
    """Scoate talpile de cauciuc vechi (cutii subtiri la podea)."""
    for p in K.parts:
        if p['joint'] is None and p['mat'] == 'rubber' and p['kind'] == 'box' and p['c'][2] < 0.02:
            p['dropped'] = True


def sled_sides(K, X, y_front, y_rear, w=0.05, h=0.09):
    """Talpi laterale pe podea, cu picioare de cauciuc."""
    K.foot((X, y_front - 0.06, 0), mirror=True); K.foot((X, y_rear + 0.06, 0), mirror=True)


def load_stub(K, arm_pts, joint='joint_arms'):
    """Leaga cornul de discuri (anchor_load_*) de cel mai apropiat punct al bratului."""
    if 'anchor_load_L' not in K.empties: return
    L = K.A('load_L'); xa = arm_pts[0][0]; q = np.array([xa, L[1], L[2]]); best = None
    for a, b in zip(arm_pts[:-1], arm_pts[1:]):
        a = np.array(a, float); b = np.array(b, float); t = np.clip((q - a) @ (b - a) / ((b - a) @ (b - a)), 0, 1)
        c = a + t * (b - a)
        if best is None or np.linalg.norm(c - q) < np.linalg.norm(best - q): best = c
    if np.linalg.norm(best - q) > 0.03:
        K.tube(tuple(best), tuple(q), w=0.045, h=0.06, joint=joint, mirror=True)
    K.hub(tuple(q), r=0.04, L=0.06, joint=joint, mirror=True)


ZF = 0.059   # axa talpilor de podea (teava 90 mm pe picioare de cauciuc)


def press_frame(K, X, side_pts, side_r, yc, back, arm_pts, xa, handle_z, tower_link_z=None, stack=True):
    """Familia de prese cu sezut: talpi laterale indoite pana la pivot, traverse, tija sezut, stalp spatar, brate."""
    K.drop_frame(); K.drop_frame(joint='joint_arms'); drop_feet(K)
    yt = None
    if stack:
        K.tower(); yt = K.towers[0]['S'][1]
    piv = K.J('arms')
    K.sweep(side_pts, w=0.05, h=0.09, r=side_r, mirror=True)
    K.hub((X, piv[1], piv[2]), r=0.052, L=0.075, mirror=True)
    yf = side_pts[0][1]
    K.foot((X, yf - 0.07, 0), mirror=True); K.foot((X, side_pts[1][1] + 0.07, 0), mirror=True)
    K.tube((-X, 0.0, 0.05), (X, 0.0, 0.05), w=0.09, h=0.06)         # traversa sub sezut
    K.tube((-X, yc, 0.05), (X, yc, 0.05), w=0.09, h=0.06)           # traversa spate
    if stack and abs(yc - yt) > 0.2:
        K.tube((0, yc, 0.05), (0, yt + 0.12, 0.05), w=0.10, h=0.06)
    if tower_link_z:
        yl = side_pts[2][1]
        K.tube((-X, yl, tower_link_z), (X, yl, tower_link_z), w=0.07, h=0.05)
        if stack and abs(yl - yt) > 0.12:
            K.tube((0.14, yl, tower_link_z), (0.14, yt + 0.06, tower_link_z), w=0.05, h=0.05, mirror=True)
    K.seat_post(base=(0, 0, 0.07), top=(0, 0, 0.46))
    lo, hi = back
    K.sweep([(0, yc, 0.07), lo, hi], w=0.06, h=0.07, r=0.25)
    K.block(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2 + 0.03, lo[2] + (hi[2] - lo[2]) * 0.72), (0.16, 0.05, 0.10))
    # brate
    g = K.A('grip_L'); gx = abs(g[0])
    K.sweep(arm_pts, w=0.045, h=0.075, r=0.16, joint='joint_arms', mirror=True)
    K.hub((xa, piv[1], piv[2]), r=0.045, L=0.05, joint='joint_arms', mirror=True)
    load_stub(K, arm_pts)
    if not stack:      # coarne de depozitare a discurilor pe cadru
        ys = side_pts[1][1] if len(side_pts) > 2 else yc
        for z in (0.42, 0.74):
            K.rod((X, ys, z), (X + 0.21, ys, z), d=0.05, mirror=True)
            K.hub((X + 0.035, ys, z), r=0.04, L=0.02, mat='steel', mirror=True)
    e = arm_pts[-1]
    K.sweep([e, (gx, e[1], e[2]), (gx, g[1], g[2] - 0.075 if handle_z > g[2] else g[2] + 0.075)], w=0.032, h=0.032,
            r=0.045, round_=True, mat='steel', joint='joint_arms', mirror=True)


@recipe
def machine_chest_press(K):
    # Ref: BodyKore GR601, Precor Vitality, Muscle D Classic V2 (prese de piept cu selector).
    piv = K.J('arms'); g = K.A('grip_L'); X = 0.37; yr = -0.40; xa = 0.335
    press_frame(K, X, [(X, 0.46, ZF), (X, yr, ZF), (X, yr, 1.52), (X, piv[1], piv[2])], [0, 0.16, 0.32, 0],
                yc=yr, back=((0, -0.305, 0.50), (0, -0.317, 1.20)),
                arm_pts=[(xa, piv[1], piv[2]), (xa, piv[1] + 0.03, 1.24), (xa, g[1], 1.16)], xa=xa, handle_z=1.16,
                tower_link_z=1.42)


@recipe
def machine_incline_press(K):
    # Ref: Hammer Strength Iso-Lateral Incline, Life Fitness Insignia: pivot sus-spate, brate peste umeri.
    piv = K.J('arms'); g = K.A('grip_L'); X = 0.33; xa = 0.295
    press_frame(K, X, [(X, 0.46, ZF), (X, piv[1], ZF), (X, piv[1], piv[2])], [0, 0.16, 0],
                yc=-0.56, back=((0, -0.465, 0.45), (0, -0.535, 1.16)),
                arm_pts=[(xa, piv[1], piv[2]), (xa, 0.02, 1.66), (xa, g[1], 1.37)], xa=xa, handle_z=1.37)


@recipe
def machine_shoulder_press(K):
    # Ref: Life Fitness Insignia / MTS Shoulder Press: turn in spate, brate care vin din spate pe langa umeri.
    piv = K.J('arms'); g = K.A('grip_L'); X = 0.37; xa = 0.335
    press_frame(K, X, [(X, 0.46, ZF), (X, piv[1], ZF), (X, piv[1], piv[2])], [0, 0.16, 0],
                yc=-0.42, back=((0, -0.27, 0.45), (0, -0.325, 1.18)),
                arm_pts=[(xa, piv[1], piv[2]), (xa, -0.30, 1.10), (xa, g[1], 1.43)], xa=xa, handle_z=1.43)


@recipe
def plate_chest_press(K):
    # Ref: Hammer Strength Iso-Lateral Bench Press (cadru lat sudat, coarne de discuri pe brate si pe cadru).
    piv = K.J('arms'); g = K.A('grip_L'); X = 0.37; yr = -0.40; xa = 0.335
    press_frame(K, X, [(X, 0.46, ZF), (X, yr, ZF), (X, yr, 1.52), (X, piv[1], piv[2])], [0, 0.16, 0.32, 0],
                yc=yr, back=((0, -0.305, 0.50), (0, -0.317, 1.20)),
                arm_pts=[(xa, piv[1], piv[2]), (xa, piv[1] + 0.03, 1.24), (xa, g[1], 1.16)], xa=xa, handle_z=1.16,
                tower_link_z=1.42, stack=False)


@recipe
def plate_incline_press(K):
    # Ref: Hammer Strength Iso-Lateral Incline Press.
    piv = K.J('arms'); g = K.A('grip_L'); X = 0.33; xa = 0.295
    press_frame(K, X, [(X, 0.46, ZF), (X, piv[1], ZF), (X, piv[1], piv[2])], [0, 0.16, 0],
                yc=-0.56, back=((0, -0.465, 0.45), (0, -0.535, 1.16)),
                arm_pts=[(xa, piv[1], piv[2]), (xa, 0.02, 1.66), (xa, g[1], 1.37)], xa=xa, handle_z=1.37, stack=False)
    K.tube((-X, piv[1], 1.2), (X, piv[1], 1.2), w=0.07, h=0.05)


@recipe
def plate_shoulder_press(K):
    # Ref: Hammer Strength Iso-Lateral Shoulder Press.
    piv = K.J('arms'); g = K.A('grip_L'); X = 0.37; xa = 0.335
    press_frame(K, X, [(X, 0.46, ZF), (X, piv[1], ZF), (X, piv[1], piv[2])], [0, 0.16, 0],
                yc=-0.42, back=((0, -0.27, 0.45), (0, -0.325, 1.18)),
                arm_pts=[(xa, piv[1], piv[2]), (xa, -0.30, 1.10), (xa, g[1], 1.43)], xa=xa, handle_z=1.43, stack=False)
    K.tube((-X, piv[1], 0.6), (X, piv[1], 0.6), w=0.07, h=0.05)


def row_frame(K, stack):
    """Ramat din sezut cu sprijin pe piept: utilizatorul priveste spre pivotul din fata."""
    K.drop_frame(); K.drop_frame(joint='joint_arms'); drop_feet(K)
    piv = K.J('arms'); g = K.A('grip_L'); gx = abs(g[0]); seat = K.A('seat'); yp = piv[1]
    if stack:
        t = K.tower(); xh = t['hw'] + 0.04; xa = xh + 0.005
        K.tube((0, -0.62, 0.05), (0, yp - 0.12, 0.05), w=0.11, h=0.06)                   # coloana centrala
        K.tube((-0.33, -0.62, 0.05), (0.33, -0.62, 0.05), w=0.09, h=0.06)               # talpa spate
        K.foot((0.29, -0.62, 0), mirror=True)
        K.block((xh - 0.03, yp, piv[2]), (0.06, 0.09, 0.11)); K.block((-xh + 0.03, yp, piv[2]), (0.06, 0.09, 0.11))
    else:
        X = 0.33; xh = 0.2; xa = 0.245
        K.sweep([(X, -0.66, ZF), (X, yp, ZF), (X, yp, 1.05), (xh - 0.045, yp, piv[2])], w=0.05, h=0.09,
                r=[0, 0.16, 0.30, 0], mirror=True)
        K.foot((X, -0.60, 0), mirror=True); K.foot((X, yp - 0.08, 0), mirror=True)
        K.tube((-X, seat[1], 0.05), (X, seat[1], 0.05), w=0.09, h=0.06)
        K.tube((-X, 0.42, 0.05), (X, 0.42, 0.05), w=0.09, h=0.06)
        K.tube((-X, yp, 0.62), (X, yp, 0.62), w=0.07, h=0.05)
        K.tube((-xh, yp, piv[2] - 0.16), (xh, yp, piv[2] - 0.16), w=0.06, h=0.05)
        for z in (0.36,):
            K.rod((X, yp, z), (X + 0.21, yp, z), d=0.05, mirror=True)
    K.hub((xh, yp, piv[2]), r=0.05, L=0.07, mirror=True)
    K.seat_post(base=(0, seat[1], 0.07), top=(0, seat[1], 0.46))
    # stalp pentru perna de piept, cu reglaj
    K.sweep([(0, 0.44, 0.07), (0, 0.40, 0.55), (0, 0.375, 0.99)], w=0.06, h=0.07, r=0.3)
    K.knob((0.03, 0.39, 0.72))
    arm = [(xa + 0.04, yp, piv[2]), (xa + 0.04, yp, 1.30), (xa + 0.04, g[1], 1.17)]
    K.sweep(arm, w=0.045, h=0.07, r=0.12, joint='joint_arms', mirror=True)
    K.hub((xa + 0.04, yp, piv[2]), r=0.045, L=0.05, joint='joint_arms', mirror=True)
    load_stub(K, arm)
    e = arm[-1]
    K.sweep([e, (e[0], g[1], 1.12), (gx, g[1], 1.10), (gx, g[1], g[2] - 0.075)], w=0.032, h=0.032, r=0.04,
            round_=True, mat='steel', joint='joint_arms', mirror=True)


@recipe
def machine_seated_row(K):
    # Ref: Life Fitness Insignia Row, Precor Vitality Row: turn in fata, perna de piept, brate atarnate de pivot.
    row_frame(K, True)


@recipe
def plate_row(K):
    # Ref: Hammer Strength Iso-Lateral Row.
    row_frame(K, False)


def spine_base(K, yfront=0.62, seat=True, tower=True):
    """Baza cu coloana centrala: turn in spate, talpa transversala in fata, tija de sezut."""
    K.drop_frame(); drop_feet(K)
    yt = -0.6
    if tower:
        K.tower(); yt = K.towers[0]['S'][1]
    K.tube((0, yt + 0.12, 0.05), (0, yfront, 0.05), w=0.11, h=0.06)
    K.tube((-0.30, yfront, 0.05), (0.30, yfront, 0.05), w=0.09, h=0.06); K.foot((0.26, yfront, 0), mirror=True)
    if seat:
        s = K.A('seat'); K.seat_post(base=(0, s[1], 0.07), top=(0, s[1], 0.46))
    return yt


def lever_arm(K, joint, w=0.04, h=0.06):
    """Inlocuieste tija subtire a parghiei cu un profil."""
    for p in K.parts:
        if p['joint'] == joint and p['mat'] == 'powder' and p['kind'] == 'cyl':
            p['dropped'] = True; ax = p['R'] * p['d'][1] / 2
            K.sweep([p['c'] - ax, p['c'] + ax], w, h, r=0, joint=joint, up=(1, 0, 0))


def side_handles(K, y=-0.02, z=0.46, x=0.22):
    """Manere laterale langa sezut."""
    K.sweep([(x - 0.06, y - 0.06, z - 0.03), (x + 0.05, y - 0.06, z - 0.03), (x + 0.05, y - 0.06, z + 0.10),
             (x + 0.05, y + 0.12, z + 0.10)], w=0.028, h=0.028, r=0.04, round_=True, mat='steel', mirror=True, caps=False)
    K.rod((x + 0.05, y + 0.02, z + 0.10), (x + 0.05, y + 0.13, z + 0.10), d=0.036, mat='rubber', mirror=True)


@recipe
def machine_pec_deck(K):
    # Ref: Skelcore Power Series, Muscle D Classic V2, Gronk: turn in spate, cap cu doi pivoti verticali
    # deasupra capului, brate in L care coboara cu perne si manere.
    yt = spine_base(K, yfront=0.60)
    K.sweep([(0, -0.42, 0.07), (0, -0.284, 0.45), (0, -0.284, 1.10)], w=0.06, h=0.07, r=0.25)
    pl = K.J('arm_R'); zt = K.towers[0]['ztop']
    K.sweep([(0, yt + 0.05, zt - 0.02), (0, pl[1] - 0.02, zt - 0.02)], w=0.12, h=0.07, r=0)          # consola
    K.block((0, pl[1], pl[2] + 0.055), (0.36, 0.16, 0.05), rc=0.05)                                    # placa pivotilor
    J = ('joint_arm_R', 'joint_arm_L'); g = K.A('grip_R')
    K.drop_frame(joint='joint_arm_L'); K.drop_frame(joint='joint_arm_R')
    K.hub((pl[0], pl[1], pl[2] - 0.02), axis=(0, 0, 1), r=0.05, L=0.10, joint=J, mirror=True)
    za = pl[2] - 0.04
    K.sweep([(pl[0], pl[1], za), (0.625, -0.115, za), (0.625, -0.115, 1.21)], w=0.045, h=0.07, r=0.12, joint=J, mirror=True)
    K.sweep([(0.625, -0.115, 1.50), (0.625, g[1], 1.56), (0.62, g[1], g[2] + 0.075)], w=0.03, h=0.03, r=0.03,
            round_=True, mat='steel', joint=J, mirror=True, caps=False)


def leg_seat_machine(K, thigh=False):
    yt = spine_base(K, yfront=0.66)
    piv = K.J('lever'); X = 0.33
    # sina spatarului reglabil + suport
    K.tube((0, -0.54, 0.43), (0, 0.02, 0.43), w=0.06, h=0.05)
    K.sweep([(0, -0.44, 0.07), (0, -0.50, 0.43)], w=0.06, h=0.06, r=0)
    K.knob((0.03, -0.42, 0.43))
    # suportul pivotului: iese lateral din coloana si urca la genunchi
    K.sweep([(0, piv[1], 0.05), (X, piv[1], 0.05), (X, piv[1], piv[2])], w=0.06, h=0.08, r=0.12)
    K.hub((X, piv[1], piv[2]), r=0.055, L=0.075)
    K.foot((X, piv[1], 0))
    K.disc((X - 0.062, piv[1], piv[2]), r=0.13, t=0.022, joint='joint_lever')                  # cama
    K.disc((X - 0.075, piv[1], piv[2]), r=0.05, t=0.02, mat='steel', joint='joint_lever')
    lever_arm(K, 'joint_lever')
    side_handles(K)
    if thigh:   # perna reglabila peste coapse
        K.sweep([(X, piv[1], piv[2]), (X, 0.2, 0.79), (0.06, 0.2, 0.79)], w=0.045, h=0.05, r=0.07)
        K.knob((X + 0.025, 0.24, 0.68))


@recipe
def machine_leg_extension(K):
    # Ref: Life Fitness Axiom, Skelcore Power Series, SFE: sezut inclinat, pivot la genunchi cu cama, rola la glezne.
    leg_seat_machine(K)


@recipe
def machine_leg_curl_seated(K):
    # Ref: Life Fitness Axiom Seated Leg Curl/Extension, elitefts Seated Leg Curl: ca extensia, plus perna peste coapse.
    leg_seat_machine(K, thigh=True)
