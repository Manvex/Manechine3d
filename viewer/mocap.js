// Animații generate automat: scheletul extras din clip (MediaPipe Pose) este aplicat pe manechin.
// Datele vin din viewer/mocap/ (vezi tools/extract_poses.py și tools/pack_mocap.py).
import * as THREE from 'three';

const J = { nose: 0, lear: 1, rear: 2, lsho: 3, rsho: 4, lelb: 5, relb: 6, lwri: 7, rwri: 8, lidx: 9, ridx: 10,
  lhip: 11, rhip: 12, lknee: 13, rknee: 14, lank: 15, rank: 16, lheel: 17, rheel: 18, ltoe: 19, rtoe: 20, root: 21 };
const SUPPORT = [J.lsho, J.rsho, J.lhip, J.rhip, J.lknee, J.rknee, J.lheel, J.rheel, J.ltoe, J.rtoe, J.lwri, J.rwri, J.lelb, J.relb];
const X = new THREE.Vector3(1, 0, 0);

let indexPromise = null;
const chunks = new Map();

export function loadIndex(cfg) {
  if (!indexPromise) indexPromise = fetch(cfg.mocap + 'index.json').then((r) => (r.ok ? r.json() : null)).catch(() => null);
  return indexPromise;
}

async function loadChunk(cfg, n) {
  if (!chunks.has(n)) chunks.set(n, (async () => {
    const name = `${cfg.mocap}c${String(n).padStart(3, '0')}.dat`;
    let bytes;
    if (cfg.b64) {
      const bin = atob((await (await fetch(name + '.txt')).text()).trim());
      bytes = new Uint8Array(bin.length);
      for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    } else bytes = new Uint8Array(await (await fetch(name)).arrayBuffer());
    const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
    return new Int16Array(await new Response(stream).arrayBuffer());
  })());
  return chunks.get(n);
}

// Decodează un clip: diferențe → poziții, mm → m, axele camerei → axele scenei (Y sus, Z spre cameră).
function decode(data, rows, off, n) {
  const w = rows * 3, f = new Float32Array(n * w), acc = new Int16Array(w);
  for (let i = 0; i < n; i++) {
    for (let k = 0; k < w; k++) {
      acc[k] = i === 0 ? data[(off + i) * w + k] : acc[k] + data[(off + i) * w + k];
      const axis = k % 3, isRoot = k >= J.root * 3;
      f[i * w + k] = acc[k] / 1000 * (isRoot ? (axis === 1 ? -1 : 1) : (axis === 0 ? 1 : -1));
    }
  }
  return f;
}

// Cadrele în care detecția a fost slabă se înlocuiesc cu cel mai apropiat cadru bun,
// apoi un filtru median scoate salturile izolate.
function cleanFrames(f, n, w) {
  const vis = Array.from({ length: n }, (_, i) => f[i * w + J.root * 3 + 2]);
  const med = [...vis].sort((a, b) => a - b)[n >> 1];
  const good = vis.map((v) => v >= 0.6 * med);
  for (let i = 0; i < n; i++) {
    if (good[i]) continue;
    for (let d = 1; d < n; d++) {
      const j = good[(i + d) % n] ? (i + d) % n : good[(i - d + n) % n] ? (i - d + n) % n : -1;
      if (j >= 0) { f.copyWithin(i * w, j * w, j * w + w); break; }
    }
  }
  const out = new Float32Array(f.length);
  for (let i = 0; i < n; i++) {
    const a = ((i - 1 + n) % n) * w, b = i * w, c = ((i + 1) % n) * w;
    for (let k = 0; k < w; k++) {
      const x = f[a + k], y = f[b + k], z = f[c + k];
      out[b + k] = Math.max(Math.min(x, y), Math.min(Math.max(x, y), z));
    }
  }
  return out;
}

// Netezire în timp (ciclică), ca să dispară tremuratul detecției.
function smoothFrames(f, n, w, passes = 3) {
  let a = f;
  for (let p = 0; p < passes; p++) {
    const b = new Float32Array(a.length);
    for (let i = 0; i < n; i++) {
      const i0 = ((i - 1 + n) % n) * w, i1 = i * w, i2 = ((i + 1) % n) * w;
      for (let k = 0; k < w; k++) b[i1 + k] = 0.25 * a[i0 + k] + 0.5 * a[i1 + k] + 0.25 * a[i2 + k];
    }
    a = b;
  }
  return a;
}

