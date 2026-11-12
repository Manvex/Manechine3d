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
        s = K.A('seat'); K.seat_post(base=(0, s[1], 0.07), top=(0, s[1], s[2] - 0.075))
    return yt


def lever_arm(K, joint, w=0.04, h=0.06):
    """Inlocuieste tija subtire a parghiei cu un profil."""
    for p in K.parts:
        if p['joint'] == joint and p['mat'] == 'powder' and p['kind'] == 'cyl' and p['d'][1] > 0.2:
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


@recipe
def machine_leg_curl_lying(K):
    # Ref: Skelcore Power Series Prone Leg Curl, Muscle D Classic V2: banca pe cadru-masa cu patru picioare,
    # turn la cap, pivot cu cama la genunchi, manere sub perna de piept.
    K.drop_frame(); drop_feet(K); K.tower(); yt = K.towers[0]['S'][1]
    piv = K.J('lever'); X = 0.2; y0 = -0.60; y1 = piv[1]
    K.sweep([(X, y0, 0.03), (X, y0, 0.66), (X, y1 - 0.06, 0.66), (X, y1 - 0.06, 0.03)], w=0.05, h=0.07, r=0.10, mirror=True)
    K.foot((X, y0, 0), mirror=True); K.foot((X, y1 - 0.06, 0), mirror=True)
    for y in (-0.35, 0.15):
        K.tube((-X, y, 0.66), (X, y, 0.66), w=0.06, h=0.05)
    K.tube((-X, y0, 0.16), (X, y0, 0.16), w=0.06, h=0.05)
    K.tube((0, y0, 0.16), (0, yt + 0.07, 0.16), w=0.08, h=0.05)
    K.sweep([(-X, y1, 0.05), (0.33, y1, 0.05), (0.33, y1, piv[2])], w=0.06, h=0.08, r=0.12)
    K.foot((0.33, y1, 0))
    K.hub((0.33, y1, piv[2]), r=0.055, L=0.075)
    K.disc((0.268, y1, piv[2]), r=0.13, t=0.022, joint='joint_lever')
    K.disc((0.255, y1, piv[2]), r=0.05, t=0.02, mat='steel', joint='joint_lever')
    lever_arm(K, 'joint_lever')


@recipe
def machine_hip_abduction_adduction(K):
    # Ref: SFE Inner/Outer Thigh, Life Fitness Axiom Hip Abductor/Adductor: sezut inclinat, mecanism sub sezut,
    # doua brate cu perne pentru genunchi pe pivoti verticali.
    yt = spine_base(K, yfront=0.66)
    K.sweep([(0, -0.52, 0.07), (0, -0.39, 0.45), (0, -0.43, 1.08)], w=0.06, h=0.07, r=0.25)
    p = K.J('thigh_R')
    K.block((0, p[1], 0.20), (0.30, 0.15, 0.26), rc=0.04)                 # carcasa mecanismului
    K.block((0, p[1], 0.335), (0.32, 0.17, 0.02), mat='plastic', rc=0.05)
    lever_arm(K, 'joint_thigh_L', w=0.045, h=0.05); lever_arm(K, 'joint_thigh_R', w=0.045, h=0.05)
    side_handles(K)
    K.knob((0.15, p[1], 0.22))


def arm_curl_machine(K):
    yt = spine_base(K, yfront=0.70)
    piv = K.J('arms'); X = 0.33
    K.sweep([(0, 0.32, 0.07), (0, 0.27, 0.62), (0, 0.175, 0.845)], w=0.07, h=0.08, r=0.22)          # suportul pernei
    K.sweep([(X, -0.02, ZF), (X, piv[1], ZF), (X, piv[1], piv[2])], w=0.05, h=0.09, r=0.14, mirror=True)
    K.hub((X, piv[1], piv[2]), r=0.052, L=0.075, mirror=True)
    K.tube((-X, 0.0, 0.05), (X, 0.0, 0.05), w=0.09, h=0.06)
    K.foot((X, 0.02, 0), mirror=True); K.foot((X, piv[1], 0), mirror=True)
    K.disc((X - 0.062, piv[1], piv[2]), r=0.12, t=0.022, joint='joint_arms')
    lever_arm(K, 'joint_arms', w=0.04, h=0.05)
    K.hub((0.29, piv[1], piv[2]), r=0.04, L=0.045, joint='joint_arms', mirror=True)


