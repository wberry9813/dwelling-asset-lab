# Quality-First Asset Pipeline

Status: **ADOPTED FOR PHASE 01+**
Date: 2026-10-07

## Decision

Dwelling Asset Lab is **quality-first and automation-assisted**, not code-generation-first.

The pipeline must optimize for:

1. visual quality;
2. reliable real-world dimensions and pivots;
3. reproducible review / validation / export;
4. runtime suitability for Dwelling;
5. maintainable source assets.

Python generation is one authoring option, not a requirement.

---

## Authoring tiers

### Tier A — Parametric hard-surface

Best for:

- cabinets;
- tables;
- shelving;
- doors;
- windows;
- modular architectural/furniture systems.

Preferred tools:

- Geometry Nodes;
- deterministic Python generators;
- Blender modifiers.

These assets benefit strongly from explicit dimensions and repeatable variants.

### Tier B — Hybrid soft-surface

Best for:

- sofas;
- cushions;
- mattresses;
- simple upholstery;
- rugs.

Preferred tools:

- authored base mesh;
- subdivision;
- lattice / curve / shrinkwrap / surface deform;
- Geometry Nodes;
- controlled Python parameterization.

Python may set dimensions and variant parameters, but does not need to create every vertex.

### Tier C — Hero cloth / sculpted assets

Best for:

- duvets;
- sheets;
- throws;
- pillows;
- curtains;
- highly organic hero assets.

Preferred tools:

- curated .blend source;
- Blender Cloth where useful;
- sculpt / proportional editing;
- retopology;
- subdivision;
- thin cloth shell over a separate soft volume when appropriate.

CI should consume the approved source and validate/export it headlessly. The source does not need to be regenerated from primitives on every build.

---

## Bedding rule

Do not model a duvet as a thick solidified sheet.

Use two concepts separately:

- **soft volume / loft** — the filled body of the duvet;
- **fabric shell** — a visually thin textile surface.

Visible fabric edge thickness should normally be millimetres, not centimetres. Loft comes from shape, not from an oversized Solidify thickness.

The current Bed 001 prototype used overly thick shell geometry and should be treated as a workflow-learning asset rather than a final benchmark.

---

## CI responsibility

GitHub Actions owns production repeatability, not artistic authorship.

CI should:

- install a pinned Blender LTS version;
- load authored .blend or run an asset builder;
- resolve approved materials / textures;
- run normalization;
- validate scale, pivot and naming;
- validate texture paths and shader compatibility;
- create runtime export(s);
- render review images;
- publish artifacts;
- fail loudly on contract violations.

CI does **not** require that source geometry be generated from Python.

---

## External tools and libraries

### Blender 5.2 LTS

Adopt as the forward production baseline after CI compatibility is proven.

Reasons:

- current LTS;
- supported through July 2028;
- improved Geometry Nodes and physics tooling;
- improved background / asset-library capabilities.

### Poly Haven

Preferred external source for reusable PBR material / HDRI building blocks when a suitable asset exists.

Rules:

- use only assets with clear source/license metadata;
- pin exact asset identity and resolution;
- record provenance in the asset manifest;
- avoid unpinned live dependencies for release builds;
- cache downloads in CI;
- keep the runtime material graph export-friendly.

### Poly Haven HAT

Use primarily as a **QC reference model**.

Its checks overlap strongly with Dwelling needs:

- metric units;
- applied transforms;
- origin discipline;
- texture path checks;
- Principled BSDF discipline;
- glTF export checks;
- file contamination / orphan checks.

Dwelling should keep its own runtime-specific validator even if selected HAT checks are later invoked directly.

### BlenderProc

Useful later for large-scale scene orchestration, randomized review scenes, dataset-style camera/render jobs and photorealistic batch rendering.

Do **not** adopt it as the core modeling layer: it does not solve furniture authoring quality and would add an abstraction layer around a pipeline that is currently small enough to control directly.

### Blendkit / BlenderKit

Potentially useful for discovery and selectively sourced assets.

Do not make it a hard release-CI dependency:

- library assets can use different license types;
- some assets require account/subscription access;
- live service/auth dependencies reduce deterministic public CI.

Any approved third-party asset should be normalized into the Dwelling pipeline with explicit provenance and license metadata.

### Paid / marketplace Geometry Nodes

May be evaluated when they materially improve quality or authoring speed.

Do not commit or redistribute marketplace source files until the exact license permits the intended repository and product use.

---

## Source asset manifest

Every production asset should converge toward a manifest such as:

```json
{
  "id": "bed-001",
  "sourceType": "blend",
  "source": "source/bed-001.blend",
  "authoringBlender": "5.2.2",
  "frontAxis": "-Y",
  "nominalDimensionsMeters": [1.98, 2.10, 1.52],
  "materials": [
    {
      "id": "linen-warm-01",
      "source": "dwelling"
    }
  ],
  "license": {
    "geometry": "Dwelling",
    "externalMaterials": []
  },
  "export": {
    "runtime": "glb"
  }
}
```

The manifest becomes the contract between artistic source, CI and Dwelling runtime.

---

## Review modes

Use two review levels.

### Fast Review

Runs on normal pushes / pull requests.

- Eevee;
- reduced resolution;
- two representative angles;
- scale / pivot / export validation.

Goal: cheap iteration.

### Hero Review

Runs manually, on release candidates, or on explicit asset-review changes.

- higher resolution;
- more angles;
- optional Cycles where it materially improves material judgment;
- stricter artifact inspection.

Goal: visual acceptance.

---

## Immediate Bed 001 direction

Bed 001 should no longer be optimized by adding more thickness or more procedural bevels.

Next version should use:

1. stable hard bed frame;
2. realistic mattress volume;
3. thin fitted-sheet layer;
4. soft duvet loft volume;
5. thin draped fabric shell;
6. independently authored pillows;
7. real fabric roughness / normal detail;
8. restrained wrinkles concentrated at compression/contact zones.

The acceptance test is visual: it must stop reading as a cheap low-poly blanket while preserving correct bounds and runtime export.


### Dwelling Remote Asset Library

Blender 5.2 introduces remote asset libraries that can be served from static HTTP hosting.

This is a strong future fit for approved Dwelling source assets:

```text
approved self-contained .blend assets
        ↓
CI: blender -b -c asset_listing generate ...
        ↓
static hosted library
        ↓
Blender Asset Browser on artist / review machines
```

Use this as a browsing/distribution layer for approved Blender assets, not as an unpinned dependency for release builds.

Authoring sources may keep external dependencies while being edited, but a published remote-library asset must be self-contained according to Blender's remote-library requirements.


## Simulation policy

Cloth and other physics are primarily **authoring tools**, not mandatory release-build steps.

Recommended flow:

```text
editable source
→ cloth / deformation / sculpt exploration
→ visual acceptance
→ bake / apply approved result to stable source mesh
→ CI normalization + validation + export
```

Re-running an expensive cloth solve in every release build is discouraged unless the asset is intentionally parameterized by simulation and reproducibility has been proven.

This keeps CI deterministic and fast while preserving high-quality authored drape.


## External asset promotion gate

External CC0 or otherwise permitted assets are never production assets merely because they can be downloaded.

Promotion path:

```text
external source
→ probe
→ inspect geometry/materials/license
→ normalize to Dwelling scale/orientation/pivot
→ remove unwanted style-specific parts/dependencies
→ assign Dwelling-compatible materials
→ visual review
→ approved stable .blend source
→ runtime export
```

Release builds should consume the approved normalized source, not an unreviewed live-library asset. Live APIs are appropriate for discovery/probes; production inputs should be version-pinned and provenance-recorded.
