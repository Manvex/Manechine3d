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


# ---------------------------------------------------------------- aparate cardio
def treadmill(K):
    # Ref: Cybex CX-445T, Precor TRM 885, Life Fitness Integrity: punte cu sine laterale argintii, capota de motor
    # in fata, doi montanti curbati, bord cu ecran, manere laterale si bara frontala.
    rails = [p for p in K.parts if p['mat'] == 'frame_gray' and p['kind'] == 'box' and max(p['d']) > 1.1]
    r0 = rails[0]; il = int(np.argmax(r0['d'])); u = r0['R'][:, il].copy()
    if u[1] < 0: u = -u
    n = np.cross([1.0, 0, 0], u); n = n if n[2] > 0 else -n
    L = r0['d'][il]; mid = np.array([0, r0['c'][1], r0['c'][2]]); F = mid + u * L / 2; B = mid - u * L / 2
    K.drop_all(keep=lambda p: p['mat'] in ('belt',) or (p['mat'] == 'plastic' and max(p['d']) > 1.0 and p['kind'] == 'box'))
    X = abs(r0['c'][0])
    def P(s, h, x=0.0):        # punct in coordonatele puntii: s de-a lungul, h pe normala, fata de capatul din fata
        q = F + u * s + n * h; return (x, q[1], q[2])
    # sine laterale + benzi antiderapante + capace spate
    K.sweep([P(-L - 0.02, 0, X), P(0.02, 0, X)], w=0.09, h=0.15, r=0, mat='shroud', up=n, mirror=True, corner=0.03)
    K.sweep([P(-L + 0.02, 0.078, X), P(-0.04, 0.078, X)], w=0.07, h=0.008, r=0, mat='rubber', up=n, mirror=True, caps=False, corner=0.003)
    for sx in (1, -1):
        c = np.array(P(-L - 0.02, -0.01, X * sx)); Rb = np.stack([np.array([1.0, 0, 0]), u, n], axis=1)
        K.block(c, (0.11, 0.12, 0.15), mat='plastic', rc=0.03, R=Rb)
    # capota motorului
    K.slab([(-0.14, -0.07), (0.30, -0.07), (0.30, 0.07), (0.18, 0.175), (-0.06, 0.15), (-0.14, 0.085)], 0.70, bevel=0.04,
           mat='plastic', r=0.05, o=F, e1=u, e2=n)
    K.slab([(-0.08, 0.10), (0.16, 0.12), (0.16, 0.176), (-0.06, 0.152)], 0.50, bevel=0.02, mat='shroud', r=0.02, o=F, e1=u, e2=n)
    # baza din fata + picioare spate
    K.tube((-0.42, 1.05, 0.04), (0.42, 1.05, 0.04), w=0.09, h=0.07)
    K.rod((0.42, 1.05, 0.045), (0.47, 1.05, 0.045), d=0.09, mat='rubber', mirror=True)        # roti de transport
    K.tube((0.37, 0.36, 0.04), (0.37, 1.02, 0.04), w=0.07, h=0.06, mirror=True)
    for sx in (1, -1):
        b = np.array(P(-L + 0.06, -0.075, X * sx))
        if b[2] < 0.12: K.foot((b[0], b[1], 0))
    if F[2] > 0.3:     # varianta inclinata: bratele de ridicare
        K.tube((0.30, 0.34, 0.06), P(-0.14, -0.07, 0.30), w=0.04, h=0.05, mirror=True)
        K.tube((0.30, 0.95, 0.06), P(-0.56, -0.07, 0.30), w=0.04, h=0.05, mirror=True)
    # montanti si manere
    Xu = 0.39
    K.sweep([(Xu, 1.03, 0.06), (Xu, 1.00, 0.80), (Xu, 0.84, 1.02), (Xu, 0.62, 1.02)], w=0.06, h=0.10, r=[0, 0.30, 0.12, 0],
            mat='shroud', mirror=True)
    K.rod((Xu, 0.63, 1.015), (Xu, 0.25, 1.01), d=0.042, mat='rubber', mirror=True)
    K.hub((Xu, 0.25, 1.01), axis=(0, 1, 0), r=0.023, L=0.012, mat='plastic', mirror=True)
    # bord
    K.slab([(0.65, 1.04), (0.73, 0.985), (1.10, 1.25), (1.05, 1.325), (0.94, 1.325), (0.63, 1.09)], 0.78, bevel=0.035,
           mat='plastic', r=0.035)
    K.slab([(0.66, 0.975), (0.90, 0.975), (0.90, 1.045), (0.66, 1.045)], 0.86, bevel=0.03, mat='plastic', r=0.025)
    K.console((0.0, 0.795, 1.215), size=(0.36, 0.26), tilt=49, thick=0.02)
    K.rod((-0.30, 0.60, 1.03), (0.30, 0.60, 1.03), d=0.04, mat='rubber')                       # bara frontala
    K.sweep([(0.30, 0.60, 1.03), (0.30, 0.70, 1.04)], w=0.035, h=0.035, r=0, round_=True, mat='plastic', mirror=True, caps=False)
    K.disc((0, 0.655, 1.085), axis=(0, -0.75, 0.66), r=0.028, t=0.016, mat='accent')            # oprire de urgenta


