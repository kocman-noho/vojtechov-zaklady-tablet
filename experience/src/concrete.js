import * as THREE from 'three';

// The CAD has no UV unwrap. Object-space triplanar sampling keeps a consistent
// grain size on the curved wall, sloped top and vertical cut faces, even exploded.
export function createConcreteMaterial(renderer, changed) {
  const material = new THREE.MeshStandardMaterial({ color: '#a1a496', roughness: .96, flatShading: true });
  material.userData.textureStatus = 'loading';
  new THREE.TextureLoader().load(import.meta.env.BASE_URL + 'textures/concrete-aggregate.jpg', texture => {
    texture.wrapS = texture.wrapT = THREE.MirroredRepeatWrapping;
    texture.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
    // Used as linear surface variation, not as a replacement albedo colour.
    texture.colorSpace = THREE.NoColorSpace;
    material.onBeforeCompile = shader => {
      shader.uniforms.concreteTexture = { value: texture };
      const varyings = 'varying vec3 vConcretePosition;\n';
      shader.vertexShader = varyings + shader.vertexShader;
      shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', `
        #include <begin_vertex>
        vConcretePosition = position;
      `);
      shader.fragmentShader = 'uniform sampler2D concreteTexture;\n' + varyings + shader.fragmentShader;
      shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', `
        #include <map_fragment>
        vec3 concreteSurfaceNormal = normalize(cross(dFdx(vConcretePosition), dFdy(vConcretePosition)));
        vec3 concreteWeights = pow(abs(concreteSurfaceNormal), vec3(4.0));
        concreteWeights /= max(dot(concreteWeights, vec3(1.0)), 0.0001);
        vec3 concretePoint = vConcretePosition / 3.0;
        vec3 concreteSample = texture2D(concreteTexture, concretePoint.yz).rgb * concreteWeights.x
          + texture2D(concreteTexture, concretePoint.xz).rgb * concreteWeights.y
          + texture2D(concreteTexture, concretePoint.xy).rgb * concreteWeights.z;
        float concreteGrain = dot(concreteSample, vec3(0.333333));
        diffuseColor.rgb *= 0.65 + concreteGrain * 0.7;
      `);
      shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>', `
        #include <roughnessmap_fragment>
        roughnessFactor = clamp(0.88 + concreteGrain * 0.16, 0.0, 1.0);
      `);
      // Surface-gradient bump mapping, using the existing raster derivatives.
      // No displacement, added vertices, extra draw calls or UV seams.
      shader.fragmentShader = shader.fragmentShader.replace('#include <normal_fragment_maps>', `
        #include <normal_fragment_maps>
        vec3 concreteDx = dFdx(-vViewPosition);
        vec3 concreteDy = dFdy(-vViewPosition);
        vec3 concreteR1 = cross(concreteDy, normal);
        vec3 concreteR2 = cross(normal, concreteDx);
        float concreteDet = dot(concreteDx, concreteR1) * faceDirection;
        vec3 concreteGradient = sign(concreteDet) * 0.003 *
          (dFdx(concreteGrain) * concreteR1 + dFdy(concreteGrain) * concreteR2);
        if (abs(concreteDet) > 0.00000001) normal = normalize(abs(concreteDet) * normal - concreteGradient);
      `);
    };
    material.customProgramCacheKey = () => 'concrete-triplanar-v2';
    material.needsUpdate = true;
    material.userData.textureStatus = 'ready';
    changed();
  }, undefined, () => {
    // Texture delivery is optional; keep the foundation readable if it fails.
    material.userData.textureStatus = 'error';
    changed();
  });
  return material;
}
