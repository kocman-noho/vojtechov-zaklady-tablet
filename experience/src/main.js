import './style.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { createComparisons } from './comparisons.js';
import { createConcreteMaterial } from './concrete.js';
import { createTerrain, GROUND_LEVEL } from './terrain.js';

const $ = s => document.querySelector(s);
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const touchInput = matchMedia('(any-pointer: coarse)');
const viewport = $('#viewport');
const scene = new THREE.Scene();
scene.background = new THREE.Color('#efeae2');
scene.fog = new THREE.Fog('#efeae2', 130, 550);
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
} catch (error) {
  $('#load-status').textContent = '3D zobrazení není dostupné. Otevřete aplikaci v prohlížeči s hardwarovou akcelerací.';
  throw error;
}
renderer.setPixelRatio(Math.min(devicePixelRatio, touchInput.matches ? 1.5 : 1.75));
renderer.setSize(viewport.clientWidth, viewport.clientHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
viewport.prepend(renderer.domElement);
renderer.domElement.setAttribute('aria-label', '3D model základu a větrné elektrárny');
renderer.domElement.tabIndex = 0;
const camera = new THREE.PerspectiveCamera(38, viewport.clientWidth / viewport.clientHeight, .08, 1500);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = !reducedMotion;
controls.dampingFactor = .075;
controls.minDistance = 9;
controls.maxDistance = 600;
controls.maxPolarAngle = Math.PI * .485;
controls.autoRotateSpeed = .5;
controls.touches.ONE = THREE.TOUCH.ROTATE;
controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
controls.target.set(0, -1, 0);
camera.position.set(35, 25, -43);
scene.add(new THREE.HemisphereLight('#fbf8f0', '#b3ab9d', 1.8));
const sun = new THREE.DirectionalLight('#fff3dc', 2.6);
sun.position.set(-35, 65, -30);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -55, right: 55, top: 55, bottom: -55, near: .5, far: 220 });
sun.shadow.normalBias = .04;
sun.shadow.bias = -.0001;
scene.add(sun);
const fill = new THREE.DirectionalLight('#d8e6ef', .8);
fill.position.set(30, 20, 15); scene.add(fill);
const material = (color, roughness = .75, metalness = 0) => new THREE.MeshStandardMaterial({ color, roughness, metalness });
const mat = {
 concrete: createConcreteMaterial(renderer, () => { dirty = true; }), steel: material('#596e6c', .48, .5), anchors: material('#ae8554', .4, .65), ducts: material('#db7938', .55),
 ground: material('#e6e0d5', 1),
};
function mesh(geometry, m, parent, pos = [0, 0, 0]) {
  const object = new THREE.Mesh(geometry, m); object.position.set(...pos); object.castShadow = true; object.receiveShadow = true; parent.add(object); return object;
}
const terrain = createTerrain(mat.ground); scene.add(terrain);
const foundation = new THREE.Group(); scene.add(foundation);
const turbine = new THREE.Group(); turbine.visible = false; scene.add(turbine);
const stub = new THREE.Group(); scene.add(stub);
// A short context shell only. Full supplied turbine is used in the scale chapter.
const stubShape = new THREE.Shape(); stubShape.absarc(0, 0, 3.35, 0, Math.PI * 2, false);
const hole = new THREE.Path(); hole.absarc(0, 0, 3.22, 0, Math.PI * 2, true); stubShape.holes.push(hole);
const shell = mesh(new THREE.ExtrudeGeometry(stubShape, { depth: 3.8, bevelEnabled: false, curveSegments: 80 }), material('#e1e0d4'), stub);
shell.rotation.x = -Math.PI / 2; shell.position.y = .06;
const comparisons = createComparisons(scene, renderer, fetchModel, () => { dirty = true; });
const objects = comparisons.objects;
const labels = [];
function label(html, point, options = {}) {
  const element = document.createElement('div'); element.className = 'model-label' + (options.dimension ? ' dimension' : ''); element.innerHTML = html;
  $('#labels').append(element); const entry = { element, point, ...options }; labels.push(entry); return entry;
}
label('<b>26,6 m</b> · průměr', new THREE.Vector3(0, GROUND_LEVEL + .15, 20.4), { dimension: true, modes: ['foundation', 'deconstruct'] });
label('<b>3,05 m</b><span> pod terénem</span>', new THREE.Vector3(14.7, -1.55, -5.7), { modes: ['foundation'] });
label('<b>1,88 m</b><span> · Muž</span>', () => objects.man.position.clone().add(new THREE.Vector3(0, 3.5, 0)), { object: 'man', modes: ['foundation', 'deconstruct'] });
label('<b>1,75 m</b><span> · Žena</span>', () => objects.woman.position.clone().add(new THREE.Vector3(0, 2.5, 0)), { object: 'woman', modes: ['foundation', 'deconstruct'] });
label('<b>4,70 m</b><span> · Škoda Kodiaq</span>', () => objects.car.position.clone().add(new THREE.Vector3(0, 2.7, 0)), { object: 'car', modes: ['foundation', 'deconstruct'] });
label('<b>9,08 m</b> · Dům', () => objects.house.position.clone().add(new THREE.Vector3(0, 11, 0)), { object: 'house', modes: ['foundation', 'deconstruct'] });
label('<b>132 m</b> · výška náboje', new THREE.Vector3(-3, 134, 0), { modes: ['scale'] });
label('Základ <b>26,6 m</b>', new THREE.Vector3(0, 2, 0), { modes: ['scale'] });
const dims = new THREE.Group(); scene.add(dims);
const dimMaterial = new THREE.LineBasicMaterial({ color: '#6e9fc8', transparent: true, opacity: .8 });
function segment(a, b, parent = dims) { parent.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(...a), new THREE.Vector3(...b)]), dimMaterial)); }
segment([-13.3, GROUND_LEVEL + .025, 19], [13.3, GROUND_LEVEL + .025, 19]);
for (const x of [-13.3, 13.3]) segment([x, GROUND_LEVEL + .025, 18.5], [x, GROUND_LEVEL + .025, 19.5]);
const burialDim = new THREE.Group(); scene.add(burialDim);
segment([14, GROUND_LEVEL, -5.4], [14, -3.2, -5.4], burialDim);
for (const y of [GROUND_LEVEL, -3.2]) segment([13.7, y, -5.4], [14.3, y, -5.4], burialDim);
const heightDim = new THREE.Group(); heightDim.visible = false; scene.add(heightDim);
segment([-16, 0, 0], [-16, 132, 0], heightDim); segment([-18, 132, 0], [-14, 132, 0], heightDim); segment([-18, 0, 0], [-14, 0, 0], heightDim);
const state = { mode: 'foundation', explosion: 0, targetExplosion: 0, playing: false, loaded: false, turbineLoaded: false, layers: { concrete: true, steel: true, anchors: true, ducts: true } };
const parts = [];
const content = { foundation: 'Základ', deconstruct: 'Rozložení', scale: 'Celá elektrárna' };
let flight = null, lastTime = performance.now(), dirty = true;
function fly(position, target, duration = 1300) {
  if (reducedMotion) duration = 0;
  flight = { from: camera.position.clone(), to: new THREE.Vector3(...position), fromTarget: controls.target.clone(), toTarget: new THREE.Vector3(...target), start: performance.now(), duration };
  dirty = true;
}
function preset(mode = state.mode) {
  const mobile = viewport.clientWidth < 600;
  const houseVisible = objects.house.visible && mode !== 'scale';
  const target = mode === 'scale' ? [0, 95, 0] : houseVisible ? [-8, mode === 'deconstruct' ? 3.5 : 0, -12] : mode === 'deconstruct' ? [-2, 3.5, 0] : [0, -1, 0];
  const position = mode === 'scale' ? [240, 155, -300] : houseVisible ? [42, 35, -69] : mode === 'deconstruct' ? [40, 29, -48] : mobile ? [39, 29, -49] : [34, 25, -42];
  // Preserve horizontal framing when the canvas becomes narrow on rotation.
  const fit = Math.max(1, 1.15 / camera.aspect) * (mode === 'scale' ? 1.18 : 1);
  const offset = new THREE.Vector3(...position).sub(new THREE.Vector3(...target)).multiplyScalar(fit);
  fly(offset.add(new THREE.Vector3(...target)).toArray(), target, mode === 'scale' ? 1800 : 1300);
}
function stopPlaying() { state.playing = false; $('#play').innerHTML = 'Přehrát <span>▶</span>'; }
function setExplosion(value, fromUser = false) {
  if (fromUser) stopPlaying();
  state.targetExplosion = THREE.MathUtils.clamp(value, 0, 1);
  $('#explode').value = Math.round(state.targetExplosion * 100); $('#explode-value').value = `${Math.round(state.targetExplosion * 100)} %`;
  if (state.mode === 'foundation' && value > 0) selectMode('deconstruct', false);
  dirty = true;
}
function selectMode(mode, defaultExplosion = true) {
  if (!content[mode]) return;
  stopPlaying(); state.mode = mode; document.body.dataset.scene = mode;
  history.replaceState(null, '', `#${mode}`);
  document.title = `NOHO · ${content[mode]} · Vojtěchov`;
  document.querySelectorAll('.chapters [data-scene]').forEach(b => { const active = b.dataset.scene === mode; b.classList.toggle('active', active); b.setAttribute('aria-pressed', active); });
  comparisons.setEnabled(mode !== 'scale');
  turbine.visible = mode === 'scale'; stub.visible = mode !== 'scale'; dims.visible = mode !== 'scale'; heightDim.visible = mode === 'scale'; burialDim.visible = mode === 'foundation';
  $('#explode').disabled = mode === 'scale'; $('#play').disabled = mode === 'scale';
  document.querySelectorAll('[data-layer]').forEach(b => { b.disabled = mode === 'scale'; });
  if (defaultExplosion) setExplosion(mode === 'deconstruct' ? .68 : 0);
  preset(); dirty = true;
}
document.querySelectorAll('.chapters [data-scene]').forEach(button => button.onclick = () => selectMode(button.dataset.scene));
document.querySelectorAll('[data-object]').forEach(button => button.onclick = () => {
  comparisons.toggle(button.dataset.object);
  if (button.dataset.object === 'house' && objects.house.visible && state.mode !== 'scale') preset();
  dirty = true;
});
document.querySelectorAll('[data-layer]').forEach(button => button.onclick = () => {
  const layer = button.dataset.layer; state.layers[layer] = !state.layers[layer]; button.setAttribute('aria-pressed', state.layers[layer]); dirty = true;
});
$('#explode').oninput = event => setExplosion(+event.target.value / 100, true);
$('#play').onclick = () => {
  if (state.playing) { stopPlaying(); return; }
  if (state.mode !== 'deconstruct') selectMode('deconstruct', false);
  if (state.targetExplosion >= .99) setExplosion(0);
  state.playing = true; $('#play').innerHTML = 'Pozastavit <span>Ⅱ</span>'; dirty = true;
};
$('#reset').onclick = () => { controls.autoRotate = false; $('#spin').setAttribute('aria-pressed', false); stopPlaying(); setExplosion(0); preset(); };
$('#top').onclick = () => fly(state.mode === 'scale' ? [0, 350, -.1] : [0, 66, -.1], [0, 0, 0]);
function zoom(factor) { const destination = camera.position.clone().sub(controls.target).multiplyScalar(factor).add(controls.target); fly(destination.toArray(), controls.target.toArray(), 300); }
$('#zoom-in').onclick = () => zoom(.8); $('#zoom-out').onclick = () => zoom(1.25);
$('#spin').onclick = () => { flight = null; controls.autoRotate = !controls.autoRotate; $('#spin').setAttribute('aria-pressed', controls.autoRotate); dirty = true; };
controls.addEventListener('start', () => { flight = null; }); controls.addEventListener('change', () => { dirty = true; });
renderer.domElement.addEventListener('keydown', e => {
  if (e.key === '+' || e.key === '=') zoom(.8); else if (e.key === '-') zoom(1.25); else if (e.key.toLowerCase() === 'r') $('#reset').click();
  else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(e.key)) {
    e.preventDefault(); flight = null;
    const spherical = new THREE.Spherical().setFromVector3(camera.position.clone().sub(controls.target));
    spherical.theta += e.key === 'ArrowLeft' ? -.12 : e.key === 'ArrowRight' ? .12 : 0;
    spherical.phi = THREE.MathUtils.clamp(spherical.phi + (e.key === 'ArrowUp' ? -.08 : e.key === 'ArrowDown' ? .08 : 0), .05, Math.PI * .485);
    camera.position.copy(new THREE.Vector3().setFromSpherical(spherical).add(controls.target)); controls.update(); dirty = true;
  }
});
const dialog = $('#about'); $('#about-button').onclick = () => dialog.showModal(); $('#close-about').onclick = () => dialog.close();
dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
new ResizeObserver(() => {
  const w = viewport.clientWidth, h = viewport.clientHeight;
  if (!w || !h) return;
  const previousFit = Math.max(1, 1.15 / camera.aspect);
  camera.aspect = w / h;
  const fit = Math.max(1, 1.15 / camera.aspect) / previousFit;
  // Retain the user's orbit/zoom while adapting to a new aspect ratio.
  camera.position.sub(controls.target).multiplyScalar(fit).add(controls.target);
  if (flight) {
    flight.from.sub(flight.fromTarget).multiplyScalar(fit).add(flight.fromTarget);
    flight.to.sub(flight.toTarget).multiplyScalar(fit).add(flight.toTarget);
  }
  camera.updateProjectionMatrix(); renderer.setSize(w, h); dirty = true;
}).observe(viewport);
function updateInteractionHint() {
  const hint = touchInput.matches ? 'Jedním prstem otáčíte, dvěma posouváte a roztažením přibližujete.' : 'Tažením otáčíte, pravým tlačítkem posouváte a kolečkem přibližujete.';
  viewport.setAttribute('aria-label', `Interaktivní 3D model. ${hint} K dispozici jsou také tlačítka v horní liště.`);
}
updateInteractionHint(); touchInput.addEventListener('change', updateInteractionHint);
const v = new THREE.Vector3();
function updateLabels() {
  const occupied = [];
  for (const entry of labels) {
    const point = typeof entry.point === 'function' ? entry.point() : entry.point;
    v.copy(point).project(camera);
    const hidden = !entry.modes.includes(state.mode) || (entry.object && (!objects[entry.object].visible || comparisons.status[entry.object] !== 'ready')) || v.z > 1 || v.z < -1 || Math.abs(v.x) > .97 || Math.abs(v.y) > .95;
    entry.element.dataset.hidden = hidden;
    if (!hidden) {
      const element = entry.element;
      const x = (v.x * .5 + .5) * viewport.clientWidth;
      let y = (-v.y * .5 + .5) * viewport.clientHeight;
      const width = element.offsetWidth, height = element.offsetHeight;
      let lift = 0;
      // Separate nearby people/car labels on tablet canvases. The longer stem
      // still points to the original projected position.
      for (let attempt = 0; attempt < labels.length; attempt++) {
        const collision = occupied.find(r => x - width / 2 < r.right + 4 && x + width / 2 > r.left - 4 && y - height < r.bottom + 4 && y > r.top - 4);
        if (!collision) break;
        const shift = y - collision.top + 5; y -= shift; lift += shift;
      }
      element.dataset.hidden = y - height < 0;
      element.style.left = `${x}px`; element.style.top = `${y}px`;
      element.style.setProperty('--stem-height', `${16 + lift}px`);
      if (y >= height) occupied.push({ left: x - width / 2, right: x + width / 2, top: y - height, bottom: y });
    }
  }
}
function animate(now) {
  requestAnimationFrame(animate);
  const dt = Math.min((now - lastTime) / 1000, .25); lastTime = now;
  if (document.hidden) return;
  if (state.playing) {
    setExplosion(Math.min(1, state.targetExplosion + dt / 12));
    if (state.targetExplosion >= 1) stopPlaying();
  }
  if (Math.abs(state.explosion - state.targetExplosion) > .0002) { state.explosion = reducedMotion ? state.targetExplosion : THREE.MathUtils.damp(state.explosion, state.targetExplosion, 6, dt); dirty = true; }
  if (flight) {
    const t = flight.duration ? Math.min(1, (now - flight.start) / flight.duration) : 1, ease = t * t * (3 - 2 * t);
    camera.position.lerpVectors(flight.from, flight.to, ease); controls.target.lerpVectors(flight.fromTarget, flight.toTarget, ease); dirty = true;
    if (t === 1) flight = null;
  }
  controls.update();
  if (!dirty) return;
  dirty = false;
  for (const part of parts) {
    const amount = state.mode === 'scale' ? 0 : state.explosion;
    part.position.copy(part.userData.origin).addScaledVector(part.userData.offset, amount);
    if (part.userData.layer === 'concrete') {
      // Lift the underside clear of the real ground before moving sideways.
      const sideways = THREE.MathUtils.smoothstep(amount, .6, 1);
      part.position.x = part.userData.origin.x + part.userData.offset.x * sideways;
      part.position.z = part.userData.origin.z + part.userData.offset.z * sideways;
    }
    part.visible = state.mode === 'scale' ? part.userData.layer === 'concrete' || part.userData.layer === 'anchors' : state.layers[part.userData.layer];
  }
  stub.position.y = state.explosion * 13;
  stub.visible = state.mode !== 'scale' && state.layers.anchors;
  scene.fog.near = state.mode === 'scale' ? 400 : 130; scene.fog.far = state.mode === 'scale' ? 950 : 550;
  renderer.render(scene, camera); updateLabels();
}
requestAnimationFrame(animate);
const draco = new DRACOLoader()
  .setDecoderPath(import.meta.env.BASE_URL + 'decoders/draco/')
  .setDecoderConfig({ type: 'wasm' })
  .setWorkerLimit(2);
