import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { ANIMATIONS, idle } from './animations.js';

const CFG = Object.assign({ assets: '../', clips: null, catalog: 'exercises.json' }, window.MANECHIN || {});
const MODELS = { male: 'male-actual.glb', female: 'female-actual.glb' };
const DEFAULT_ID = '6268'; // ales la întâmplare din „clipuri de facut”
const PAGE = 120;
const $ = (id) => document.getElementById(id);
const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;

// ---------- rig ----------
class Rig {
  constructor(root) {
    this.root = root;
    this.b = {};
    this.rest = [];
    root.traverse((o) => {
      if (o.isBone) {
        this.b[o.name] = o;
        this.rest.push([o, o.quaternion.clone(), o.position.clone()]);
      }
    });
    this._q = new THREE.Quaternion();
    this._p = new THREE.Quaternion();
    this._r = new THREE.Quaternion();
    // orientările din poza de repaus, în spațiul lumii (pentru tălpi pe podea etc.)
    root.updateMatrixWorld(true);
    this.restWorld = {};
    for (const [o] of this.rest) this.restWorld[o.name] = o.getWorldQuaternion(new THREE.Quaternion());
  }
  reset() {
    for (const [o, q, p] of this.rest) { o.quaternion.copy(q); o.position.copy(p); }
  }
  // Aplică o rotație din spațiul lumii (cuaternion) osului, păstrând copiii atașați.
  rotQ(name, r) {
    const b = this.b[name];
    if (!b) return;
    b.parent.getWorldQuaternion(this._p);
    this._q.copy(this._p).multiply(b.quaternion);
    this._q.premultiply(r);
    b.quaternion.copy(this._p.invert().multiply(this._q));
  }
  // Rotește osul în jurul unei axe din spațiul lumii, păstrând copiii atașați.
  rotW(name, axis, angle) {
    if (!this.b[name] || !angle) return;
    this.rotQ(name, this._r.setFromAxisAngle(axis, angle));
  }
  pos(name) { return this.b[name].getWorldPosition(new THREE.Vector3()); }
  quat(name) { return this.b[name].getWorldQuaternion(new THREE.Quaternion()); }
  // Pune osul înapoi în orientarea lui de repaus din spațiul lumii (ex. talpa plată pe podea).
  setRestW(name) {
    const b = this.b[name];
    b.parent.getWorldQuaternion(this._p);
    b.quaternion.copy(this._p.invert().multiply(this.restWorld[name]));
  }
  // Rotește osul cel mai scurt drum, ca direcția spre copil să devină `dir` (în lumea reală).
  aim(name, child, dir) {
    const cur = this.pos(child).sub(this.pos(name)).normalize();
    this.rotQ(name, new THREE.Quaternion().setFromUnitVectors(cur, dir.clone().normalize()));
  }
  // IK pe două segmente (șold–genunchi–gleznă sau umăr–cot–încheietură). `pole` spune încotro stă articulația din mijloc.
  ik2(upper, mid, end, target, pole) {
    const a = this.pos(upper), b = this.pos(mid), c = this.pos(end);
    const l1 = a.distanceTo(b), l2 = b.distanceTo(c);
    const dir = target.clone().sub(a);
    const d = THREE.MathUtils.clamp(dir.length(), Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3);
    dir.normalize();
    const x = (l1 * l1 - l2 * l2 + d * d) / (2 * d);
    const h = Math.sqrt(Math.max(0, l1 * l1 - x * x));
    const side = pole.clone().addScaledVector(dir, -pole.dot(dir)).normalize();
    const mp = a.clone().addScaledVector(dir, x).addScaledVector(side, h);
    this.aim(upper, mid, mp.clone().sub(a));
    this.aim(mid, end, target.clone().sub(this.pos(mid)));
  }
  // O axă din poza de repaus, dusă în orientarea curentă a osului.
  axis(name, v) {
    const b = this.b[name];
    return v.clone().applyQuaternion(b.getWorldQuaternion(new THREE.Quaternion())).normalize();
  }
  dir(a, b) {
    const pa = this.b[a].getWorldPosition(new THREE.Vector3());
    const pb = this.b[b].getWorldPosition(new THREE.Vector3());
    return pb.sub(pa).normalize();
  }
}