@recipe
def machine_preacher_curl(K):
    # Ref: elitefts Preacher Curl Selectorized, Life Fitness Axiom Biceps Curl: perna inclinata, pivot la cot cu cama.
    arm_curl_machine(K)


@recipe
def machine_triceps_extension(K):
    # Ref: Life Fitness Axiom Biceps Curl / Triceps Extension, Precor Vitality C025.
    arm_curl_machine(K)


@recipe
def machine_ab_crunch(K):
    # Ref: Hammer Strength Select Abdominal Crunch, Precor Resolute Ab Crunch: sezut cu spatar, pivot cu cama
    # la nivelul soldului, brat cu perna de piept si manere, bara pentru picioare.
    yt = spine_base(K, yfront=0.68)
    K.sweep([(0, -0.46, 0.07), (0, -0.323, 0.45), (0, -0.342, 1.09)], w=0.06, h=0.07, r=0.25)
    piv = K.J('arm'); X = 0.33
    K.sweep([(X, 0.42, ZF), (X, piv[1], ZF), (X, piv[1], piv[2])], w=0.05, h=0.09, r=0.14, mirror=True)
    K.hub((X, piv[1], piv[2]), r=0.052, L=0.075, mirror=True)
    K.tube((-X, 0.30, 0.05), (X, 0.30, 0.05), w=0.09, h=0.06)
    K.foot((X, 0.36, 0), mirror=True); K.foot((X, piv[1], 0), mirror=True)
    K.disc((X - 0.062, piv[1], piv[2]), r=0.14, t=0.022, joint='joint_arm')
    K.disc((X - 0.075, piv[1], piv[2]), r=0.05, t=0.02, mat='steel', joint='joint_arm')
    lever_arm(K, 'joint_arm', w=0.04, h=0.06)
    K.sweep([(0, 0.52, 0.07), (0, 0.58, 0.27)], w=0.05, h=0.05, r=0)                 # bara pentru picioare
    K.rod((-0.21, 0.58, 0.28), (0.21, 0.58, 0.28), d=0.045, mat='rubber')


@recipe
def machine_rotary_torso(K):
    # Ref: Technogym Selection Rotary Torso, Muscle D Elite MDE-18: sezut rotativ pe coloana, spatar fix,
    # catarg lateral care trece peste umar spre perna de piept si manere.
    yt = spine_base(K, yfront=0.62, seat=False)
    j = K.J('seat')
    K.hub((0, j[1], 0.17), axis=(0, 0, 1), r=0.075, L=0.26)                          # coloana sezutului
    K.block((0, j[1], 0.045), (0.26, 0.26, 0.03), rc=0.06)
    K.sweep([(0, -0.38, 0.07), (0, -0.2, 0.45), (0, -0.2, 1.08)], w=0.06, h=0.07, r=0.25)       # stalp spatar
    Xm = 0.42
    K.sweep([(0, -0.27, 0.05), (Xm, -0.27, 0.05), (Xm, -0.27, 1.02), (Xm, 0.42, 1.02), (0.0, 0.42, 1.02)],
            w=0.06, h=0.08, r=[0, 0.12, 0.18, 0.16, 0])
    K.foot((Xm, -0.27, 0))
    K.tube((0, 0.42, 0.93), (0, 0.42, 1.26), w=0.05, h=0.05)


