/**
 * Extract the skid-only unit from the CAD export for the 3D map layer.
 *
 * The map fills each MVPS block with a procedurally instanced tracker field
 * (the CAD's PV Area is 227k meshes for the whole plant — per-block extraction
 * from it is neither feasible nor needed at map scale), plus one real skid
 * model per station. This script produces that skid.
 *
 * Run:  node tools/prepare_map_assets.mjs
 * Out:  src/najm3000/dashboard/static/models/skid_unit.glb
 */

import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, join, prune, quantize, weld } from '@gltf-transform/functions';
import { writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const SOURCE = resolve(REPO, '3D_GLB/MVPS.glb');
const OUT = resolve(REPO, 'src/najm3000/dashboard/static/models/skid_unit.glb');

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);

const document = await io.read(SOURCE);
const root = document.getRoot();

for (const texture of root.listTextures()) texture.dispose();
for (const material of root.listMaterials()) {
  material.setMetallicFactor(0.15).setRoughnessFactor(0.8);
}

const target = root.listNodes().find((n) => n.getName() === 'SKID');
if (!target) throw new Error('SKID node not found');

const scene = root.getDefaultScene() ?? root.listScenes()[0];
for (const child of scene.listChildren()) scene.removeChild(child);
target.detach();
scene.addChild(target);

await document.transform(
  prune({ keepAttributes: false, keepLeaves: false }),
  dedup(),
  weld(),
  join({ keepNamed: false }),
  quantize(),
  prune(),
);

const bytes = await io.writeBinary(document);
writeFileSync(OUT, bytes);
console.log(
  `skid_unit.glb: ${(bytes.byteLength / 1e6).toFixed(2)} MB, ` +
  `${root.listMeshes().length} meshes`,
);
