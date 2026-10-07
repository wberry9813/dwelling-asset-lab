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