@recipe
def machine_calf_standing(K):
    # Ref: Skelcore Power Series Standing Calf, Muscle D Classic V2: turn in spate, parghie cu perne de umeri
    # pe pivot inalt, platforma pentru varfuri.
    K.drop_frame(); drop_feet(K); K.tower(); yt = K.towers[0]['S'][1]
    piv = K.J('lever'); X = 0.3
    K.sweep([(X, 0.52, ZF), (X, piv[1], ZF), (X, piv[1], piv[2])], w=0.05, h=0.09, r=0.16, mirror=True)
    K.hub((X, piv[1], piv[2]), r=0.052, L=0.075, mirror=True)
    K.foot((X, 0.46, 0), mirror=True); K.foot((X, piv[1], 0), mirror=True)
    K.tube((-X, piv[1], 0.05), (X, piv[1], 0.05), w=0.09, h=0.06)
    K.tube((-X, 0.44, 0.05), (X, 0.44, 0.05), w=0.09, h=0.06)
    K.tube((0, piv[1], 0.05), (0, yt + 0.12, 0.05), w=0.10, h=0.06)
    K.tube((-X, piv[1], 1.50), (X, piv[1], 1.50), w=0.07, h=0.05)
    K.tube((0.14, piv[1], 1.50), (0.14, yt + 0.06, 1.50), w=0.05, h=0.05, mirror=True)
    lever_arm(K, 'joint_lever', w=0.045, h=0.06)
    K.hub((0.225 + 0.05, piv[1], piv[2]), r=0.045, L=0.04, joint='joint_lever', mirror=True)


@recipe
def machine_assisted_pullup_dip(K):
    # Ref: Skelcore Power Series Dip/Chin Assist, Body-Solid S2ACD, Hammer Strength Select Assist Dip Chin:
    # turn inalt, doi stalpi care se indoaie sus spre turn, trepte laterale, platforma pentru genunchi.
    K.drop_frame(); drop_feet(K); K.tower(); yt = K.towers[0]['S'][1]; zt = K.towers[0]['ztop']
    X = 0.33; yp = 0.15
    K.sweep([(X, yp, 0.03), (X, yp, zt - 0.02), (0.19, yt + 0.05, zt - 0.02)], w=0.06, h=0.09, r=0.22, up=(0, 1, 0), mirror=True)
    K.tube((-X, yp, zt - 0.12), (X, yp, zt - 0.12), w=0.07, h=0.05)
    K.tube((-0.56, yp, 0.05), (0.56, yp, 0.05), w=0.09, h=0.06); K.foot((0.52, yp, 0), mirror=True)
    K.tube((0, yp, 0.05), (0, yt + 0.12, 0.05), w=0.10, h=0.06)
    K.tube((-X, yp, 1.05), (X, yp, 1.05), w=0.06, h=0.05)
    K.sweep([(X, yp, 0.22), (0.42, 0.32, 0.335)], w=0.05, h=0.05, r=0, mirror=True)              # suport trepte
    pk = K.J('knee_lever')
    K.tube((0, pk[1], 0.07), (0, pk[1], pk[2]), w=0.07, h=0.08, up=(0, 1, 0))
    K.hub((0, pk[1], pk[2]), r=0.05, L=0.13)


def cable_station(K, floor_beam):
    """Doua turnuri cu scripeti reglabili pe coloane, legate sus printr-o grinda cu bara de tractiuni."""
    K.drop_frame(); drop_feet(K)
    for p in K.parts:      # bara de otel de sus devine grinda vopsita
        if p['joint'] is None and p['mat'] == 'steel' and p['kind'] == 'box' and max(p['d']) > 1.2:
            p['dropped'] = True; zb = p['c'][2]; yb = p['c'][1]
    xs_all = []
    for k, T in enumerate(K.towers):
        t = K.tower(k); xs = T['S'][0]; ys = T['S'][1]; sg = 1 if xs > 0 else -1; xs_all.append(xs)
        jc = K.J('carriage_R' if sg > 0 else 'carriage_L'); xc, yc = jc[0], jc[1]
        K.tube((xs, ys - 0.30, 0.045), (xs, yc + 0.34, 0.045), w=0.08, h=0.07)             # talpa
        K.foot((xs, ys - 0.26, 0)); K.foot((xs, yc + 0.30, 0))
        zt = T['ztop']
        for z in (0.10, zt - 0.09):                                                        # console pentru coloana
            K.tube((xs, ys + 0.06, z), (xc, yc + 0.02, z), w=0.07, h=0.05)
            K.hub((xc, yc, z), axis=(0, 0, 1), r=0.034, L=0.07)
    xo = max(abs(x) for x in xs_all)
    K.sweep([(-xo, yb, zb), (xo, yb, zb)], w=0.08, h=0.07, r=0, up=(0, 0, 1))
    if floor_beam:
        K.tube((-xo, yb, 0.03), (xo, yb, 0.03), w=0.12, h=0.035)


