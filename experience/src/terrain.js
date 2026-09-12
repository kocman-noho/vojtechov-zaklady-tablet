import * as THREE from 'three';

// Drawing D02888980: pedestal top = 0, backfill = -0.15 m.
// The opening is an explanatory soil cutaway, not an excavation design.
export const GROUND_LEVEL = -.15;
export const OPENING_RADIUS = 17.6;
export const CUTAWAY_FLOOR = -4.05;
export function foundationUnderside(radius) {
  return radius <= 4.4 ? -3.2 : radius >= 4.9 ? -2.7 : -3.2 + radius - 4.4;
}

export function createTerrain(groundMaterial) {
  const terrain = new THREE.Group(); terrain.name = 'ground_cutaway';
  const soil = new THREE.MeshStandardMaterial({ color: '#b9ac94', roughness: 1, side: THREE.DoubleSide });
  const cutFace = new THREE.MeshStandardMaterial({ color: '#a99a81', roughness: 1, side: THREE.DoubleSide });
  const surface = new THREE.Shape();
  surface.moveTo(-700, -700); surface.lineTo(700, -700); surface.lineTo(700, 700); surface.lineTo(-700, 700); surface.closePath();
  const opening = new THREE.Path(); opening.absarc(0, 0, OPENING_RADIUS, 0, Math.PI * 2, true); surface.holes.push(opening);
  const ground = new THREE.Mesh(new THREE.ShapeGeometry(surface, 144), groundMaterial);
  ground.rotation.x = -Math.PI / 2; ground.position.y = GROUND_LEVEL; ground.receiveShadow = true;
  ground.name = 'finished_ground'; terrain.add(ground);

  function addSurface(positions, indices, material, name) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geometry.setIndex(indices); geometry.computeVertexNormals();
    const mesh = new THREE.Mesh(geometry, material); mesh.receiveShadow = true; mesh.name = name;
    terrain.add(mesh); return mesh;
  }
  const rings = [0, 4.4, 4.9, 13.3, 15.6, OPENING_RADIUS];
  const height = (r, exposed) => {
    const bed = exposed ? CUTAWAY_FLOOR : foundationUnderside(r);
    if (r <= 15.6) return bed;
    return THREE.MathUtils.lerp(bed, GROUND_LEVEL, (r - 15.6) / (OPENING_RADIUS - 15.6));
  };
  // Match the concrete's removed quadrant: X positive, Z negative.
  for (let sector = 0; sector < 4; sector++) {
    const positions = [], indices = [], steps = 48;
    for (const r of rings) for (let j = 0; j <= steps; j++) {
      const angle = -Math.PI / 2 + sector * Math.PI / 2 + j / steps * Math.PI / 2;
      positions.push(r * Math.cos(angle), height(r, sector === 0), r * Math.sin(angle));
    }
    for (let i = 0; i < rings.length - 1; i++) for (let j = 0; j < steps; j++) {
      const a = i * (steps + 1) + j, b = a + steps + 1;
      indices.push(a, a + 1, b, a + 1, b + 1, b);
    }
    addSurface(positions, indices, soil, sector === 0 ? 'exposed_soil_below_ducts' : `supporting_soil_${sector}`);
  }
  // Vertical soil section faces below the two concrete cut faces.
  for (const angle of [-Math.PI / 2, 0]) {
    const positions = [], indices = [];
    for (const r of rings) {
      const x = r * Math.cos(angle), z = r * Math.sin(angle);
      positions.push(x, height(r, false), z, x, height(r, true), z);
    }
    for (let i = 0; i < rings.length - 1; i++) { const a = i * 2; indices.push(a, a + 1, a + 2, a + 1, a + 3, a + 2); }
    addSurface(positions, indices, cutFace, 'soil_section_face');
  }
  // Clip the ground grid to the opening so it cannot draw across the interior.
  const gridPoints = [];
  const line = (a, b) => gridPoints.push(...a, ...b);
  for (let coordinate = -70; coordinate <= 70; coordinate += 2) {
    const gap = Math.abs(coordinate) < OPENING_RADIUS ? Math.sqrt(OPENING_RADIUS ** 2 - coordinate ** 2) : 0;
    const y = GROUND_LEVEL + .012;
    if (gap) {
      line([coordinate, y, -70], [coordinate, y, -gap]); line([coordinate, y, gap], [coordinate, y, 70]);
      line([-70, y, coordinate], [-gap, y, coordinate]); line([gap, y, coordinate], [70, y, coordinate]);
    } else {
      line([coordinate, y, -70], [coordinate, y, 70]); line([-70, y, coordinate], [70, y, coordinate]);
    }
  }
  const grid = new THREE.LineSegments(new THREE.BufferGeometry().setAttribute('position', new THREE.Float32BufferAttribute(gridPoints, 3)), new THREE.LineBasicMaterial({ color: '#cfc6b7', transparent: true, opacity: .42 }));
  terrain.add(grid);
  const rimPoints = Array.from({ length: 192 }, (_, i) => {
    const angle = i / 192 * Math.PI * 2;
    return new THREE.Vector3(OPENING_RADIUS * Math.cos(angle), GROUND_LEVEL + .018, OPENING_RADIUS * Math.sin(angle));
  });
  terrain.add(new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(rimPoints), new THREE.LineBasicMaterial({ color: '#a89c89', transparent: true, opacity: .7 })));
  return terrain;
}
