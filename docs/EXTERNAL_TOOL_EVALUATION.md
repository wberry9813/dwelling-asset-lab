# External Tool Evaluation

Status: **ACTIVE**
Date: 2026-10-07

This document records which external Blender projects / asset sources are useful to Dwelling and what role they should play.

## Decision table

| Candidate | Decision | Best use in Dwelling | Why |
| --- | --- | --- | --- |
| Blender 5.2 LTS | ADOPTED | Production baseline | LTS, remote asset libraries, current Geometry Nodes / physics |
| Poly Haven | ADOPT | PBR materials, HDRIs, selected CC0 models / quality references | CC0, high quality, public API, no account required for assets |
| Poly Haven HAT | ADOPT CONCEPTS / PROBE DIRECT USE | Asset QC | Its validation philosophy closely matches Dwelling contracts |
| Blender Remote Asset Library | ADOPT LATER | Distribution of approved source assets | Static hosting, Blender-native browsing/download |
| Home Builder (public GitHub v3.0.7) | REFERENCE ONLY | Interior-system ideas | Public repo/release is old and targets Blender 3.x-era APIs; do not make it a Blender 5.2 CI dependency |
| blender_cad | REFERENCE ONLY | Declarative hard-surface ideas | Technically interesting, but current public repo has no declared license; do not vendor or depend on it |
| blender_furniture_builder | REFERENCE | Cabinet construction logic | Useful construction semantics but older Blender baseline |
| BlenderProc | DEFER | Large scene orchestration / render automation | Strong batch scene tool, but does not improve furniture authoring quality |
| BlenderKit | DISCOVERY ONLY | Inspiration / selectively licensed assets | Variable asset licensing and service/account dependency are poor release-CI defaults |

## Poly Haven policy

Poly Haven is the preferred external public asset source because its assets are CC0.

Use cases:

- fabric / wood / stone / metal PBR materials;
- HDRI lighting references;
- selected props;
- quality references for topology, material breakup and textile treatment;
- selected model geometry only when the visual style actually fits Dwelling.

Do not copy a model merely because it is free. It must still pass the Dwelling visual direction and runtime normalization gates.

Current quality references:

- Rough Linen — material reference for upholstery / bedding;
- Vintage Day Bed — geometry/detail reference for sag, pillow treatment and draped bedding, **not** the desired Dwelling visual style.

## Home Builder

Worth a focused technical probe for:

- base cabinets;
- wall cabinets;
- wardrobes / closets;
- doors and windows;
- countertops.

If its generated topology and Blender 5 headless behavior are acceptable, it can save substantial work on dimension-driven hard-surface families.

The public GitHub repository currently exposes releases only through v3.0.7 and its README describes the Blender 3 migration. A newer commercial/site distribution may exist, but it is not an appropriate reproducible public-CI dependency unless its exact package and license are independently pinned.

It should not be used for sofas, bedding or other hero soft goods.

## blender_cad

Worth probing as a lower-level alternative for hard-surface production.

Potential strengths:

- explicit dimensions;
- declarative assemblies;
- code review;
- Blender-native meshes and modifiers.

Do not adopt code from the current public repository until a compatible license is explicitly present. Its declarative modeling concepts may still inform our own design.

## HAT

HAT should influence our validator even if we do not install it directly in CI.

Checks worth converging on:

- metric units;
- clean asset isolation;
- applied/intentional transforms;
- naming discipline;
- Principled BSDF export-safe materials;
- texture path/color-space checks;
- no orphan / contaminated data;
- glTF export validation;
- LOD structure when introduced.

Dwelling-specific scale / pivot / front-axis checks remain authoritative.

## Bed 001 production decision

Bed 001 moves from **generator-first** to **authored hybrid source**.

Target workflow:

```text
parametric hard bed frame
        +
authored mattress / pillows / duvet
        +
thin fabric shell + PBR textile
        ↓
visual authoring in Blender
        ↓
cloth/deform/sculpt as needed
        ↓
bake/apply accepted result
        ↓
stable .blend source
        ↓
GitHub Actions validation/export/review
```

The release build must not depend on reproducing an artistic cloth solve every time.

## Next probes

Priority:

1. Bed 001 authored-hybrid source workflow.
2. Poly Haven Rough Linen material integration at controlled resolution.
3. Home Builder 5 headless cabinet probe.
4. HAT check mapping into Dwelling validator.
5. Remote Asset Library publication after several assets are accepted.


## Hard-surface decision

For Dwelling's first cabinet family, implement a small in-house parametric casework generator instead of adopting an external framework.

Reasons:

- cabinet geometry is simple and dimension-driven;
- Dwelling needs a strict 600/450/300 mm module language;
- runtime pivots and semantic parts matter more than general CAD features;
- avoiding old or ambiguously licensed dependencies keeps public CI deterministic;
- the generator can still use normal Blender modifiers/materials and authored detail assets.

External projects remain useful references, but the first production hard-surface benchmark should have no mandatory third-party code dependency.
