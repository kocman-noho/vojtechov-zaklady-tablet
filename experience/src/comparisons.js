import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GROUND_LEVEL } from './terrain.js';

export const comparisonAssets = {
  man: { name: 'Muž', size: 'výška 1,88 m', position: [5, -19], rotation: Math.PI, visible: true },
  woman: { name: 'Žena', size: 'výška 1,75 m', position: [7.3, -18.7], rotation: Math.PI - .3, visible: true },
  car: { name: 'Škoda Kodiaq', size: 'délka 4,70 m', position: [1, -22], rotation: -.2, visible: true },
  house: { name: 'Dům', size: 'výška 9,08 m', position: [-16, -29], rotation: .35, visible: false },
};

export function createComparisons(scene, renderer, loadModel, changed) {
  const objects = {}, status = {}, pending = {}, selected = {};
  let enabled = true;
  let environment;
  const message = document.querySelector('#comparison-status');
  for (const [key, asset] of Object.entries(comparisonAssets)) {
    const object = new THREE.Group();
    object.position.set(asset.position[0], GROUND_LEVEL, asset.position[1]);
    object.rotation.y = asset.rotation;
    object.visible = asset.visible;
    selected[key] = asset.visible;
    objects[key] = object;
    status[key] = 'idle';
    scene.add(object);
  }

  function update() {
    for (const [key, object] of Object.entries(objects)) {
      const button = document.querySelector(`[data-object="${key}"]`);
      button.disabled = !enabled;
      button.setAttribute('aria-pressed', object.visible);
      button.setAttribute('aria-busy', status[key] === 'loading');
      button.querySelector('i').textContent = status[key] === 'loading' ? '…' : object.visible ? '✓' : '+';
    }
    const failed = Object.keys(status).filter(key => status[key] === 'error');
    const loading = Object.keys(status).filter(key => status[key] === 'loading' && objects[key].visible);
    message.textContent = failed.length ? `Nelze načíst: ${failed.map(key => comparisonAssets[key].name).join(', ')}. Zkuste znovu klepnout na tlačítko.`
      : loading.length ? `Načítání: ${loading.map(key => comparisonAssets[key].name).join(', ')}…` : '';
    changed();
  }

  async function ensureLoaded(key) {
    if (status[key] === 'ready') return;
    if (pending[key]) return pending[key];
    status[key] = 'loading';
    update();
    pending[key] = loadModel(`comparisons/${key}.glb`).then(gltf => {
      if (!environment) {
        const pmrem = new THREE.PMREMGenerator(renderer);
        const room = new RoomEnvironment();
        environment = pmrem.fromScene(room, .04);
        room.dispose();
        pmrem.dispose();
      }
      const anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
      gltf.scene.traverse(object => {
        if (!object.isMesh) return;
        object.castShadow = true;
        object.receiveShadow = true;
        const materials = Array.isArray(object.material) ? object.material : [object.material];
        for (const material of materials) {
          material.envMap = environment.texture;
          material.envMapIntensity = key === 'car' ? .8 : .35;
          for (const texture of [material.map, material.normalMap]) {
            if (texture) texture.anisotropy = anisotropy;
          }
        }
      });
      // Correct sub-millimetre compression drift at the contact plane.
      const bounds = new THREE.Box3().setFromObject(gltf.scene);
      gltf.scene.position.y -= bounds.min.y;
      objects[key].add(gltf.scene);
      status[key] = 'ready';
    }).catch(() => {
      status[key] = 'error';
      selected[key] = false;
      objects[key].visible = false;
    }).finally(() => {
      delete pending[key];
      update();
    });
    return pending[key];
  }

  function toggle(key) {
    if (!enabled) return;
    selected[key] = !selected[key];
    objects[key].visible = selected[key];
    if (objects[key].visible) void ensureLoaded(key);
    update();
  }

  return {
    objects, status, toggle,
    setEnabled(value) {
      enabled = value;
      for (const [key, object] of Object.entries(objects)) {
        object.visible = enabled && selected[key];
        if (object.visible) void ensureLoaded(key);
      }
      update();
    },
    loadVisible: () => Promise.all(Object.keys(objects).filter(key => objects[key].visible).map(ensureLoaded)),
  };
}
