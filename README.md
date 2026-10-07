# Dwelling Asset Lab

Procedural 3D asset production lab for **Dwelling**.

## Goal

Build a reusable library of precise, refined and attractive residential assets. Blender is treated as a deterministic build tool: source scripts generate editable `.blend` files, runtime `.glb` files, validation reports and review renders.

## Visual direction

**Warm Miniature Realism**

- Real-world metric scale and believable construction
- Refined silhouettes, bevels and material separation
- Warm, restrained residential palette
- Miniature/diorama readability without toy-like proportions
- Hero-quality source assets with runtime-friendly exports

## First benchmark

**Apartment 001** — a compact one-bedroom apartment with living/dining room, kitchen and bathroom.

The first milestone is intentionally small: prove the complete asset pipeline before expanding the furniture library.

## Build outputs

A successful CI build should produce:

- `dwelling-apartment-001.blend`
- `dwelling-apartment-001.glb`
- preview renders
- `validation.json`

Generated binary assets are build artifacts, not committed source files.


## Current phase

See [Phase 01 — Production Direction & Benchmark Strategy](docs/PHASE_01_PRODUCTION_DIRECTION.md) for the current production boundary, benchmark strategy, lighting approach and asset sequencing.


### Active benchmark

[Phase 01A — Mother Asset Benchmark](docs/PHASE_01A_MOTHER_ASSET_BENCHMARK.md) builds Sofa 001 and Bed 001 in a shared neutral review vignette.


### Quality-first production

See [Quality-First Asset Pipeline](docs/QUALITY_FIRST_PIPELINE.md) for the adopted hybrid authoring model: curated Blender sources, Geometry Nodes / cloth / sculpt where useful, with automated CI validation and export.


### Hard-surface benchmark

[Phase 01B — Hard Surface Benchmark](docs/PHASE_01B_HARD_SURFACE_BENCHMARK.md) validates the 600 mm kitchen base cabinet module, physical/install bounds, semantic door pivots and runtime GLB hierarchy.
