import assert from 'node:assert/strict';
import * as THREE from 'three';
import {createTerrain, GROUND_LEVEL, CUTAWAY_FLOOR, foundationUnderside} from '../src/terrain.js';
const terrain = createTerrain(new THREE.MeshStandardMaterial({side:THREE.DoubleSide}));
terrain.updateMatrixWorld(true);
const meshes=[];terrain.traverse(o=>{if(o.isMesh)meshes.push(o);});
function soilHeight(x,z) {
 const ray=new THREE.Raycaster(new THREE.Vector3(x,10,z),new THREE.Vector3(0,-1,0));
 const hits=ray.intersectObjects(meshes,false);assert.ok(hits.length,`No soil at ${x},${z}`);return hits[0].point.y;
}
for(const [x,z] of [[1,-22],[5,-19],[7.3,-18.7],[-16,-29],[-24,3],[-19,0],[0,22]]) assert.ok(Math.abs(soilHeight(x,z)-GROUND_LEVEL)<1e-5,'Ground under comparison objects');
for(const [x,z] of [[.1,-.1],[1,-1],[10,-.1],[.1,-10],[10,-10]]) assert.ok(Math.abs(soilHeight(x,z)-CUTAWAY_FLOOR)<1e-5,'Duct opening is unobstructed');
for(const [x,z] of [[-2,2],[-4.65,0],[-8,2],[10,2]]) assert.ok(Math.abs(soilHeight(x,z)-foundationUnderside(Math.hypot(x,z)))<.001,'Foundation rests on matching soil profile');
console.log('PASS: finished ground, open soil below ducts, and foundation support profile.');
