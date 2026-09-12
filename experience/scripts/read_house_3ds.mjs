// Convert the supplied static 3DS house to an intermediate glTF for Blender.
// TDSLoader is a build-time dependency only; the app still loads compressed GLB.
import fs from 'node:fs';
import * as THREE from 'three';
import { TDSLoader } from 'three/addons/loaders/TDSLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';

const [source, destination, reportPath] = process.argv.slice(2);
if (!source || !destination || !reportPath) throw new Error('Usage: node read_house_3ds.mjs source.3DS intermediate.glb report.json');
// GLTFExporter needs FileReader for binary buffers; no DOM or texture decoding is
// needed because this particular 3DS contains colours and UVs but no image maps.
globalThis.FileReader = class {
  readAsArrayBuffer(blob) {
    blob.arrayBuffer().then(result => { this.result = result; this.onloadend?.(); });
  }
};
const data = fs.readFileSync(source);
const loader = new TDSLoader();
const scene = loader.parse(data.buffer.slice(data.byteOffset, data.byteOffset + data.byteLength), '');
const report = { materials: [], excluded: [], originalTriangles: 0, retainedTriangles: 0 };
for (const material of Object.values(loader.materials)) {
  if (material.map || material.bumpMap || material.alphaMap || material.specularMap) {
    throw new Error('Unexpected image references: resolve source textures before conversion.');
  }
  report.materials.push({ name: material.name, color: material.color.getHexString(), opacity: material.opacity });
}
for (const object of [...scene.children]) {
  if (!object.isMesh) continue;
  const triangles = object.geometry.index.count / 3;
  report.originalTriangles += triangles;
  const materials = Array.isArray(object.material) ? object.material : [object.material];
  if (materials.length !== 1) throw new Error(`Review nontrivial face material groups on ${object.name}`);
  const material = materials[0];
  if (['ground', 'ground_2', 'paving'].includes(material.name)) {
    report.excluded.push({ name: object.name, material: material.name, triangles });
    scene.remove(object);
    continue;
  }
  object.updateWorldMatrix(true, false);
  const bounds = new THREE.Box3().setFromObject(object);
  if (![...bounds.min.toArray(), ...bounds.max.toArray()].every(value => Number.isFinite(value) && Math.abs(value) < 10000)) {
    throw new Error(`Invalid building coordinates in ${object.name}`);
  }
  // The glass's legacy opacity is zero; Blender assigns browser PBR finishes.
  object.material = new THREE.MeshStandardMaterial({ color: material.color, name: material.name, roughness: .8 });
  report.retainedTriangles += triangles;
}
report.boundsSource = new THREE.Box3().setFromObject(scene).getSize(new THREE.Vector3()).toArray();
scene.rotation.x = -Math.PI / 2; // 3DS Z up -> glTF Y up.
const binary = await new GLTFExporter().parseAsync(scene, { binary: true, onlyVisible: true });
fs.writeFileSync(destination, Buffer.from(binary));
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report, null, 2));