RECIPES['treadmill_flat'] = treadmill
RECIPES['treadmill_incline'] = treadmill


@recipe
def upright_bike(K):
    # Ref: Matrix U7xe, Star Trac 8UB, Precor UBK 885: carcasa-picatura in jurul volantei, baza cu doua talpi,
    # tija de sa reglabila, catarg in fata cu ghidon si consola.
    K.drop_all(keep=lambda p: p['mat'] in ('rubber', 'vinyl', 'steel') or p['nv'] == 350)
    K.tube((0, -0.40, 0.05), (0, 0.72, 0.05), w=0.09, h=0.06)
    for y, w in ((-0.40, 0.30), (0.72, 0.38)):
        K.tube((-w, y, 0.045), (w, y, 0.045), w=0.08, h=0.06)
        K.rod((w - 0.01, y, 0.045), (w + 0.03, y, 0.045), d=0.075, mat='plastic', mirror=True)
    K.slab([(-0.12, 0.09), (0.64, 0.09), (0.76, 0.30), (0.62, 0.57), (0.22, 0.63), (-0.07, 0.52), (-0.16, 0.26)], 0.18,
           bevel=0.045, mat='shroud', r=0.10)
    c = K.J('crank')
    for sx in (1, -1):
        K.disc((sx * 0.086, c[1], c[2]), r=0.16, t=0.016, mat='plastic')
        K.disc((sx * 0.096, c[1], c[2]), r=0.045, t=0.02, mat='steel')
    K.sweep([(0, -0.095, 0.36), (0, -0.045, 0.585)], w=0.065, h=0.075, r=0); K.knob((0.033, -0.06, 0.52))     # manson sa
    K.sweep([(0, 0.62, 0.50), (0, 0.86, 0.78), (0, 0.86, 1.29)], w=0.07, h=0.10, r=0.30)                       # catarg
    K.block((0, 0.80, 1.19), (0.10, 0.20, 0.06), rc=0.02)
    K.console((0, 0.87, 1.40), size=(0.30, 0.22), tilt=28)
    K.tube((0, 0.865, 1.27), (0, 0.875, 1.34), w=0.05, h=0.05, up=(0, 1, 0))


@recipe
def elliptical_trainer(K):
    # Ref: Star Trac 6CT, Life Fitness Integrity Cross-Trainer, Precor EFX: volanta carcasata in spate, grinda centrala
    # cu sine, carcasa si catarg in fata, consola, manere fixe; bratele mobile si pedalele sunt piese separate.
    K.drop_all(keep=lambda p: p['mat'] == 'rubber' or (p['mat'] == 'powder' and p['kind'] == 'cyl' and p['nv'] == 82))
    yf = -0.85; zf = 0.46
    K.disc((0, yf, zf), r=0.25, t=0.22, mat='shroud'); K.disc((0, yf, zf), r=0.19, t=0.25, mat='plastic')
    K.disc((0, yf, zf), r=0.05, t=0.30, mat='steel')
    K.slab([(-1.12, 0.03), (-0.56, 0.03), (-0.56, 0.24), (-0.66, 0.40), (-1.02, 0.40), (-1.12, 0.22)], 0.20, bevel=0.04,
           mat='plastic', r=0.06)
    K.tube((-0.28, -1.02, 0.045), (0.28, -1.02, 0.045), w=0.10, h=0.07); K.foot((0.24, -1.02, 0), mirror=True)
    K.tube((0, -0.60, 0.20), (0, 0.14, 0.20), w=0.10, h=0.07)
    K.rod((0.09, -0.60, 0.20), (0.09, -0.05, 0.15), d=0.03, mirror=True)
    K.slab([(0.04, 0.09), (0.66, 0.09), (0.66, 0.44), (0.57, 0.70), (0.36, 0.72), (0.04, 0.38)], 0.34, bevel=0.06,
           mat='shroud', r=0.08)
    K.tube((-0.42, 0.30, 0.05), (0.42, 0.30, 0.05), w=0.14, h=0.08); K.foot((0.38, 0.30, 0), size=(0.12, 0.16), mirror=True)
    K.sweep([(0, 0.50, 0.66), (0, 0.61, 1.02), (0, 0.43, 1.38)], w=0.07, h=0.09, r=0.30)
    K.console((0, 0.37, 1.44), size=(0.32, 0.24), tilt=30)
    K.block((0, 0.40, 1.33), (0.12, 0.10, 0.07), rc=0.02)
    K.rod((-0.20, 0.35, 0.60), (0.20, 0.35, 0.60), d=0.035)