// Camera din clip privește de obicei ușor de sus. Căutăm înclinarea care aduce punctele de sprijin
// (cele mai joase 4 articulații din fiecare cadru) la aceeași înălțime, adică pe podea.
function estimatePitch(f, n, w) {
  let best = 0, bestCost = Infinity;
  const h = new Float32Array(SUPPORT.length);
  for (let deg = -16; deg <= 48; deg += 2) {
    const c = Math.cos(deg * Math.PI / 180), s = Math.sin(deg * Math.PI / 180);
    let cost = 0;
    for (let i = 0; i < n; i++) {
      const o = i * w;
      SUPPORT.forEach((j, q) => { h[q] = f[o + j * 3 + 1] * c - f[o + j * 3 + 2] * s; });
      const sorted = Array.from(h).sort((a, b) => a - b);
      cost += sorted[3] - sorted[0];
    }
    cost = cost / n + 0.0006 * Math.abs(deg);
    if (cost < bestCost) { bestCost = cost; best = deg; }
  }
  return best;
}

function applyPitch(f, n, w, deg) {
  const c = Math.cos(deg * Math.PI / 180), s = Math.sin(deg * Math.PI / 180);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < J.root; j++) {
      const o = i * w + j * 3, y = f[o + 1], z = f[o + 2];
      f[o + 1] = y * c - z * s; f[o + 2] = y * s + z * c;
    }
    // din deplasarea rădăcinii păstrăm doar componenta laterală (mers, fandări); înălțimea vine din contactul cu podeaua
    const o = i * w + J.root * 3;
    f[o] = Math.max(-1.2, Math.min(1.2, f[o])); f[o + 1] = 0; f[o + 2] = 0;
  }
}

const _v = Array.from({ length: 22 }, () => new THREE.Vector3());
const _m = new THREE.Matrix4();
function basisQuat(xDir, upDir) {
  const x = xDir.clone().normalize();
  const z = x.clone().cross(upDir).normalize();
  const y = z.clone().cross(x);
  return new THREE.Quaternion().setFromRotationMatrix(_m.makeBasis(x, y, z));
}

function applyPose(rig, P) {
  const mid = (a, b) => P[a].clone().add(P[b]).multiplyScalar(0.5);
  const hipMid = mid(J.lhip, J.rhip), shMid = mid(J.lsho, J.rsho), earMid = mid(J.lear, J.rear);
  const up = shMid.clone().sub(hipMid);
  const qHips = basisQuat(P[J.lhip].clone().sub(P[J.rhip]), up);
  const qChest = basisQuat(P[J.lsho].clone().sub(P[J.rsho]), up);
  rig.setW('hips', qHips);
  rig.setW('spine', qHips.clone().slerp(qChest, 0.33));
  rig.setW('spine2', qHips.clone().slerp(qChest, 0.66));
  rig.setW('chest', qChest);

  // cap: axa urechilor + direcția nasului
  const earX = P[J.lear].clone().sub(P[J.rear]);
  const fwd = P[J.nose].clone().sub(earMid);
  if (earX.lengthSq() > 1e-6 && fwd.lengthSq() > 1e-6) {
    const x = earX.normalize(), y = fwd.clone().cross(x).normalize(), z = x.clone().cross(y);
    const qHead = new THREE.Quaternion().setFromRotationMatrix(_m.makeBasis(x, y, z));
    // nasul stă puțin sub linia urechilor: corecție de ~15° ca privirea să fie dreaptă
    qHead.multiply(new THREE.Quaternion().setFromAxisAngle(X, -0.26));
    rig.setW('neck', qChest.clone().slerp(qHead, 0.5));
    rig.setW('head', qHead);
  }

  for (const [s, sh, el, wr, ix, hp, kn, an, toe] of [
    ['L', J.lsho, J.lelb, J.lwri, J.lidx, J.lhip, J.lknee, J.lank, J.ltoe],
    ['R', J.rsho, J.relb, J.rwri, J.ridx, J.rhip, J.rknee, J.rank, J.rtoe]]) {
    rig.aim(`${s}_upperarm`, `${s}_forearm`, P[el].clone().sub(P[sh]));
    rig.aim(`${s}_forearm`, `${s}_hand`, P[wr].clone().sub(P[el]));
    rig.aim(`${s}_hand`, `${s}_grip`, P[ix].clone().sub(P[wr]));

    const tDir = P[kn].clone().sub(P[hp]).normalize(), sDir = P[an].clone().sub(P[kn]).normalize();
    rig.aim(`${s}_thigh`, `${s}_shin`, tDir);
    // răsucirea coapsei: balamaua genunchiului se aliniază cu planul în care se îndoaie piciorul
    const hinge = tDir.clone().cross(sDir);
    const bend = hinge.length();
    if (bend > 0.2) {
      const cur = rig.axis(`${s}_thigh`, X);
      cur.addScaledVector(tDir, -cur.dot(tDir)).normalize();
      hinge.normalize();
      const ang = Math.atan2(cur.clone().cross(hinge).dot(tDir), cur.dot(hinge));
      rig.rotW(`${s}_thigh`, tDir, ang * Math.min(1, (bend - 0.2) / 0.3));
    }
    rig.aim(`${s}_shin`, `${s}_foot`, sDir);
    rig.aim(`${s}_foot`, `${s}_toes`, P[toe].clone().sub(P[an]));
  }
}