// ---------- theme ----------
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
function themeColors() {
  return { accent: new THREE.Color(css('--accent') || '#d9481f'), ink: new THREE.Color(css('--ink') || '#161a1f') };
}

// ---------- scene ----------
const canvas = $('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.minDistance = 1.2;
controls.maxDistance = 9;
controls.maxPolarAngle = Math.PI * 0.53;

scene.add(new THREE.HemisphereLight(0xf2f5ff, 0x8a8178, 1.5));
const key = new THREE.DirectionalLight(0xffffff, 2.3);
key.position.set(-2.5, 4.5, 3.2);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
Object.assign(key.shadow.camera, { left: -1.6, right: 1.6, top: 2.2, bottom: -1.6, near: 0.5, far: 12 });
key.shadow.bias = -0.0004;
key.shadow.normalBias = 0.02;
scene.add(key);
const rim = new THREE.DirectionalLight(0xdfe8ff, 1.1);
rim.position.set(2.5, 2.8, -3);
scene.add(rim);

const floor = new THREE.Mesh(new THREE.CircleGeometry(2.6, 64), new THREE.ShadowMaterial({ opacity: 0.22 }));
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
scene.add(floor);
const ringMat = new THREE.LineBasicMaterial({ transparent: true, opacity: 0.35 });
const ring = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(
  Array.from({ length: 96 }, (_, i) => new THREE.Vector3(Math.cos(i / 96 * Math.PI * 2) * 0.75, 0.001, Math.sin(i / 96 * Math.PI * 2) * 0.75))), ringMat);
scene.add(ring);
// saltea pentru exercițiile făcute la sol
const MAT_H = 0.03;
const mat = new THREE.Mesh(new THREE.BoxGeometry(0.78, MAT_H, 2.1),
  new THREE.MeshStandardMaterial({ color: 0x3c4a55, roughness: 0.92 }));
mat.position.set(0, MAT_H / 2, 0.1);
mat.castShadow = true;
mat.receiveShadow = true;
mat.visible = false;
scene.add(mat);

// material manechin, cu evidențierea mușchilor (atribut aMuscle)
const muscleUniforms = { uAccent: { value: new THREE.Color() }, uIntensity: { value: 0 } };
const bodyMat = new THREE.MeshStandardMaterial({ color: 0xc4c9cf, roughness: 0.62, metalness: 0 });
bodyMat.onBeforeCompile = (sh) => {
  Object.assign(sh.uniforms, muscleUniforms);
  sh.vertexShader = sh.vertexShader
    .replace('#include <common>', '#include <common>\nattribute float aMuscle;\nvarying float vMuscle;')
    .replace('#include <begin_vertex>', '#include <begin_vertex>\nvMuscle = aMuscle;');
  sh.fragmentShader = sh.fragmentShader
    .replace('#include <common>', '#include <common>\nuniform vec3 uAccent;\nuniform float uIntensity;\nvarying float vMuscle;')
    .replace('#include <color_fragment>', '#include <color_fragment>\ndiffuseColor.rgb = mix(diffuseColor.rgb, uAccent, clamp(vMuscle * uIntensity, 0.0, 1.0));');
};
const eyeMat = new THREE.MeshStandardMaterial({ color: 0x2a2f35, roughness: 0.3 });

function applyTheme() {
  const c = themeColors();
  muscleUniforms.uAccent.value.copy(c.accent);
  ringMat.color.copy(c.accent);
  const dark = matchMedia('(prefers-color-scheme: dark)').matches && document.documentElement.dataset.theme !== 'light'
    || document.documentElement.dataset.theme === 'dark';
  floor.material.opacity = dark ? 0.45 : 0.22;
}
applyTheme();
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
new MutationObserver(applyTheme).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