@recipe
def rowing_machine(K):
    # Ref: Bells of Steel Blitz Air Rower, Torque Stealth Air Rower, Concept2 RowErg: monosina din aluminiu,
    # volanta cu carcasa perforata in fata pe picioare in A, brat cu monitor, placa pentru picioare.
    K.drop_all(keep=lambda p: p['mat'] == 'rubber' or (p['mat'] == 'powder' and p['kind'] == 'box' and min(p['d']) < 0.05 and max(p['d']) > 0.3 and p['d'][0] > 0.3))
    K.sweep([(0, -0.67, 0.335), (0, 0.84, 0.335)], w=0.09, h=0.07, r=0, mat='shroud', corner=0.012)
    K.sweep([(0, 0.78, 0.30), (0, 1.02, 0.33), (0, 1.44, 0.62)], w=0.07, h=0.11, r=0.25)
    K.sweep([(0, -0.64, 0.31), (0, -0.72, 0.04)], w=0.06, h=0.08, r=0)
    K.tube((-0.30, -0.72, 0.03), (0.30, -0.72, 0.03), w=0.07, h=0.045)
    K.sweep([(0.03, 1.31, 0.46), (0.30, 1.34, 0.04)], w=0.05, h=0.07, r=0, mirror=True)
    K.tube((-0.42, 1.34, 0.03), (0.42, 1.34, 0.03), w=0.07, h=0.045)
    K.rod((0.37, 1.39, 0.04), (0.41, 1.39, 0.04), d=0.07, mat='plastic', mirror=True)
    yw, zw = 1.6, 0.55
    K.disc((0, yw, zw), r=0.255, t=0.20, mat='plastic'); K.disc((0, yw, zw), r=0.215, t=0.235, mat='shroud')
    K.disc((0, yw, zw), r=0.10, t=0.262, mat='plastic'); K.disc((0, yw, zw), r=0.03, t=0.285, mat='steel')
    K.sweep([(0, 1.30, 0.70), (0, 0.97, 0.94)], w=0.03, h=0.05, r=0)
    c = (0, 0.945, 0.985); K.console(c, size=(0.14, 0.17), tilt=20, thick=0.03)
    K.block((0, 1.22, 0.60), (0.10, 0.12, 0.10), rc=0.02)


def regray(K, joint, w=None):
    """Piesele mobile gri (cutii) devin profile rotunjite in culoarea cadrului."""
    for p in K.parts:
        if p['joint'] == joint and p['mat'] == 'frame_gray' and p['kind'] == 'box' and min(p['d']) >= 0.02:
            p['dropped'] = True; d = p['d']; il = int(np.argmax(d)); ax = p['R'][:, il] * d[il] / 2
            o = [i for i in range(3) if i != il]
            K.sweep([p['c'] - ax, p['c'] + ax], d[o[0]] + 0.006, d[o[1]] + 0.006, r=0, joint=joint, up=p['R'][:, o[1]])


def keep_fittings(p):
    """Pastreaza scripetii, otelul, cauciucul, greutatile si placile subtiri."""
    return p['mat'] in ('steel', 'rubber', 'iron', 'vinyl', 'label') or (p['mat'] == 'plastic' and p['kind'] != 'box') \
        or (p['kind'] == 'box' and min(p['d']) < 0.021 and max(p['d']) < 0.3)