@recipe
def cable_crossover(K):
    # Ref: Skelcore Cable Crossover, Body-Solid Series II, HOIST CMD-6180: doua turnuri carcasate,
    # coloane reglabile in fata, grinda sus cu manere de tractiuni, fara traversa pe podea.
    cable_station(K, floor_beam=False)


@recipe
def cable_functional_trainer(K):
    # Ref: Precor Resolute Dual Adjustable Pulley, Life Fitness Dual Adjustable Pulley.
    cable_station(K, floor_beam=True)


@recipe
def cable_lat_row_combo(K):
    # Ref: elitefts Lat Pulldown w/ Low Row, Muscle D Classic V2, Legend SelectEDGE: turn central inalt cu
    # brat sus pentru helcometru, sezut cu role pentru coapse, scripete jos + placa pentru picioare la ramat.
    K.drop_frame(); drop_feet(K); K.tower(); zt = K.towers[0]['ztop']
    K.tube((0, 0.10, 0.05), (0, 0.86, 0.05), w=0.11, h=0.06); K.tube((0, -0.10, 0.05), (0, -0.96, 0.05), w=0.11, h=0.06)
    for y in (0.86, -0.96):
        K.tube((-0.30, y, 0.05), (0.30, y, 0.05), w=0.09, h=0.06); K.foot((0.26, y, 0), mirror=True)
    K.tube((-0.60, 0, 0.05), (0.60, 0, 0.05), w=0.09, h=0.06); K.foot((0.56, 0, 0), mirror=True)
    K.sweep([(0, -0.07, zt + 0.03), (0, 0.54, zt + 0.03)], w=0.08, h=0.09, r=0)                    # bratul de sus
    K.block((0, 0.46, zt - 0.045), (0.05, 0.15, 0.10))
    s = K.A('seat_lat'); K.seat_post(base=(0, s[1], 0.07), top=(0, s[1], s[2] - 0.075))
    K.sweep([(0, 0.08, 0.62), (0, 0.40, 0.62), (0, 0.40, 0.735)], w=0.05, h=0.05, r=0.06); K.knob((0.025, 0.30, 0.62))
    r = K.A('seat_row'); K.tube((0, r[1], 0.07), (0, r[1], r[2] - 0.08), w=0.07, h=0.07, up=(0, 1, 0))
    K.tube((0, -0.08, 0.12), (0, -0.29, 0.12), w=0.05, h=0.05)
    K.sweep([(0.15, -0.30, 0.07), (0.15, -0.375, 0.30)], w=0.04, h=0.04, r=0, mirror=True)


@recipe
def smith_machine(K):
    # Ref: Precor / Hoist / Body-Solid Series 7 Smith: doua cadre laterale in U intors, ghidaje inclinate 7 grade,
    # sine cu carlige de siguranta, traversa sus. Fara traversa pe podea sub bara.
    K.drop_frame(); drop_feet(K)
    X = 1.042
    K.sweep([(X, -0.45, 0.09), (X, -0.45, 2.16), (X, 0.45, 2.16), (X, 0.45, 0.09)], w=0.075, h=0.075, r=0.14,
            up=(0, 1, 0), mirror=True)
    K.tube((X, -0.66, 0.045), (X, 0.66, 0.045), w=0.09, h=0.09, mirror=True)
    K.foot((X, -0.6, 0), mirror=True); K.foot((X, 0.6, 0), mirror=True)
    K.tube((-X, -0.114, 2.085), (X, -0.114, 2.085), w=0.07, h=0.06)                       # traversa sus (capete ghidaje)
    K.tube((-X, -0.45, 0.10), (X, -0.45, 0.10), w=0.08, h=0.06)                           # traversa jos, in spate
    K.tube((X, 0.128, 0.10), (0.60, 0.128, 0.10), w=0.07, h=0.06, mirror=True)            # suport ghidaj jos
    K.sweep([(X, 0.128, 0.10), (X, 0.128, 0.0901)], w=0.07, h=0.06, r=0, mirror=True, caps=False)