// ---------- assets ----------
const loader = new GLTFLoader();
const cache = new Map();
// CFG.b64: modelele vin ca text base64 (`x.glb.txt`), pentru găzduiri care nu servesc .glb.
async function fetchB64(url) {
  const res = await fetch(url + '.txt');
  if (!res.ok) throw new Error(`${url}: ${res.status}`);
  const bin = atob((await res.text()).trim());
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return loader.parseAsync(bytes.buffer, '');
}
function load(url) {
  if (!cache.has(url)) cache.set(url, CFG.b64 ? fetchB64(url) : loader.loadAsync(url));
  return cache.get(url);
}

const state = {
  model: 'male', char: null, rig: null, anim: idle, ex: null,
  gear: [], t: 0, playing: !reduceMotion, speed: 1, highlight: true,
  list: [], filtered: [], shown: 0, token: 0,
};

async function setModel(name) {
  state.model = name;
  document.querySelectorAll('[data-model]').forEach((b) => b.classList.toggle('on', b.dataset.model === name));
  const gltf = await load(CFG.assets + MODELS[name]);
  if (state.model !== name) return;
  if (state.char) scene.remove(state.char);
  const char = gltf.scene;
  char.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
      o.frustumCulled = false;
      const small = o.geometry.attributes.position.count < 2000;
      o.material = small ? eyeMat : bodyMat;
      if (!o.geometry.attributes.aMuscle)
        o.geometry.setAttribute('aMuscle', new THREE.BufferAttribute(new Float32Array(o.geometry.attributes.position.count), 1));
    }
  });
  scene.add(char);
  state.char = char;
  state.rig = new Rig(char);
  await setupAnim();
}

// Evidențierea se calculează din greutățile pielii (`muscleBones`), din poziția vârfului
// în poza de repaus (`muscleMask(x, y, z)` → 0..1), sau din amândouă înmulțite.
function paintMuscles() {
  const { muscleBones, muscleMask } = state.anim;
  const weights = muscleBones || {};
  state.char.traverse((o) => {
    if (!o.isSkinnedMesh) return;
    const g = o.geometry;
    const idx = g.attributes.skinIndex, wt = g.attributes.skinWeight, pos = g.attributes.position, out = g.attributes.aMuscle;
    const factor = o.skeleton.bones.map((b) => weights[b.name] || 0);
    for (let i = 0; i < out.count; i++) {
      let s = 1;
      if (muscleBones) {
        s = 0;
        for (let k = 0; k < 4; k++) s += factor[idx.getComponent(i, k)] * wt.getComponent(i, k);
        s = Math.min(1, s * 1.15);
      }
      if (muscleMask) s *= muscleMask(pos.getX(i), pos.getY(i), pos.getZ(i));
      out.array[i] = muscleBones || muscleMask ? s : 0;
    }
    out.needsUpdate = true;
  });
}

async function setupAnim() {
  const token = ++state.token;
  const { rig, anim } = state;
  for (const g of state.gear) g.removeFromParent();
  state.gear = [];
  mat.visible = !!anim.mat;
  ring.visible = !anim.mat;
  paintMuscles();
  for (const eq of anim.equipment || []) {
    const gltf = await load(CFG.assets + eq.url);
    if (token !== state.token) return;
    const obj = gltf.scene.clone(true);
    obj.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = true;
        o.material = new THREE.MeshStandardMaterial({ color: /knurl/.test(o.name) ? 0x3b4047 : 0x23272c, metalness: 0.75, roughness: /knurl/.test(o.name) ? 0.7 : 0.32 });
      }
    });
    // atașare: poza neutră, apoi bara pusă în spațiul lumii și convertită în coordonatele mâinii
    rig.reset();
    anim.neutral ? anim.neutral(rig) : anim.pose(rig, 0, 0);
    state.char.updateMatrixWorld(true);
    const parent = rig.b[eq.attach];
    const gp = parent.getWorldPosition(new THREE.Vector3()).add(eq.offset || new THREE.Vector3());
    const want = new THREE.Matrix4().compose(gp, eq.worldRotation, new THREE.Vector3(1, 1, 1));
    const local = parent.matrixWorld.clone().invert().multiply(want);
    local.decompose(obj.position, obj.quaternion, obj.scale);
    parent.add(obj);
    state.gear.push(obj);
  }
}