@recipe
def cable_lat_station(K):
    # Ref: Skelcore Power Series Lat Pulldown, elitefts Lat Pulldown Selectorized, Body-Solid GLM85: turn carcasat in fata,
    # grinda sus cu scripeti, catarg inclinat, banca joasa cu role reglabile pentru coapse.
    K.drop_all(keep=keep_fittings)
    S = K.J('stack'); ys = S[1]
    K.tower(top=1.99)
    K.sweep([(0, ys + 0.03, 2.045), (0, 0.07, 1.985)], w=0.09, h=0.09, r=0)
    K.sweep([(0, 0.76, 0.07), (0, 1.30, 1.97)], w=0.07, h=0.10, r=0)
    K.tube((0, 0.20, 0.045), (0, ys - 0.12, 0.045), w=0.10, h=0.07)
    K.tube((-0.26, 0.22, 0.045), (0.26, 0.22, 0.045), w=0.08, h=0.06); K.foot((0.22, 0.22, 0), mirror=True)
    K.sweep([(0, -0.20, 0.312), (0, 0.95, 0.312)], w=0.10, h=0.06, r=0)
    K.sweep([(0, 0.40, 0.07), (0, 0.03, 0.07), (0, 0.03, 0.29)], w=0.09, h=0.07, r=0.13)
    K.tube((0, 0.95, 0.07), (0, 0.95, 0.29), w=0.07, h=0.07, up=(0, 1, 0))
    K.block((0, 1.05, 0.20), (0.09, 0.27, 0.16), rc=0.03)
    K.block((0, 1.352, 1.70), (0.035, 0.08, 0.36)); K.block((0, 1.352, 1.93), (0.03, 0.06, 0.16))
    K.knob((0.05, 0.30, 0.312))
    regray(K, 'joint_pad_adjust'); regray(K, 'joint_seat_adjust')


@recipe
def cable_tower_high(K):
    # Ref: turnuri cu scripete inalt (Skelcore / elitefts lat pulldown, coloane de cablu Body-Solid): turn carcasat,
    # brat curbat tip gat-de-lebada cu scripeti la varf, placa de baza.
    K.drop_all(keep=keep_fittings)
    S = K.J('stack'); ys = S[1]
    K.tower(top=2.0, base=False)
    K.block((0, 0.80, 0.014), (0.68, 0.62, 0.028), mat='plastic', rc=0.06)
    K.sweep([(0, 0.72, 0.03), (0, 0.72, 1.72), (0, 0.325, 2.195)], w=0.07, h=0.10, r=0.5)
    for z in (0.82, 1.44):
        K.block((0, 0.80, z), (0.30, 0.12, 0.08), rc=0.02)
    K.block((0, 0.72, 0.09), (0.12, 0.20, 0.12), rc=0.03)


@recipe
def lever_leg_press(K):
    # Ref: Skelcore Power Series Leg Press, Muscle D Classic V2 Leg Press, Hammer Strength Select Seated Leg Press:
    # turn carcasat in spatele sezutului, talpi laterale lungi, stalpi in fata, sine inclinate pentru placa de picioare.
    K.drop_all(keep=keep_fittings)
    K.tower(top=1.88)
    X = 0.30
    K.sweep([(X, -0.52, 0.06), (X, 1.32, 0.06), (0.27, 1.01, 0.64)], w=0.06, h=0.09, r=[0, 0.10, 0], mirror=True)
    for y in (0.35, 1.26):
        K.tube((-X, y, 0.06), (X, y, 0.06), w=0.07, h=0.07)
    K.tube((-X, -0.50, 0.06), (X, -0.50, 0.06), w=0.07, h=0.07)
    K.tube((-0.27, 1.0, 0.62), (0.27, 1.0, 0.62), w=0.06, h=0.06)
    K.tube((0.27, 0.03, 0.08), (0.27, 0.03, 0.25), w=0.05, h=0.08, up=(0, 1, 0), mirror=True)
    for y in (-0.46, 0.4, 1.28):
        K.foot((X, y, 0), mirror=True)
    regray(K, 'joint_plate'); regray(K, 'joint_seat')
