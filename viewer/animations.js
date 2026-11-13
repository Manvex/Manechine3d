// Animații de exerciții pentru scheletul manechinului.
// Toate oasele au orientarea globală identitate în poza de repaus (poză A, fața spre +Z,
// dreapta personajului spre −X), deci rotațiile se scriu în axele lumii:
//   X = axa laterală, Y = sus, Z = înainte.
import * as THREE from 'three';

const X = new THREE.Vector3(1, 0, 0);
const Y = new THREE.Vector3(0, 1, 0);
const Z = new THREE.Vector3(0, 0, 1);
const D = THREE.MathUtils.degToRad;

const FINGERS = ['Index', 'Middle', 'Ring', 'Pinky'];
const SEGS = ['Proximal', 'Intermediate', 'Distal'];

const smooth = (x) => x * x * x * (x * (x * 6 - 15) + 10); // smootherstep 0..1

// Funcție pe bucăți: chei [timp normalizat, valoare], interpolare smootherstep între ele.
export function keys(list, t) {
  if (t <= list[0][0]) return list[0][1];
  for (let i = 1; i < list.length; i++) {
    const [t1, v1] = list[i];
    const [t0, v0] = list[i - 1];
    if (t <= t1) return v0 + (v1 - v0) * smooth((t - t0) / (t1 - t0 || 1));
  }
  return list[list.length - 1][1];
}

// Mâinile manechinului sunt modelate deja strânse în pumn, cu nodul *_grip în centrul pumnului.
// curl > 0 strânge mai tare, curl < 0 deschide mâna; thumb < 0 desface degetul mare.
export function grip(rig, side, curl, thumb = 0) {
  const pre = side === 'R' ? 'Right' : 'Left';
  const s = side === 'R' ? 1 : -1;
  const knuckle = rig.axis(`${side}_hand`, Z);
  FINGERS.forEach((f, i) => {
    const spread = [1.0, 1.05, 1.0, 0.95][i];
    SEGS.forEach((seg, j) => {
      const k = [0.9, 1.15, 0.75][j];
      rig.rotW(`${pre}_${f}${seg}`, knuckle, s * curl * k * spread);
    });
  });
  // Degetul mare: se închide peste bară (în jurul axei lungi a mâinii), apoi se îndoaie.
  const along = rig.dir(`${side}_hand`, `${pre}_MiddleProximal`);
  rig.rotW(`${pre}_ThumbProximal`, along, s * D(-30) * thumb);
  rig.rotW(`${pre}_ThumbIntermediate`, knuckle, s * D(20) * thumb);
  rig.rotW(`${pre}_ThumbDistal`, knuckle, s * D(25) * thumb);
}

// Postura de bază: în picioare, brațele pe lângă corp, respirație ușoară.
export function standing(rig, time, opts = {}) {
  const breath = Math.sin(time * Math.PI * 2 / 4.2);
  const sway = Math.sin(time * Math.PI * 2 / 7.3);
  rig.rotW('hips', Z, D(0.6) * sway);
  rig.rotW('spine', X, D(-0.8) * breath);
  rig.rotW('chest', X, D(-0.9) * breath);
  rig.rotW('neck', X, D(0.6) * breath);

  // umerii: din poza A (45°) în brațe lăsate, ~8° depărtate de corp
  rig.rotW('R_clavicle', Z, D(2));
  rig.rotW('L_clavicle', Z, D(-2));
  rig.rotW('R_upperarm', Z, D(opts.rAbd ?? 37));
  rig.rotW('L_upperarm', Z, D(-(opts.lAbd ?? 39)));
  rig.rotW('R_forearm', X, D(-(opts.rElbow ?? 8)));
  rig.rotW('L_forearm', X, D(-(opts.lElbow ?? 10)));
  // picioare ușor depărtate, genunchi ușor relaxați
  rig.rotW('R_thigh', Z, D(-1.5));
  rig.rotW('L_thigh', Z, D(1.5));
  // mâini relaxate: pumnul din poza de repaus, deschis pe jumătate
  if (!opts.keepRightHand) grip(rig, 'R', D(-38), -0.8);
  if (!opts.keepLeftHand) grip(rig, 'L', D(-38), -0.8);
}