def horns(K, x, y, zs, length=0.22):
    """Coarne de depozitare a discurilor."""
    for z in zs:
        K.rod((x, y, z), (x + length, y, z), d=0.05, mirror=True)
        K.hub((x + 0.04, y, z), r=0.04, L=0.02, mat='steel', mirror=True)


@recipe
def hack_squat(K):
    # Ref: Extreme Training Equipment Hack Squat, Hammer Strength Hack Squat, Titan Linear Hack Squat:
    # talpi lungi, stalpi in spate, lonjeroane inclinate la 45 de grade langa ghidaje, placa de picioare jos.
    K.drop_frame(); drop_feet(K)
    X = 0.33
    K.sweep([(X, 1.06, ZF), (X, -0.86, ZF), (X, -0.86, 1.72)], w=0.06, h=0.09, r=0.16, mirror=True)
    K.tube((X, -0.83, 1.69), (X, 0.74, 0.12), w=0.05, h=0.08, mirror=True)                 # lonjeron la 45 de grade
    for y, z in ((-0.86, 1.68), (0.68, 0.17), (-0.86, 0.06), (1.02, 0.06)):
        K.tube((-X, y, z), (X, y, z), w=0.07, h=0.06)
    K.foot((X, 1.0, 0), mirror=True); K.foot((X, -0.8, 0), mirror=True)
    K.tube((0.24, 0.93, 0.07), (0.24, 0.93, 0.158), w=0.05, h=0.05, up=(0, 1, 0), mirror=True)
    horns(K, X + 0.03, -0.86, (0.5, 0.85, 1.2))


@recipe
def leg_press_45(K):
    # Ref: BLK BOX 45 Degree Leg Press, Hammer Strength Linear Leg Press, Exigo 45: cadre laterale triunghiulare
    # (talpa, stalp spate, sina la 45 de grade dintr-o singura teava), sezut jos, coarne de discuri in spate.
    K.drop_frame(); drop_feet(K)
    X = 0.41
    K.sweep([(X, -1.22, ZF), (X, 1.15, ZF), (X, 1.15, 1.47), (X, -0.2, 0.2)], w=0.06, h=0.09, r=[0, 0.16, 0.13, 0], mirror=True)
    K.tube((X, 0.2, 0.09), (X, 0.2, 0.58), w=0.05, h=0.08, up=(0, 1, 0), mirror=True)
    for y, z in ((-1.17, 0.05), (0.2, 0.11), (1.15, 0.05), (1.15, 1.44)):
        K.tube((-X, y, z), (X, y, z), w=0.08, h=0.06)
    K.tube((0, -1.17, 0.05), (0, 0.2, 0.05), w=0.10, h=0.06)
    K.sweep([(0, -0.54, 0.07), (0, -0.62, 0.34)], w=0.08, h=0.08, r=0)
    K.sweep([(0, -0.92, 0.07), (0, -1.0, 0.56)], w=0.08, h=0.08, r=0)
    for y in (-1.15, 0.0, 1.1):
        K.foot((X, y, 0), mirror=True)
    horns(K, X + 0.03, 1.15, (0.55, 0.95))


