/**
 * Prepare the MVPS 3D model for the dashboard as ONE scene.
 *
 * The source CAD export is 49 MB: 395,129 nodes instancing 410 meshes, which
 * renders 25.5 million vertices per frame and hangs a browser tab. Almost all
 * of those nodes are unnamed scaffolding (`Geom3D`, `Geom3D_`, or blank).
 *
 * The whole scene is kept, so the station reads as the model that was authored
 * rather than a set of disconnected parts. Equipment the dashboard needs to
 * highlight is renamed to a stable tag first, so those groups can still be
 * found after the optimisation that collapses everything else.
 *
 * The tracker field is left instanced rather than joined: joining bakes out
 * 25.5 M vertices and costs 66 MB, while GPU instancing keeps it small and fast.
 *
 * Run:  node tools/prepare_model.mjs
 * Out:  src/najm3000/dashboard/static/models/station.glb + manifest.json
 */

import { NodeIO, PropertyType } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import {
  dedup,
  instance,
  prune,
  quantize,
  weld,
} from '@gltf-transform/functions';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..');
const SOURCE = resolve(REPO, '3D_GLB/MVPS.glb');
const OUT_DIR = resolve(REPO, 'src/najm3000/dashboard/static/models');
const OUT_FILE = 'station.glb';

/** Equipment the dashboard can highlight, keyed by its node name in the CAD. */
const HIGHLIGHTABLE = [
  { key: 'inverter_01', node: 'Electric switch box_Inventer 1', asset: 'inverter_01', label: 'Inverter 01' },
  { key: 'inverter_02', node: 'electrical box_Inventer 2',      asset: 'inverter_02', label: 'Inverter 02' },
  { key: 'rmu',         node: 'electrical box_RMU',             asset: 'rmu',         label: 'RMU' },
  { key: 'skid',        node: 'SKID',                           asset: 'skid',        label: 'MVPS skid' },
  { key: 'transformer', node: 'Power+Transformer++30+40+50+MVA+(Tirathai)_Transformer', asset: 'idt_01', label: 'Transformer' },
  { key: 'pss',         node: '08+01+2010+MODEL+2_PSS',         asset: 'pss',         label: 'Pooling substation' },
];

/** Prefix marking a group the viewer may recolour. */
const TAG = 'NAJM_';

const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);

/**
 * Rename each highlightable node to a stable tag.
 *
 * Optimisation rewrites or drops arbitrary CAD names, but a node still
 * referenced by the scene keeps whatever name it carries. Tagging before
 * optimising is what lets the viewer find these six afterwards.
 */
function tagHighlightable(document) {
  const found = [];
  const byName = new Map();
  for (const node of document.getRoot().listNodes()) {
    const name = node.getName();
    if (name && !byName.has(name)) byName.set(name, node);
  }

  HIGHLIGHTABLE.forEach((part, index) => {
    const root = byName.get(part.node);
    if (!root) {
      console.warn(`  ! not found in source: ${part.node}`);
      return;
    }

    // Tag the MATERIAL rather than the node. Pruning drops intermediate nodes
    // that hold no mesh of their own, which loses a node-name tag, but a
    // material stays reachable for as long as a primitive references it.
    const marker = document
      .createMaterial(`${TAG}${part.key}`)
      .setRoughnessFactor(0.8)
      .setMetallicFactor(0.1)
      // A unique base colour keeps dedup() from merging these into one.
      .setBaseColorFactor([
        0.62 + index * 0.001,
        0.63 + index * 0.001,
        0.64 + index * 0.001,
        1,
      ]);

    // The inverters and the RMU are children of the skid, so tagging the skid
    // naively would overwrite theirs and leave only one group. Order in
    // HIGHLIGHTABLE puts the children first, and an already-tagged primitive is
    // never reclaimed - so the skid ends up owning only what is left of it.
    // Meshes are cloned per node because several of these subtrees share
    // geometry instanced at different positions.
    let primitives = 0;
    const visit = (node) => {
      const mesh = node.getMesh();
      if (mesh) {
        const copy = document.createMesh(`${TAG}${part.key}_mesh`);
        let claimed = 0;
        for (const prim of mesh.listPrimitives()) {
          const owner = prim.getMaterial()?.getName() ?? '';
          if (owner.startsWith(TAG)) {
            copy.addPrimitive(prim);
            continue;
          }
          copy.addPrimitive(prim.clone().setMaterial(marker));
          claimed += 1;
        }
        primitives += claimed;
        node.setMesh(copy);
      }
      node.listChildren().forEach(visit);
    };
    visit(root);

    root.setName(`${TAG}${part.key}`);
    found.push({ ...part, primitives });
    console.log(`  tagged ${part.key.padEnd(12)} ${primitives} primitives`);
  });

  return found;
}

/** Strip textures; the dashboard renders a schematic, not a photoreal scene. */
function stripTextures() {
  return (document) => {
    for (const texture of document.getRoot().listTextures()) texture.dispose();
    for (const material of document.getRoot().listMaterials()) {
      if ((material.getName() ?? '').startsWith(TAG)) continue;
      material.setMetallicFactor(0.1).setRoughnessFactor(0.8);
    }
  };
}

async function main() {
  mkdirSync(OUT_DIR, { recursive: true });
  console.log(`source: ${SOURCE}`);

  const document = await io.read(SOURCE);
  const before = document.getRoot().listNodes().length;
  const parts = tagHighlightable(document);
  console.log(`tagged ${parts.length} groups; ${before} nodes in source`);

  await document.transform(
    stripTextures(),
    prune({ keepAttributes: false, keepLeaves: false }),
    dedup({ propertyTypes: [PropertyType.MESH, PropertyType.TEXTURE, PropertyType.ACCESSOR] }),
    instance({ min: 2 }),
    weld(),
    quantize(),
  );

  const kept = document
    .getRoot()
    .listMaterials()
    .filter((m) => (m.getName() ?? '').startsWith(TAG))
    .map((m) => m.getName());

  const bytes = await io.writeBinary(document);
  writeFileSync(resolve(OUT_DIR, OUT_FILE), bytes);

  const after = document.getRoot().listNodes().length;
  console.log(
    `\n${OUT_FILE}: ${(bytes.byteLength / 1e6).toFixed(2)} MB, ` +
    `${after} nodes (from ${before}), ${document.getRoot().listMeshes().length} meshes`,
  );
  console.log(`highlightable groups surviving: ${kept.length}/${parts.length}`);
  for (const name of kept) console.log(`  ${name}`);

  writeFileSync(
    resolve(OUT_DIR, 'manifest.json'),
    JSON.stringify(
      {
        file: OUT_FILE,
        note:
          'Representative 3D model, purpose-built for this proof of concept. ' +
          'Geometry and part names are illustrative and do not depict the ' +
          'specified equipment. Architecture only.',
        tag_prefix: TAG,
        source_nodes: before,
        output_nodes: after,
        bytes: bytes.byteLength,
        parts: parts.map(({ key, asset, label }) => ({
          key,
          group: `${TAG}${key}`,
          asset,
          label,
          present: kept.includes(`${TAG}${key}`),
        })),
      },
      null,
      2,
    ),
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
