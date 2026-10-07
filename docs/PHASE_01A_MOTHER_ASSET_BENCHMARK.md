# Phase 01A — Mother Asset Benchmark

Status: **IN PROGRESS**
Date: 2026-10-07

## Scope

Phase 01A creates two reusable mother assets:

- Sofa 001
- Bed 001

They are reviewed inside a deliberately simple Review Vignette. The shell is not a shipping architectural asset.

## Outputs

Each mother asset produces:

- editable Blender source (.blend);
- GLB runtime/interchange export;
- three-quarter review render;
- side review render;
- measured bounds and mesh statistics.

The phase also emits a semantic lighting recipe:

- `dwelling-warm-daylight-v0.1`

## Quality questions

### Sofa 001

The sofa must answer:

- Does the silhouette read as upholstered rather than block-built?
- Are arms, base, seat and back cushions structurally believable?
- Do seams/details improve form without becoming noise?
- Does the model remain attractive from normal Dwelling camera distances?
- Is the asset reusable without baked directional lighting?

### Bed 001

The bed must answer:

- Do hard structure and textiles feel like one coherent asset?
- Are mattress, sheet, duvet, pillows and throw visually layered?
- Does the bedding avoid a rigid procedural-box appearance?
- Is the footprint believable at real-world scale?

## Acceptance gate

Phase 01A is not accepted merely because CI passes.

CI PASS means the production mechanics work.

Visual acceptance requires manual review of the generated renders. If either asset still reads as procedural blockout, revise modeling language before adding more mother assets.

## Runtime note

Current Dwelling RealityKit implementation is still evolving. Phase 01A may propose changes to runtime material, lighting, format or placement conventions when those changes improve the long-term asset system.