// ---------- camera ----------
const VIEWS = {
  '34': { pos: [-2.5, 1.45, 3.0], target: [-0.1, 0.95, 0.05] },
  side: { pos: [-3.9, 1.15, 0.2], target: [-0.1, 0.92, 0] },
  front: { pos: [0.05, 1.2, 4.3], target: [0, 0.93, 0] },
};
let camTween = null;
function setView(name, instant) {
  const v = (state.anim.views && state.anim.views[name]) || VIEWS[name] || VIEWS['34'];
  document.querySelectorAll('[data-view]').forEach((b) => b.classList.toggle('on', b.dataset.view === name));
  const aspect = camera.aspect || 1;
  const narrow = aspect < 0.95;
  const k = narrow ? Math.min(2.2, 1.12 / aspect) : 1;
  const target = new THREE.Vector3(...v.target);
  if (narrow) target.y -= 0.12; // lasă loc pentru bara de redare de jos
  const pos = new THREE.Vector3(...v.pos).sub(target).multiplyScalar(k).add(target);
  if (instant || reduceMotion) {
    camera.position.copy(pos); controls.target.copy(target); camTween = null;
  } else {
    camTween = { t: 0, p0: camera.position.clone(), p1: pos, t0: controls.target.clone(), t1: target };
  }
  state.view = name;
}

function resize() {
  const r = canvas.parentElement.getBoundingClientRect();
  renderer.setSize(r.width, r.height, false);
  camera.aspect = r.width / Math.max(1, r.height);
  camera.updateProjectionMatrix();
}
new ResizeObserver(() => { resize(); }).observe(canvas.parentElement);

// ---------- UI: detalii ----------
function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// Cadran: valoarea v din [lo, hi] se întinde pe semicercul de jos, de la stânga la dreapta.
function gaugeXY(v, r, g = state.anim.gauge || {}) {
  const lo = g.lo ?? -45, hi = g.hi ?? 45;
  const f = Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
  const a = THREE.MathUtils.degToRad(-90 + f * 180);
  return [100 + r * Math.sin(a), 100 - r * Math.cos(a)];
}

function renderDetails(ex) {
  const anim = state.anim;
  const has = anim !== idle;
  $('now-title').textContent = ex[1];
  $('now-eyebrow').textContent = (ex[0] === DEFAULT_ID && !state.userPicked ? 'Ales la întâmplare · ' : 'Exercițiu · ') + '#' + ex[0];
  $('file').textContent = 'clipuri de facut/' + ex[2];

  const tags = $('tags');
  tags.replaceChildren();
  tags.append(el('span', 'tag' + (has ? ' hot' : ''), has ? 'Animație 3D' : 'Fără animație încă'));
  const tagList = has ? anim.tags : [ex[3], ex[4] === 'm' ? 'Bărbat' : ex[4] === 'f' ? 'Femeie' : ''].filter(Boolean);
  for (const t of tagList) tags.append(el('span', 'tag', t));

  $('gauge-box').hidden = !(has && anim.gauge);
  if (has && anim.gauge) {
    const [x0, y0] = gaugeXY(anim.gauge.min, 80), [x1, y1] = gaugeXY(anim.gauge.max, 80);
    $('g-range').setAttribute('d', `M${x0.toFixed(1)} ${y0.toFixed(1)} A80 80 0 0 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`);
    const [l, r] = anim.gauge.ends || ['ulnar', 'radial'];
    $('g-end-l').textContent = l;
    $('g-end-r').textContent = r;
  }

  const steps = $('steps');
  steps.replaceChildren();
  if (has) for (const s of anim.steps) steps.append(el('li', null, s));
  else steps.append(el('li', null, 'Pașii apar odată cu animația. Până atunci, urmărește clipul de referință.'));

  const mus = $('muscles');
  mus.replaceChildren();
  if (has) for (const [m, lvl] of anim.muscles) {
    const li = el('li');
    li.append(el('span', null, m), el('span', 'lvl ' + lvl, lvl === 'p' ? 'Principal' : 'Secundar'));
    mus.append(li);
  } else mus.append(el('li', 'small', ex[3] ? 'Zona: ' + ex[3] : 'Nespecificat în numele clipului'));
  $('highlight').closest('label').hidden = !has;

  const notice = $('notice');
  notice.hidden = has;
  if (!has) {
    notice.replaceChildren(el('strong', null, 'Animația nu e făcută încă'),
      document.createTextNode(`Au animație 3D doar ${Object.keys(ANIMATIONS).map((k) => '#' + k).join(' și ')}. Manechinul stă în postura de bază.`));
  }
  $('transport').style.visibility = has ? 'visible' : 'hidden';

  const box = $('ref-box'), video = $('ref');
  if (CFG.clips) {
    box.hidden = false;
    video.src = CFG.clips + encodeURIComponent(ex[2]);
    video.onerror = () => { box.hidden = true; };
    video.play().catch(() => {});
  } else box.hidden = true;
}