export const idle = {
  duration: 4.2,
  phases: [],
  pose(rig, t, time) { standing(rig, time); },
};

// 6268 — EZ Barbell Standing Single Arm Neutral Wrist Curl
// Bara EZ ținută de mijloc, priză neutră, braț drept întins pe lângă corp.
// Mișcarea e doar în încheietură: deviație radială (capătul din față urcă)
// și deviație ulnară (capătul din față coboară). Antebrațul rămâne nemișcat.
const WRIST = [ // [timp în ciclu, unghi încheietură în grade; + = radial]
  [0.00, -30], [0.10, -30],   // jos, întindere ulnară
  [0.46, 26],                 // urcare (concentric)
  [0.58, 26],                 // contracție sus
  [0.96, -30], [1.00, -30],   // coborâre controlată
];

export const ex6268 = {
  id: '6268',
  duration: 3.4,
  muscleBones: { R_forearm: 1, R_wrist_half: 0.8, R_elbow_half: 0.35 },
  equipment: [{
    url: 'echipamente/glb/ez_bar_olympic.glb',
    attach: 'R_grip',
    // bara (axa X a modelului) devine orizontală, de la spate spre față
    worldRotation: new THREE.Quaternion().setFromAxisAngle(Y, D(-90)),
    offset: new THREE.Vector3(0, 0, 0),
  }],
  camera: '34',
  tags: ['Antebrațe', 'Bară EZ', 'În picioare', 'Un braț'],
  steps: [
    'Stai drept, cu picioarele la lățimea șoldurilor. Ține bara EZ de mijloc, cu mâna dreaptă, palma spre coapsă (priză neutră).',
    'Brațul rămâne întins pe lângă corp. Bara stă orizontală, de la spate spre față.',
    'Coboară capătul din față lăsând încheietura să cadă spre degetul mic (deviație ulnară).',
    'Ridică capătul din față doar din încheietură, spre degetul mare (deviație radială). Cotul și umărul nu se mișcă.',
    'Ține o clipă sus, apoi coboară controlat. Schimbă mâna după setul complet.',
  ],
  muscles: [
    ['Extensor radial lung și scurt al carpului', 'p'],
    ['Flexor radial al carpului', 'p'],
    ['Lung abductor al policelui', 's'],
    ['Brahioradial (stabilizare)', 's'],
  ],
  phases: [
    { from: 0.00, to: 0.10, label: 'Jos · întindere ulnară' },
    { from: 0.10, to: 0.46, label: 'Ridicare · deviație radială' },
    { from: 0.46, to: 0.58, label: 'Contracție sus' },
    { from: 0.58, to: 1.00, label: 'Coborâre controlată' },
  ],
  gauge: { min: -30, max: 26, label: (v) => v >= 0 ? 'Deviație radială' : 'Deviație ulnară' },
  effort(t) { return t > 0.1 && t < 0.58 ? 1 : 0.55; },
  angle(t) { return keys(WRIST, t); },
  pose(rig, t, time) {
    standing(rig, time, { rAbd: 32, rElbow: 6, keepRightHand: true });
    const w = keys(WRIST, t);
    // deviația radială duce mâna spre degetul mare, adică înainte: rotație în jurul −X
    rig.rotW('R_hand', X, D(-w));
    // pumnul se strânge puțin mai tare în partea de sus
    grip(rig, 'R', D(3) * Math.max(0, w) / 26);
  },
  // Pentru atașarea barei: poza cu încheietura neutră.
  neutral(rig) {
    standing(rig, 0, { rAbd: 32, rElbow: 6, keepRightHand: true });
  },
};

export const ANIMATIONS = { '6268': ex6268 };
