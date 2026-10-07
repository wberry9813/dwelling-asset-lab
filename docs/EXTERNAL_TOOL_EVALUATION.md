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
| Home Builder 5.2.4 | PROBE NEXT | Cabinets, closets, doors/windows, hard-surface interior modules | Explicit Blender 5.2 compatibility, Linux package, GPL-3.0, purpose-built for home interiors |
| blender_cad | PROBE | Declarative hard-surface / modular environment generation | Good match for dimensions and code-reviewable hard assets |
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

## Home Builder 5.2.4

Worth a focused technical probe for:

- base cabinets;
- wall cabinets;
- wardrobes / closets;
- doors and windows;
- countertops.

If its generated topology and Blender 5 headless behavior are acceptable, it can save substantial work on dimension-driven hard-surface families.

5.2.4 adds explicit Blender 5.2 compatibility and ships for Linux, making it suitable for a GitHub Actions compatibility probe.

It should not be used for sofas, bedding or other hero soft goods.

## blender_cad

Worth probing as a lower-level alternative for hard-surface production.

Potential strengths:

- explicit dimensions;
- declarative assemblies;
- code review;
- Blender-native meshes and modifiers.

Adopt only if it reduces our own generator complexity without forcing a new abstraction onto soft or artistic assets.

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