@recipe
def plate_calf_seated(K):
    # Ref: Hammer Strength / Skelcore / Gym Gear Pro Series Seated Calf Raise: coloana joasa, sezut mic,
    # parghie cu role pentru genunchi si corn de discuri, pivot in spatele sezutului.
    K.drop_frame(); drop_feet(K)
    piv = K.J('lever')
    K.tube((0, -0.64, 0.05), (0, 0.76, 0.05), w=0.11, h=0.06)
    for y in (-0.64, 0.76):
        K.tube((-0.31, y, 0.05), (0.31, y, 0.05), w=0.09, h=0.06); K.foot((0.27, y, 0), mirror=True)
    K.sweep([(0.3, -0.64, 0.08), (0.3, piv[1], 0.32), (0.3, piv[1], piv[2])], w=0.05, h=0.08, r=0.2, mirror=True)
    K.hub((0.3, piv[1], piv[2]), r=0.05, L=0.07, mirror=True)
    s = K.A('seat'); K.seat_post(base=(0, s[1], 0.07), top=(0, s[1], s[2] - 0.075))


@recipe
def glute_ham_developer(K):
    # Ref: French Fitness GHD20, Body-Solid ProClub SGH500, Titan GHD: baza lunga cu talpi late, cadru in U intors,
    # perne mari semirotunde pentru solduri, role pentru glezne si placa pentru talpi reglabile.
    K.drop_frame(); drop_feet(K)
    K.tube((0, -0.92, 0.05), (0, 0.92, 0.05), w=0.11, h=0.06)
    for y in (-0.92, 0.92):
        K.tube((-0.37, y, 0.05), (0.37, y, 0.05), w=0.09, h=0.06); K.foot((0.33, y, 0), mirror=True)
    K.sweep([(0, -0.46, 0.07), (0, -0.15, 0.97), (0, 0.55, 0.97), (0, 0.55, 0.07)], w=0.08, h=0.08, r=0.13)
    K.tube((0, -0.34, 0.97), (0, -0.14, 0.97), w=0.08, h=0.08)
    K.block((0, -0.2, 0.925), (0.46, 0.22, 0.03), mat='plastic', rc=0.04)
    K.tube((0, 0.55, 0.72), (0, 0.672, 0.72), w=0.05, h=0.05)
    K.tube((0, 0.60, 1.0), (0, 0.60, 1.10), w=0.05, h=0.05, up=(0, 1, 0))
    K.knob((0.04, 0.45, 0.97)); K.knob((0.04, 0.55, 0.6))


@recipe
def hyperextension_45(K):
    # Ref: Body-Solid GHPY345 / Powerline PHYP200X, CAP 45 Degree Hyperextension: stalp principal la 45 de grade,
    # contrafisa curbata, perna pentru solduri sus, manere laterale, suport reglabil pentru picioare.
    K.drop_frame(); drop_feet(K)
    K.tube((0, -0.84, 0.05), (0, 0.57, 0.05), w=0.11, h=0.06)
    for y in (-0.84, 0.57):
        K.tube((-0.32, y, 0.05), (0.32, y, 0.05), w=0.09, h=0.06); K.foot((0.28, y, 0), mirror=True)
    K.sweep([(0, -0.56, 0.08), (0, 0.214, 0.853)], w=0.07, h=0.08, r=0)
    K.sweep([(0, 0.44, 0.07), (0, 0.36, 0.46), (0, 0.10, 0.73)], w=0.06, h=0.07, r=0.3)
    K.tube((0, -0.337, 0.07), (0, -0.337, 0.30), w=0.05, h=0.05, up=(0, 1, 0))
    K.tube((0, 0.11, 0.73), (0, 0.035, 0.805), w=0.06, h=0.06)
    K.sweep([(0.0, 0.19, 0.83), (0.24, 0.19, 0.83), (0.24, 0.31, 0.95)], w=0.03, h=0.03, r=0.05, round_=True,
            mat='steel', mirror=True, caps=False)
    K.rod((0.24, 0.235, 0.875), (0.24, 0.315, 0.955), d=0.038, mat='rubber', mirror=True)
    K.knob((0.04, -0.40, 0.25))
