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

// Mâinile la ceafă, coatele depărtate (IK pe umăr–cot–încheietură). Merge în orice poziție a corpului.
export function handsBehindHead(rig) {
  const headQ = rig.quat('head'), chestQ = rig.quat('chest');
  const headPos = rig.pos('head');
  for (const [side, sx] of [['R', -1], ['L', 1]]) {
    const wrist = headPos.clone().add(new THREE.Vector3(sx * 0.118, 0.05, -0.075).applyQuaternion(headQ));
    const pole = new THREE.Vector3(sx, 0, 0.45).applyQuaternion(chestQ);
    rig.ik2(`${side}_upperarm`, `${side}_forearm`, `${side}_hand`, wrist, pole);
    const mid = headPos.clone().add(new THREE.Vector3(0, 0.04, -0.105).applyQuaternion(headQ));
    rig.aim(`${side}_hand`, `${side}_grip`, mid.sub(rig.pos(`${side}_hand`)));
    grip(rig, side, D(-18), -0.4);
  }
}

// 0001 — 3/4 Sit up
// Culcat pe spate, genunchii îndoiți, tălpile pe saltea, mâinile la ceafă. Trunchiul se
// rulează în sus cam trei sferturi din drum, ține o clipă, apoi coboară încet.
const MAT_TOP = 0.03;
// bazinul stă pe saltea: spatele (măsurat pe model) atinge suprafața
const matHipHeight = (rig) => MAT_TOP + rig.info.back + 0.011;
const CURL = [ // [timp în ciclu, îndoire totală a coloanei în grade]
  [0.00, 0], [0.10, 0],       // culcat
  [0.40, 128],                // urcare
  [0.56, 128],                // sus
  [0.92, 0], [1.00, 0],       // coborâre controlată
];
const SMOOTH = (x) => Math.min(1, Math.max(0, x));

// Tălpile plate pe saltea, genunchii îndoiți: IK pe șold–genunchi–gleznă. `dz` = cât în fața șoldului stau gleznele.
// Întoarce pozițiile gleznelor, ca mâinile să poată ajunge la călcâie.
function feetOnMat(rig, dz) {
  const ankles = {};
  for (const [side, sx] of [['R', -1], ['L', 1]]) {
    const hip = rig.pos(`${side}_thigh`);
    const ankle = new THREE.Vector3(hip.x + sx * 0.012, MAT_TOP + rig.info.ankleY + 0.003, hip.z + dz);
    rig.ik2(`${side}_thigh`, `${side}_shin`, `${side}_foot`, ankle, new THREE.Vector3(sx * 0.12, 1, 0));
    rig.setRestW(`${side}_foot`); // talpa rămâne paralelă cu podeaua
    ankles[side] = ankle;
  }
  return ankles;
}

function lyingPose(rig, curlDeg, time) {
  const F = D(curlDeg);
  const breath = Math.sin(time * Math.PI * 2 / 4.2);

  // culcat pe spate: fața în sus, capul spre −Z, bazinul pe saltea
  rig.rotW('hips', X, D(-90));
  rig.b.hips.position.set(0, matHipHeight(rig), 0.16);

  // trunchiul se rulează vertebră cu vertebră; cea mai mare parte a mișcării e în zona lombară
  rig.rotW('spine', X, F * 0.40);
  rig.rotW('spine2', X, F * 0.31);
  rig.rotW('chest', X, F * 0.17 + D(0.8) * breath);
  rig.rotW('neck', X, F * 0.06);
  rig.rotW('head', X, F * 0.05 + D(4));

  // picioare: tălpile plate pe saltea, genunchii îndoiți
  feetOnMat(rig, 0.44);

  handsBehindHead(rig);
}