function setPlaying(p) {
  state.playing = p;
  $('play').setAttribute('aria-label', p ? 'Pauză' : 'Pornește');
  $('play-icon').setAttribute('d', p ? 'M7 5h3.5v14H7zM13.5 5H17v14h-3.5z' : 'M8 5.5v13l11-6.5z');
}

async function select(ex, { fromUser = false } = {}) {
  if (!ex) return;
  if (fromUser) state.userPicked = true;
  const before = state.anim;
  state.ex = ex;
  state.anim = ANIMATIONS[ex[0]] || idle;
  state.t = 0;
  try { history.replaceState(null, '', '#ex-' + ex[0]); } catch { /* ignorat */ }
  renderDetails(ex);
  document.querySelectorAll('.list button').forEach((b) => b.classList.toggle('sel', b.dataset.id === ex[0]));
  const want = ex[4] === 'f' ? 'female' : ex[4] === 'm' ? 'male' : state.model;
  if (want !== state.model || !state.rig) await setModel(want);
  else await setupAnim();
  if (state.anim !== before) setView(state.anim.camera || '34');
}

// ---------- UI: bibliotecă ----------
function renderList(reset) {
  const list = $('list');
  if (reset) { list.replaceChildren(); state.shown = 0; }
  const next = state.filtered.slice(state.shown, state.shown + PAGE);
  for (const ex of next) {
    const li = el('li');
    const b = el('button');
    b.type = 'button';
    b.dataset.id = ex[0];
    if (state.ex && state.ex[0] === ex[0]) b.classList.add('sel');
    b.append(el('span', 'nm', ex[1]), el('span', 'id', '#' + ex[0]));
    b.append(el('span', 'bp', ex[3] || '—'));
    if (ANIMATIONS[ex[0]]) b.append(el('span', 'b3d', '3D'));
    b.addEventListener('click', () => select(ex, { fromUser: true }));
    li.append(b);
    list.append(li);
  }
  state.shown += next.length;
  const n = state.filtered.length;
  $('list-meta').textContent = n === state.list.length
    ? `${n.toLocaleString('ro-RO')} exerciții, afișate ${state.shown}`
    : `${n.toLocaleString('ro-RO')} rezultate, afișate ${state.shown}`;
  $('more').hidden = state.shown >= n;
}

function applyFilter() {
  const q = $('search').value.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const body = $('body').value;
  const only = $('only3d').checked;
  state.filtered = state.list.filter((ex) =>
    (!body || ex[3] === body) && (!only || ANIMATIONS[ex[0]]) &&
    q.every((w) => ex[1].toLowerCase().includes(w) || ex[0] === w.replace('#', '')));
  renderList(true);
}

async function initLibrary() {
  const res = await fetch(CFG.catalog);
  state.list = await res.json();
  $('count').textContent = `${state.list.length.toLocaleString('ro-RO')} exerciții · ${Object.keys(ANIMATIONS).length} animate`;
  const bodies = [...new Set(state.list.map((e) => e[3]).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'ro'));
  for (const b of bodies) $('body').append(new Option(b, b));
  $('search').addEventListener('input', applyFilter);
  $('body').addEventListener('change', applyFilter);
  $('only3d').addEventListener('change', applyFilter);
  $('more').addEventListener('click', () => renderList(false));
  $('random').addEventListener('click', () => {
    const pool = state.filtered.length ? state.filtered : state.list;
    select(pool[Math.floor(Math.random() * pool.length)], { fromUser: true });
  });
  applyFilter();
}