const loader = new GLTFLoader().setDRACOLoader(draco);
async function fetchModel(path, compressed = false) {
  const response = await fetch(import.meta.env.BASE_URL + 'models/' + path).catch(error => { throw new Error(path + ': ' + error.message); });
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
  let data = await response.arrayBuffer();
  const signature = new Uint8Array(data, 0, Math.min(2, data.byteLength));
  // Static servers differ: Vite adds Content-Encoding and the browser decompresses.
  // Decode ourselves only when the received bytes still have the gzip signature.
  if (compressed && signature[0] === 31 && signature[1] === 139) {
    const stream = new Blob([data]).stream().pipeThrough(new DecompressionStream('gzip'));
    data = await new Response(stream).arrayBuffer();
  }
  return loader.parseAsync(data, '');
}
async function init() {
  const turbinePromise = fetchModel('turbine.glb').then(gltf => {
    gltf.scene.traverse(object => { if (object.isMesh) { object.castShadow = true; object.receiveShadow = true; object.material.side = THREE.DoubleSide; } });
    turbine.add(gltf.scene); state.turbineLoaded = true; dirty = true;
  });
  const foundationPromise = fetchModel('foundation.glb.gz', true).then(gltf => {
    gltf.scene.traverse(object => {
      if (!object.isMesh) return;
      const name = object.name;
      const layer = /concrete/.test(name) ? 'concrete' : /duct/.test(name) ? 'ducts' : /anchor|flange/.test(name) ? 'anchors' : 'steel';
      object.material = mat[layer]; object.castShadow = layer === 'concrete'; object.receiveShadow = true;
      const offset = /concrete/.test(name) ? [-9, 6, 7] : /upper/.test(name) ? [0, 10, 0] : /shear|pedestal/.test(name) ? [0, 6, 0] : /anchor|flange/.test(name) ? [0, 5, 0] : /duct/.test(name) ? [0, 0, 0] : [0, 2, 0];
      object.userData = { layer, origin: object.position.clone(), offset: new THREE.Vector3(...offset) };
      parts.push(object);
    });
    foundation.add(gltf.scene); dirty = true;
  });
  await Promise.all([foundationPromise, turbinePromise, comparisons.loadVisible()]);
  state.loaded = true; $('#loading').classList.add('hidden');
  selectMode(content[location.hash.slice(1)] ? location.hash.slice(1) : 'foundation');
  window.foundationExperience = {
    state: () => ({ ...state, concreteTexture: mat.concrete.userData.textureStatus, comparisons: { ...comparisons.status }, layers: { ...state.layers }, objects: Object.fromEntries(Object.entries(objects).map(([key, value]) => [key, value.visible])), meshCount: parts.length, triangles: renderer.info.render.triangles }),
    selectMode, setExplosion,
    view: () => ({ position: camera.position.toArray(), target: controls.target.toArray(), distance: camera.position.distanceTo(controls.target) }),
    placement: () => ({ groundLevel: GROUND_LEVEL, objectBottoms: Object.fromEntries(Object.entries(objects).filter(([key]) => comparisons.status[key] === 'ready').map(([key, object]) => [key, new THREE.Box3().setFromObject(object).min.y])), concreteBottom: new THREE.Box3().setFromObject(parts.find(part => part.userData.layer === 'concrete')).min.y }),
    bounds: () => ({ foundation: new THREE.Box3().setFromObject(foundation).getSize(new THREE.Vector3()).toArray(), turbine: new THREE.Box3().setFromObject(turbine).getSize(new THREE.Vector3()).toArray(), comparisons: Object.fromEntries(Object.entries(objects).filter(([key]) => comparisons.status[key] === 'ready').map(([key, value]) => [key, new THREE.Box3().setFromObject(value).getSize(new THREE.Vector3()).toArray()])) }),
  };
}
// A direct link to the full turbine should not fetch hidden comparison models.
if (location.hash === '#scale') comparisons.setEnabled(false);
init().catch(error => {
  $('#loading').classList.remove('hidden'); $('#loading strong').textContent = 'Model se nepodařilo načíst';
  $('#load-status').textContent = 'Obnovte stránku a zkuste to znovu.'; console.error(error);
});
renderer.domElement.addEventListener('webglcontextlost', event => { event.preventDefault(); $('#loading').classList.remove('hidden'); $('#loading strong').textContent = '3D zobrazení bylo přerušeno'; $('#load-status').textContent = 'Pro obnovení modelu načtěte stránku znovu.'; });