export const ex0001 = {
  id: '0001',
  duration: 5.2,
  mat: true,
  // abdomenul din față: fâșie centrală (dreptul abdominal) și părțile laterale (oblicii)
  muscleMask(x, y, z, m) {
    const ax = Math.abs(x) / m.w, u = (y - m.hipsY) / m.L;   // u: 0 la șold, 1 la gât
    const front = SMOOTH((z + 0.01) / 0.05);
    const band = SMOOTH((u + 0.045) / 0.1) * SMOOTH((0.777 - u) / 0.1);
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

// 0002 — 45 degrees Side Bend
// Pe banca de hiperextensii înclinată la 45°, culcat pe o parte: șoldul pe pad, picioarele drepte
// pe placa pentru tălpi, mâinile la ceafă. Trunchiul se îndoaie lateral în planul frontal,
// de la ~30° spre bancă până la ~30° în sus față de linia corpului.
const BENCH_UP = new THREE.Vector3(0, Math.SQRT1_2, -Math.SQRT1_2);   // de la picioare spre cap, pe șina băncii
const BENCH_N = new THREE.Vector3(0, Math.SQRT1_2, Math.SQRT1_2);     // normala padului, spre persoană
// baza corpului: stânga manechinului spre pad, capul în sus pe șină, fața spre +X
const LYING_SIDE_Q = new THREE.Quaternion().setFromRotationMatrix(
  new THREE.Matrix4().makeBasis(BENCH_N.clone().negate(), BENCH_UP, new THREE.Vector3(1, 0, 0)));
const BENCH_PAD = new THREE.Vector3(0, 0.86, 0.019);                  // `anchor_hip_pad` din modelul băncii
const HIP_OFFSET = 0.17;                                              // jumătate din lățimea bazinului (manechin bărbat)
const FOOT_SLIDE = -0.056;                                            // placa pentru tălpi, de-a lungul șinei (manechin bărbat)
const MALE_HIPS_Y = 1.033;

const BEND = [ // [timp în ciclu, îndoire laterală în grade; − spre bancă, + în sus]
  [0.00, -34], [0.14, -34],
  [0.46, 30],
  [0.58, 30],
  [0.92, -34], [1.00, -34],
];

export const ex0002 = {
  id: '0002',
  duration: 5.9,
  ring: false,
  equipment: [{
    url: 'echipamente/glb/hyperextension_45.glb',
    attach: null,
    finish: 'bench',
    // placa pentru tălpi se mută după lungimea piciorului: un picior mai scurt cere placa mai sus pe șină
    adjust(obj, rig) {
      obj.getObjectByName('joint_foot_adjust')?.position
        .addScaledVector(BENCH_UP, FOOT_SLIDE + (MALE_HIPS_Y - rig.info.hipsY));
    },
  }],
  // flancurile: oblicii în față și pe lateral, ușor și dreptul abdominal
  muscleMask(x, y, z, m) {
    const ax = Math.abs(x) / m.w, u = (y - m.hipsY) / m.L;
    const front = SMOOTH((z + 0.05) / 0.06);
    const band = SMOOTH((u + 0.025) / 0.1) * SMOOTH((0.72 - u) / 0.1);
    const flank = SMOOTH((ax - 0.06) / 0.04) * SMOOTH((0.25 - ax) / 0.04);
    const core = 0.3 * SMOOTH((0.1 - ax) / 0.03);
    return front * band * Math.max(flank, core);
  },
  camera: '34',
  views: {
    '34': { pos: [3.3, 1.55, 2.9], target: [0, 0.62, 0.1] },
    side: { pos: [0.3, 1.15, 4.7], target: [0, 0.62, 0.1] },
    front: { pos: [4.7, 0.95, 0.15], target: [0, 0.65, 0.1] },
  },
  tags: ['Abdomen', 'Oblici', 'Banc 45°', 'Mâini la ceafă'],
  steps: [
    'Așază-te lateral pe banca înclinată la 45°, cu șoldul pe pad și picioarele drepte, fixate pe placa pentru tălpi.',
    'Pune mâinile la ceafă, cu coatele depărtate. Corpul face o linie dreaptă de la glezne până la cap.',
    'Coboară trunchiul lateral, spre bancă, doar din talie. Nu roti umerii.',
    'Ridică trunchiul îndoindu-te lateral, până treci puțin de linia corpului. Strânge flancul.',
    'Coboară controlat și repetă. Schimbă partea după ce termini setul.',
  ],
  muscles: [
    ['Oblic extern și intern', 'p'],
    ['Pătrat lombar', 'p'],
    ['Drept abdominal', 's'],
    ['Erectori spinali (stabilizare)', 's'],
  ],
  phases: [
    { from: 0.00, to: 0.14, label: 'Jos · spre bancă' },
    { from: 0.14, to: 0.46, label: 'Ridicare · îndoire laterală' },
    { from: 0.46, to: 0.58, label: 'Sus · flancul strâns' },
    { from: 0.58, to: 1.00, label: 'Coborâre controlată' },
  ],
  gauge: { lo: -45, hi: 45, min: -34, max: 30, ends: ['spre bancă', 'în sus'],
    label: (v) => v >= 0 ? 'Îndoire în sus' : 'Îndoire spre bancă' },
  effort(t) { return 0.35 + 0.65 * (keys(BEND, t) + 34) / 64; },
  angle(t) { return keys(BEND, t); },
  pose(rig, t, time) {
    const a = D(keys(BEND, t));
    const breath = Math.sin(time * Math.PI * 2 / 4.2);
    // pe bancă: șoldul pe pad, corpul pe șină
    rig.setW('hips', LYING_SIDE_Q);
    rig.b.hips.position.copy(BENCH_PAD)
      .addScaledVector(BENCH_N, HIP_OFFSET * rig.info.w)
      .addScaledVector(BENCH_UP, 0.057);
    // îndoire laterală în jurul axei înainte a persoanei (+X în lume)
    rig.rotW('spine', X, a * 0.36);
    rig.rotW('spine2', X, a * 0.30);
    rig.rotW('chest', X, a * 0.24 + D(0.5) * breath);
    rig.rotW('neck', X, a * 0.07);
    rig.rotW('head', X, a * 0.03);
    handsBehindHead(rig);
  },
};

// 0003 — Air Bike (male)
// Crunch „pedalat”: culcat pe spate, mâinile la ceafă, picioarele ridicate de la sol. Un genunchi
// vine spre piept, celălalt picior se întinde, iar trunchiul se rulează și se răsucește ca să
// aducă cotul opus spre genunchi. Picioarele se schimbă continuu, în antifază.
const lerp = (a, b, k) => a + (b - a) * k;
const BIKE = { hipOut: 28, hipIn: 100, kneeOut: 6, kneeIn: 122, flexMin: 24, flexMax: 64, twist: 36 };

// 0 = piciorul întins, 1 = genunchiul la piept. În antifază pentru cele două picioare.
function bikeLeg(t, side) {
  const q = Math.sin(Math.PI * 2 * t);
  return smooth(0.5 + 0.5 * q * (side === 'R' ? 1 : -1));
}

export const ex0003 = {
  id: '0003',
  duration: 6.4,
  mat: true,
  muscleMask: ex0001.muscleMask,
  camera: '34',
  views: {
    '34': { pos: [-3.2, 1.6, 3.1], target: [0, 0.4, 0.15] },
    side: { pos: [-4.8, 1.0, 0.2], target: [0, 0.45, 0.2] },
    front: { pos: [0.2, 1.4, 4.8], target: [0, 0.45, 0.0] },
  },
  tags: ['Abdomen', 'Greutatea corpului', 'La sol', 'Cu saltea'],
  steps: [
    'Culcă-te pe spate pe saltea, cu mâinile la ceafă și coatele depărtate. Ridică ambele picioare de la sol.',
    'Adu un genunchi spre piept și întinde complet celălalt picior, ținut sus, la circa 30° față de podea.',
    'Rotește trunchiul și apropie cotul opus de genunchiul ridicat. Umărul rămâne desprins de pe saltea.',
    'Schimbă picioarele într-o mișcare continuă, ca la pedalat. Nu trage de cap cu mâinile.',
  ],
  muscles: [
    ['Drept abdominal', 'p'],
    ['Oblic extern și intern', 'p'],
    ['Flexori ai șoldului (iliopsoas)', 's'],
    ['Cvadriceps (drept femural)', 's'],
  ],
  phases: [
    { from: 0.00, to: 0.12, label: 'Schimbare · picioarele se încrucișează' },
    { from: 0.12, to: 0.38, label: 'Genunchi drept · cot stâng spre el' },
    { from: 0.38, to: 0.62, label: 'Schimbare · picioarele se încrucișează' },
    { from: 0.62, to: 0.88, label: 'Genunchi stâng · cot drept spre el' },
    { from: 0.88, to: 1.00, label: 'Schimbare · picioarele se încrucișează' },
  ],
  gauge: { lo: -45, hi: 45, min: -BIKE.twist, max: BIKE.twist, ends: ['genunchi stâng', 'genunchi drept'],
    label: (v) => 'Răsucire spre genunchiul ' + (v >= 0 ? 'drept' : 'stâng') },
  effort(t) { const q = Math.sin(Math.PI * 2 * t); return 0.45 + 0.55 * q * q; },
  angle(t) { return BIKE.twist * Math.sin(Math.PI * 2 * t); },
  pose(rig, t, time) {
    const q = Math.sin(Math.PI * 2 * t);
    const F = D(lerp(BIKE.flexMin, BIKE.flexMax, q * q));   // cât se rulează trunchiul
    const psi = D(-BIKE.twist * q);                          // răsucirea, spre genunchiul adus
    const breath = Math.sin(time * Math.PI * 2 / 4.2);

    rig.rotW('hips', X, D(-90));
    rig.b.hips.position.set(0, matHipHeight(rig), 0.16);

    // trunchi: rulare + răsucire în jurul axei lungi, repartizate pe coloană
    for (const [bone, kf, kt] of [['spine', 0.34, 0.18], ['spine2', 0.30, 0.32], ['chest', 0.24, 0.38], ['neck', 0.07, 0.12], ['head', 0.05, 0]]) {
      rig.rotW(bone, X, F * kf + (bone === 'chest' ? D(0.6) * breath : 0));
      rig.rotW(bone, rig.axis(bone, Y), psi * kt);
    }

    // picioare: șold și genunchi, în antifază
    for (const side of ['R', 'L']) {
      const u = bikeLeg(t, side);
      rig.rotW(`${side}_thigh`, X, D(-lerp(BIKE.hipOut, BIKE.hipIn, u)));
      rig.rotW(`${side}_shin`, X, D(lerp(BIKE.kneeOut, BIKE.kneeIn, u)));
    }

    handsBehindHead(rig);
  },
};

// 0004 — Air Twisting Crunch (female)
// Culcată pe spate, genunchii îndoiți, ambele tălpi pe saltea, mâinile la ceafă. La fiecare repetare
// un picior se ridică (genunchiul spre piept, gamba orizontală) în timp ce trunchiul se rulează și
// se răsucește, ca cotul opus să vină spre genunchi. Cealaltă talpă rămâne pe saltea. Apoi coboară
// și se repetă cu celălalt picior.
const TWIST = { flexLow: 6, flexHigh: 56, twist: 32, plantDz: 0.42, cross: 0.1 };
const CRUNCH = [[0, 0], [0.06, 0], [0.34, 1], [0.6, 1], [0.92, 0], [1, 0]];   // o repetare

// gradul de crunch (0..1) și partea: +1 = genunchiul drept urcă, −1 = genunchiul stâng
function twistState(t) {
  const half = t < 0.5 ? 0 : 1;
  return { k: keys(CRUNCH, (t - half * 0.5) * 2), side: half === 0 ? 1 : -1 };
}

export const ex0004 = {
  id: '0004',
  duration: 7.0,
  mat: true,
  muscleMask: ex0002.muscleMask,
  camera: '34',
  views: ex0003.views,
  tags: ['Abdomen', 'Oblici', 'Greutatea corpului', 'Cu saltea'],
  steps: [
    'Culcă-te pe spate pe saltea, cu genunchii îndoiți și tălpile pe podea. Mâinile stau ușor la ceafă, coatele depărtate.',
    'Expiră și ridică un picior, cu genunchiul spre piept și gamba paralelă cu podeaua. În același timp rulează umerii de pe saltea.',
    'Răsucește trunchiul ca să apropii cotul opus de genunchiul ridicat. Ține o clipă, fără să tragi de gât.',
    'Coboară controlat, cu talpa înapoi pe saltea. Repetă cu celălalt picior și răsucire spre cealaltă parte.',
  ],
  muscles: [
    ['Oblic extern și intern', 'p'],
    ['Drept abdominal', 's'],
    ['Flexori ai șoldului (iliopsoas)', 's'],
  ],
  phases: [
    { from: 0.00, to: 0.17, label: 'Urcare · genunchiul drept spre cotul stâng' },
    { from: 0.17, to: 0.30, label: 'Sus · cot la genunchi' },
    { from: 0.30, to: 0.50, label: 'Coborâre · talpa înapoi pe saltea' },
    { from: 0.50, to: 0.67, label: 'Urcare · genunchiul stâng spre cotul drept' },
    { from: 0.67, to: 0.80, label: 'Sus · cot la genunchi' },
    { from: 0.80, to: 1.00, label: 'Coborâre · talpa înapoi pe saltea' },
  ],
  gauge: { lo: -45, hi: 45, min: -TWIST.twist, max: TWIST.twist, ends: ['stânga', 'dreapta'],
    label: (v) => 'Răsucire spre ' + (v >= 0 ? 'dreapta' : 'stânga') },
  effort(t) { return 0.35 + 0.65 * twistState(t).k; },
  angle(t) { const { k, side } = twistState(t); return TWIST.twist * side * k; },
  pose(rig, t, time) {
    const { k, side } = twistState(t);
    const F = D(lerp(TWIST.flexLow, TWIST.flexHigh, k));
    const psi = D(-TWIST.twist * side * k);
    const breath = Math.sin(time * Math.PI * 2 / 4.2);

    rig.rotW('hips', X, D(-90));
    rig.b.hips.position.set(0, matHipHeight(rig), 0.16);

    for (const [bone, kf, kt] of [['spine', 0.34, 0.18], ['spine2', 0.30, 0.32], ['chest', 0.24, 0.38], ['neck', 0.07, 0.12], ['head', 0.05, 0]]) {
      rig.rotW(bone, X, F * kf + (bone === 'chest' ? D(0.6) * breath : 0));
      rig.rotW(bone, rig.axis(bone, Y), psi * kt);
    }

    // picioare: amândouă pe saltea; piciorul care lucrează urcă spre piept și trece ușor spre mijloc
    const lift = side === 1 ? 'R' : 'L';
    for (const [s, sx] of [['R', -1], ['L', 1]]) {
      const hip = rig.pos(`${s}_thigh`);
      const planted = new THREE.Vector3(hip.x + sx * 0.012, MAT_TOP + rig.info.ankleY + 0.003, hip.z + TWIST.plantDz);
      const w = s === lift ? smooth(k) : 0;
      let target = planted, pole = new THREE.Vector3(sx * 0.12, 1, 0);
      if (w > 0) {
        const l1 = hip.distanceTo(rig.pos(`${s}_shin`)), l2 = rig.pos(`${s}_shin`).distanceTo(rig.pos(`${s}_foot`));
        // sus: coapsa verticală, gamba orizontală, genunchiul ușor spre mijloc
        const air = new THREE.Vector3(hip.x - sx * TWIST.cross, hip.y + 0.92 * l1, hip.z + 0.95 * l2);
        target = planted.clone().lerp(air, w);
        pole = pole.lerp(new THREE.Vector3(-sx * 0.2, 1, -0.4), w);
      }
      rig.ik2(`${s}_thigh`, `${s}_shin`, `${s}_foot`, target, pole);
      // talpa plată pe saltea; în aer laba urmează gamba
      const qFoot = rig.restWorld[`${s}_foot`].clone().slerp(rig.quat(`${s}_foot`), w);
      rig.setW(`${s}_foot`, qFoot);
    }

    handsBehindHead(rig);
  },
};

// 0006 — Alternate Heel Touchers
// Culcat pe spate, genunchii îndoiți, tălpile pe saltea, brațele pe lângă corp. Umerii stau ușor
// ridicați, iar trunchiul se îndoaie lateral, pe rând spre fiecare parte, ca mâna să alunece
// spre călcâiul de pe aceeași parte.
const HEEL = { flex: 26, lateral: 36 };
const HEEL_LAT = (t) => Math.sin(Math.PI * 2 * t);   // + spre dreapta, − spre stânga

export const ex0006 = {
  id: '0006',
  duration: 6.4,
  mat: true,
  muscleMask: ex0002.muscleMask,
  camera: '34',
  views: {
    '34': { pos: [-2.8, 1.9, 3.0], target: [0, 0.35, 0.1] },
    side: { pos: [-4.6, 1.0, 0.2], target: [0, 0.4, 0.15] },
    front: { pos: [0.2, 2.3, 3.9], target: [0, 0.3, -0.05] },
  },
  tags: ['Abdomen', 'Oblici', 'Greutatea corpului', 'Cu saltea'],
  steps: [
    'Culcă-te pe spate pe saltea, cu genunchii îndoiți și tălpile pe podea, brațele întinse pe lângă corp.',
    'Ridică ușor umerii de pe saltea și ține abdomenul încordat.',
    'Îndoaie trunchiul lateral și alunecă mâna spre călcâiul de pe aceeași parte.',
    'Revino prin centru și repetă spre cealaltă parte. Umerii nu ating salteaua între repetări.',
  ],
  muscles: [
    ['Oblic extern și intern', 'p'],
    ['Pătrat lombar', 's'],
    ['Drept abdominal', 's'],
  ],
  phases: [
    { from: 0.00, to: 0.10, label: 'Trecere prin centru' },
    { from: 0.10, to: 0.40, label: 'Spre dreapta · mâna spre călcâi' },
    { from: 0.40, to: 0.60, label: 'Trecere prin centru' },
    { from: 0.60, to: 0.90, label: 'Spre stânga · mâna spre călcâi' },
    { from: 0.90, to: 1.00, label: 'Trecere prin centru' },
  ],
  gauge: { lo: -45, hi: 45, min: -HEEL.lateral, max: HEEL.lateral, ends: ['stânga', 'dreapta'],
    label: (v) => 'Îndoire spre ' + (v >= 0 ? 'dreapta' : 'stânga') },
  effort(t) { return 0.4 + 0.6 * Math.abs(HEEL_LAT(t)); },
  angle(t) { return HEEL.lateral * HEEL_LAT(t); },
  pose(rig, t, time) {
    const lat = HEEL_LAT(t);
    const F = D(HEEL.flex);
    const theta = D(HEEL.lateral * lat);
    const breath = Math.sin(time * Math.PI * 2 / 4.2);

    rig.rotW('hips', X, D(-90));
    rig.b.hips.position.set(0, matHipHeight(rig), 0.16);

    // umerii ridicați + îndoire laterală în jurul axei „înainte” a trunchiului (+ = spre dreapta)
    for (const [bone, kf, kl] of [['spine', 0.34, 0.30], ['spine2', 0.30, 0.34], ['chest', 0.24, 0.26], ['neck', 0.07, 0.07], ['head', 0.05, 0.03]]) {
      rig.rotW(bone, X, F * kf + (bone === 'chest' ? D(0.6) * breath : 0));
      rig.rotW(bone, rig.axis(bone, Z), theta * kl);
    }

    const ankles = feetOnMat(rig, 0.34);

    // brațe pe lângă corp; mâna de pe partea îndoită alunecă spre călcâi
    const hips = rig.pos('hips');
    for (const [side, sx] of [['R', -1], ['L', 1]]) {
      const w = smooth(Math.max(0, sx === -1 ? lat : -lat));
      const rest = new THREE.Vector3(hips.x + sx * 0.2 * rig.info.w, MAT_TOP + 0.05, hips.z + 0.1);
      const heel = new THREE.Vector3(ankles[side].x + sx * 0.1, MAT_TOP + 0.06, ankles[side].z - 0.1);
      const target = rest.lerp(heel, w);
      rig.ik2(`${side}_upperarm`, `${side}_forearm`, `${side}_hand`, target, new THREE.Vector3(sx, 0.6, 0));
      grip(rig, side, D(-38), -0.8);
    }
  },
};

// 0008 — Alternate Lying Floor Leg Raise
// Culcat pe spate, brațele pe lângă corp, picioarele întinse. Un picior urcă drept până la verticală,
// celălalt rămâne întins la câțiva centimetri deasupra solului (călcâiul nu atinge podeaua). Apoi
// se schimbă. Zona lombară stă lipită de saltea tot timpul; bazinul nu se mișcă.
const RAISE = [ // profilul unui picior pe jumătate de ciclu: [timp, cât de sus 0..1]
  [0.00, 0], [0.06, 0],
  [0.44, 1],
  [0.56, 1],
  [0.94, 0], [1.00, 0],
];
const LEG = { low: 5, top: 88 };   // flexia șoldului: picior „în aer” jos / vertical

// cât de sus e fiecare picior: dreptul în prima jumătate a ciclului, stângul în a doua
function legRaise(t) {
  return t < 0.5 ? { R: keys(RAISE, t * 2), L: 0 } : { R: 0, L: keys(RAISE, t * 2 - 1) };
}

export const ex0008 = {
  id: '0008',
  duration: 5.6,
  mat: true,
  // abdomenul inferior și fața coapselor (flexorii șoldului)
  muscleMask(x, y, z, m) {
    const ax = Math.abs(x) / m.w, u = (y - m.hipsY) / m.L;
    const s = m.hipsY / 1.033;
    const absLow = SMOOTH((z + 0.01) / 0.05) * SMOOTH((u + 0.045) / 0.1) * SMOOTH((0.42 - u) / 0.12) * SMOOTH((0.2 - ax) / 0.05);
    const thigh = 0.8 * SMOOTH((z - 0.02) / 0.04) * SMOOTH((m.hipsY - 0.03 - y) / 0.04) * SMOOTH((y - (m.hipsY - 0.5 * s)) / 0.06) * SMOOTH((0.22 - ax) / 0.05);
    return Math.max(absLow, thigh);
  },
  camera: '34',
  views: {
    '34': { pos: [-3.5, 1.6, 2.7], target: [0, 0.55, 0.15] },
    side: { pos: [-4.8, 0.95, 0.15], target: [0, 0.6, 0.15] },
    front: { pos: [0.2, 1.4, 4.8], target: [0, 0.55, 0.0] },
  },
  tags: ['Abdomen', 'Greutatea corpului', 'La sol', 'Alternativ'],
  steps: [
    'Culcă-te pe spate pe saltea, cu brațele pe lângă corp, palmele pe podea și picioarele întinse.',
    'Ridică ambele călcâie la câțiva centimetri de podea. Zona lombară rămâne lipită de saltea.',
    'Ridică un picior întins până la verticală, în timp ce celălalt rămâne jos, în aer, fără să atingă podeaua.',
    'Coboară piciorul încet până lângă celălalt, apoi ridică piciorul opus. Expiră la urcare, inspiră la coborâre.',
  ],
  muscles: [
    ['Drept abdominal (partea de jos)', 'p'],
    ['Flexori ai șoldului (iliopsoas)', 'p'],
    ['Cvadriceps (drept femural)', 's'],
    ['Transvers abdominal (stabilizare)', 's'],
  ],
  phases: [
    { from: 0.00, to: 0.22, label: 'Piciorul drept urcă · stângul în aer' },
    { from: 0.22, to: 0.28, label: 'Piciorul drept vertical' },
    { from: 0.28, to: 0.50, label: 'Piciorul drept coboară încet' },
    { from: 0.50, to: 0.72, label: 'Piciorul stâng urcă · dreptul în aer' },
    { from: 0.72, to: 0.78, label: 'Piciorul stâng vertical' },
    { from: 0.78, to: 1.00, label: 'Piciorul stâng coboară încet' },
  ],
  gauge: { lo: 0, hi: 180, min: 0, max: 92, ends: ['podea', ''], signed: false,
    label: () => 'Piciorul ridicat față de podea' },
  effort(t) { const r = legRaise(t); return 0.45 + 0.55 * Math.max(r.R, r.L); },
  // unghiul real al piciorului care lucrează, citit din schelet (șold → gleznă)
  angle(t, rig) {
    if (!rig) return 0;
    const side = t < 0.5 ? 'R' : 'L';
    const h = rig.pos(`${side}_thigh`), f = rig.pos(`${side}_foot`);
    return Math.max(0, THREE.MathUtils.radToDeg(Math.atan2(f.y - h.y, f.z - h.z)));
  },
  pose(rig, t, time) {
    const r = legRaise(t);
    const breath = Math.sin(time * Math.PI * 2 / 4.2);

    rig.rotW('hips', X, D(-90));
    rig.b.hips.position.set(0, matHipHeight(rig), 0.16);
    rig.rotW('chest', X, D(0.6) * breath);
    rig.rotW('head', X, D(3));

    // fiecare picior întins: doar flexie la șold, genunchiul aproape drept
    for (const side of ['R', 'L']) {
      rig.rotW(`${side}_thigh`, Y, D(2.5) * (side === 'R' ? 1 : -1));
      rig.rotW(`${side}_thigh`, X, D(-lerp(LEG.low, LEG.top, r[side])));
      rig.rotW(`${side}_shin`, X, D(2));
    }

    // brațe pe lângă corp, palmele pe saltea
    const hips = rig.pos('hips');
    for (const [side, sx] of [['R', -1], ['L', 1]]) {
      const target = new THREE.Vector3(hips.x + sx * 0.22 * rig.info.w, MAT_TOP + 0.045, hips.z + 0.2);
      rig.ik2(`${side}_upperarm`, `${side}_forearm`, `${side}_hand`, target, new THREE.Vector3(sx * 0.3, 1, 0));
      grip(rig, side, D(-38), -0.8);
    }
  },
};

export const ANIMATIONS = { '0001': ex0001, '0002': ex0002, '0003': ex0003, '0004': ex0004, '0006': ex0006, '0008': ex0008, '6268': ex6268 };