const GROUND_BONES = ['hips', 'chest', 'head', 'L_shin', 'R_shin', 'L_foot', 'R_foot', 'L_toes', 'R_toes', 'L_hand', 'R_hand', 'L_forearm', 'R_forearm', 'L_upperarm', 'R_upperarm'];
const PAD = { hips: 0.13, chest: 0.12, head: 0.1, L_foot: 0.09, R_foot: 0.09, L_toes: 0.02, R_toes: 0.02 };

export async function loadMocap(cfg, ex) {
  const index = await loadIndex(cfg);
  const entry = index && index.clips[ex[0]];
  if (!entry) return null;
  const [chunk, off, n] = entry;
  const rows = index.rows, w = rows * 3;
  let f = smoothFrames(cleanFrames(decode(await loadChunk(cfg, chunk), rows, off, n), n, w), n, w);
  applyPitch(f, n, w, estimatePitch(f, n, w));

  const duration = n / index.fps;
  const ground = new WeakMap();   // rig → pentru fiecare cadru, înălțimea care pune cel mai jos punct pe podea
  const sample = (t) => {
    const x = t * n, i0 = Math.floor(x) % n, i1 = (i0 + 1) % n, k = x - Math.floor(x);
    for (let j = 0; j < rows; j++) {
      const a = i0 * w + j * 3, b = i1 * w + j * 3;
      _v[j].set(f[a] + (f[b] - f[a]) * k, f[a + 1] + (f[b + 1] - f[a + 1]) * k, f[a + 2] + (f[b + 2] - f[a + 2]) * k);
    }
    return _v;
  };
  const poseAt = (rig, t, lift) => {
    const P = sample(t);
    applyPose(rig, P);
    rig.b.hips.position.set(P[J.root].x, lift, 0);
  };
  const groundFor = (rig) => {
    let lifts = ground.get(rig);
    if (lifts) return lifts;
    lifts = new Float32Array(n);
    for (let i = 0; i < n; i++) {
      rig.reset();
      poseAt(rig, i / n, 0);
      rig.root.updateMatrixWorld(true);
      let low = Infinity;
      for (const b of GROUND_BONES) low = Math.min(low, rig.pos(b).y - (PAD[b] ?? 0.05));
      lifts[i] = -low;
    }
    lifts = smoothFrames(lifts, n, 1, 4);
    ground.set(rig, lifts);
    rig.reset();
    return lifts;
  };

  return {
    id: ex[0], auto: true, duration, phases: [], ring: true,
    camera: '34',
    views: {
      '34': { pos: [2.2, 1.5, 4.2], target: [0, 0.8, 0] },
      side: { pos: [4.6, 1.1, 0.2], target: [0, 0.8, 0] },
      front: { pos: [0, 1.2, 4.9], target: [0, 0.8, 0] },
    },
    tags: [ex[3], 'Generat automat din clip'].filter(Boolean),
    steps: ['Mișcarea este extrasă automat din clipul de referință și aplicată pe manechin. Echipamentul nu este afișat, iar detaliile fine (mâini, răsuciri) pot fi aproximative.'],
    muscles: [],
    effort() { return 0; },
    pose(rig, t) {
      const lifts = groundFor(rig);
      const x = t * n, i0 = Math.floor(x) % n, i1 = (i0 + 1) % n, k = x - Math.floor(x);
      poseAt(rig, t, lifts[i0] + (lifts[i1] - lifts[i0]) * k);
    },
  };
}
