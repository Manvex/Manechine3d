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

// 0001 — 3/4 Sit up
// Culcat pe spate, genunchii îndoiți, tălpile pe saltea, mâinile la ceafă. Trunchiul se
// rulează în sus cam trei sferturi din drum, ține o clipă, apoi coboară încet.
const MAT_TOP = 0.03;
const CURL = [ // [timp în ciclu, îndoire totală a coloanei în grade]
  [0.00, 0], [0.10, 0],       // culcat
  [0.40, 128],                // urcare
  [0.56, 128],                // sus
  [0.92, 0], [1.00, 0],       // coborâre controlată
];
const SMOOTH = (x) => Math.min(1, Math.max(0, x));

function lyingPose(rig, curlDeg, time) {
  const F = D(curlDeg);
  const breath = Math.sin(time * Math.PI * 2 / 4.2);

  // culcat pe spate: fața în sus, capul spre −Z, bazinul pe saltea
  rig.rotW('hips', X, D(-90));
  rig.b.hips.position.set(0, MAT_TOP + 0.158, 0.16);

  // trunchiul se rulează vertebră cu vertebră; cea mai mare parte a mișcării e în zona lombară
  rig.rotW('spine', X, F * 0.40);
  rig.rotW('spine2', X, F * 0.31);
  rig.rotW('chest', X, F * 0.17 + D(0.8) * breath);
  rig.rotW('neck', X, F * 0.06);
  rig.rotW('head', X, F * 0.05 + D(4));

  // picioare: tălpile plate pe saltea, genunchii îndoiți (IK pe șold–genunchi–gleznă)
  for (const [side, sx] of [['R', -1], ['L', 1]]) {
    const hip = rig.pos(`${side}_thigh`);
    const ankle = new THREE.Vector3(hip.x + sx * 0.012, MAT_TOP + 0.108, hip.z + 0.44);
    rig.ik2(`${side}_thigh`, `${side}_shin`, `${side}_foot`, ankle, new THREE.Vector3(sx * 0.12, 1, 0));
    rig.setRestW(`${side}_foot`); // talpa rămâne paralelă cu podeaua
  }

  // mâini la ceafă, coatele larg (IK pe umăr–cot–încheietură)
  const headQ = rig.quat('head'), chestQ = rig.quat('chest');
  const headPos = rig.pos('head');
  const fwd = new THREE.Vector3(0, 0, 1).applyQuaternion(chestQ);
  for (const [side, sx] of [['R', -1], ['L', 1]]) {
    const wrist = headPos.clone().add(new THREE.Vector3(sx * 0.118, 0.05, -0.075).applyQuaternion(headQ));
    const pole = new THREE.Vector3(sx, 0, 0).addScaledVector(fwd, 0.45);
    rig.ik2(`${side}_upperarm`, `${side}_forearm`, `${side}_hand`, wrist, pole);
    const mid = headPos.clone().add(new THREE.Vector3(0, 0.04, -0.105).applyQuaternion(headQ));
    rig.aim(`${side}_hand`, `${side}_grip`, mid.sub(rig.pos(`${side}_hand`)));
    grip(rig, side, D(-18), -0.4);
  }
}

export const ex0001 = {
  id: '0001',
  duration: 5.2,
  mat: true,
  // abdomenul din față: fâșie centrală (dreptul abdominal) și părțile laterale (oblicii)
  muscleMask(x, y, z) {
    const ax = Math.abs(x);
    const front = SMOOTH((z + 0.01) / 0.05);
    const band = SMOOTH((y - 1.01) / 0.05) * SMOOTH((1.43 - y) / 0.05);
    const core = SMOOTH((0.125 - ax) / 0.03);          // dreptul abdominal
    const flank = 0.45 * SMOOTH((0.21 - ax) / 0.05);   // oblicii
    return front * band * Math.max(core, flank);
  },
  camera: '34',
  views: {
    '34': { pos: [-2.9, 1.5, 2.9], target: [0, 0.4, 0.0] },
    side: { pos: [-4.4, 0.95, 0.15], target: [0, 0.5, 0.1] },
    front: { pos: [0.1, 1.25, 4.4], target: [0, 0.45, -0.05] },
  },
  tags: ['Abdomen', 'Greutatea corpului', 'La sol', 'Cu saltea'],
  steps: [
    'Culcă-te pe spate pe saltea, cu genunchii îndoiți și tălpile pe podea, la distanță de fese.',
    'Pune mâinile la ceafă, cu coatele depărtate. Nu trage de cap cu mâinile.',
    'Expiră și rulează trunchiul în sus, vertebră cu vertebră, până la aproximativ trei sferturi din drum.',
    'Ține o clipă sus, cu abdomenul strâns, apoi coboară încet, fără să te lași pe spate dintr-odată.',
  ],
  muscles: [
    ['Drept abdominal', 'p'],
    ['Oblic extern și intern', 's'],
    ['Flexori ai șoldului (iliopsoas)', 's'],
    ['Transvers abdominal (stabilizare)', 's'],
  ],
  phases: [
    { from: 0.00, to: 0.10, label: 'Culcat' },
    { from: 0.10, to: 0.40, label: 'Urcare · trunchiul se rulează' },
    { from: 0.40, to: 0.56, label: 'Sus · abdomenul strâns' },
    { from: 0.56, to: 1.00, label: 'Coborâre controlată' },
  ],
  gauge: { lo: 0, hi: 180, min: 0, max: 75, ends: ['podea', ''], signed: false,
    label: () => 'Trunchi față de podea' },
  effort(t) { return Math.min(1, 0.3 + keys(CURL, t) / 128 * 0.75); },
  // unghiul real al liniei șold → gât față de podea, citit din schelet
  angle(t, rig) {
    if (!rig) return 0;
    const h = rig.pos('hips'), n = rig.pos('neck');
    return THREE.MathUtils.radToDeg(Math.atan2(n.y - h.y, -(n.z - h.z)));
  },
  pose(rig, t, time) {
    lyingPose(rig, keys(CURL, t), time);
  },
};

export const ANIMATIONS = { '0001': ex0001, '6268': ex6268 };