// ---------- controale ----------
$('play').addEventListener('click', () => setPlaying(!state.playing));
document.querySelectorAll('[data-speed]').forEach((b) => b.addEventListener('click', () => {
  state.speed = +b.dataset.speed;
  document.querySelectorAll('[data-speed]').forEach((x) => x.classList.toggle('on', x === b));
}));
document.querySelectorAll('[data-view]').forEach((b) => b.addEventListener('click', () => setView(b.dataset.view)));
document.querySelectorAll('[data-model]').forEach((b) => b.addEventListener('click', () => setModel(b.dataset.model)));
$('highlight').addEventListener('change', (e) => { state.highlight = e.target.checked; });
let wasPlaying = false;
$('scrub').addEventListener('pointerdown', () => { wasPlaying = state.playing; setPlaying(false); });
$('scrub').addEventListener('input', (e) => {
  const d = state.anim.duration;
  state.t = Math.floor(state.t / d) * d + (e.target.value / 1000) * d * 0.9999;
});
$('scrub').addEventListener('change', () => { if (wasPlaying) setPlaying(true); wasPlaying = false; });
addEventListener('keydown', (e) => {
  if (e.code === 'Space' && !/INPUT|SELECT|BUTTON/.test(document.activeElement?.tagName || '')) {
    e.preventDefault(); setPlaying(!state.playing);
  }
});

// ---------- buclă ----------
const clock = new THREE.Clock();
let lastPhase = '';
function frame() {
  const dt = Math.min(clock.getDelta(), 0.1);
  const anim = state.anim;
  if (state.playing) state.t += dt * state.speed;
  const d = anim.duration;
  const u = (state.t % d) / d;

  if (state.rig) {
    state.rig.reset();
    anim.pose(state.rig, u, state.t);
    const e = anim.effort ? anim.effort(u) : 0;
    muscleUniforms.uIntensity.value += ((state.highlight ? 0.25 + 0.6 * e : 0) - muscleUniforms.uIntensity.value) * Math.min(1, dt * 6);
  }

  if (anim !== idle) {
    if (document.activeElement !== $('scrub')) $('scrub').value = Math.round(u * 1000);
    const ph = anim.phases.find((p) => u >= p.from && u < p.to);
    const label = ph ? ph.label : '';
    if (label !== lastPhase) { $('phase').textContent = label; lastPhase = label; }
    $('reps').textContent = 'rep ' + (Math.floor(state.t / d) + 1);
    if (anim.angle) {
      const v = anim.angle(u, state.rig);
      const signed = anim.gauge.signed !== false;
      $('angle').textContent = (signed ? (v >= 0 ? '+' : '−') : '') + Math.abs(Math.round(v)) + '°';
      $('angle-label').textContent = anim.gauge.label(v);
      const [x, y] = gaugeXY(v, 74);
      $('g-needle').setAttribute('x2', x.toFixed(1));
      $('g-needle').setAttribute('y2', y.toFixed(1));
    }
  }

  if (camTween) {
    camTween.t = Math.min(1, camTween.t + dt / 0.7);
    const k = 1 - Math.pow(1 - camTween.t, 3);
    camera.position.lerpVectors(camTween.p0, camTween.p1, k);
    controls.target.lerpVectors(camTween.t0, camTween.t1, k);
    if (camTween.t >= 1) camTween = null;
  }
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}

// ---------- start ----------
resize();
setView('34', true);
setPlaying(state.playing);
await initLibrary();
const fromHash = (location.hash.match(/^#ex-(\w+)/) || [])[1];
const first = state.list.find((e) => e[0] === fromHash) || state.list.find((e) => e[0] === DEFAULT_ID) || state.list[0];
await select(first);
setView(state.anim.camera || '34', true);
window.__manechin = { state, camera, controls, setPlaying }; // pentru depanare
requestAnimationFrame(frame);
