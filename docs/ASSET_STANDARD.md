# Dwelling Asset Standard v0.1

## Coordinate & scale

- Blender units: metric, 1 unit = 1 metre.
- Z is up.
- Real-world dimensions are the default; stylisation must not break believable use.
- Object origins should be intentional and useful for placement.

## Visual quality

The target is **Warm Miniature Realism**: realistic construction with restrained stylisation.

Every hero asset should prioritize:
1. believable proportions and construction;
2. clean silhouette and controlled bevels;
3. readable material separation;
4. details that survive close review;
5. visual consistency with the complete apartment.

## Runtime discipline

- Keep source detail editable in the .blend.
- Export a GLB suitable for real-time review.
- Avoid unnecessary hidden geometry.
- Use stable, descriptive object/material names.
- Validation must fail loudly for missing required outputs.

## Review

Every benchmark scene should provide at least:
- isometric overview;
- validation JSON;
- editable BLEND;
- runtime GLB.

Additional close-ups and turntables will be added after the baseline pipeline is proven.


## Placement contract

Mother and production assets must use an explicit placement contract.

Current Phase 01 convention:

- Blender authoring axes: local X = width, local Y = depth, local Z = height.
- Canonical asset front = local -Y.
- World origin lies on the asset's floor-contact plane.
- The asset is centered around X/Y zero unless its placement semantics require another documented pivot.
- Nominal dimensions are metadata and must be checked against measured geometry bounds.
- Phase 01A benchmark tolerance is 0.03 m per dimension and 0.015 m for floor contact. Production tolerances may be tightened after runtime integration evidence.

Runtime systems such as RealityKit may use different axis semantics. Mapping belongs at the asset/runtime adapter boundary; do not silently change the authoring convention per asset.

## Modeling method

The pipeline is automation-first, not primitive-only.

Choose the modeling technique that best preserves quality and reuse:

- hard-surface and modular assets: prefer dimensions, reusable generators and deterministic procedural construction;
- upholstery and soft goods: procedural base meshes may be combined with subdivision, deformation, cloth simulation or other Blender-native modifiers;
- hero assets may use curated source geometry when pure procedural generation would visibly reduce quality.

The invariant is reproducibility of validation/export/review, not that every vertex must be produced by a simple Python primitive.

## Review shell boundary

Review walls, floors and background geometry are presentation context only. They must remain visually subordinate and must not become accidental production architecture.

## Lighting portability

Review lighting should be captured as semantic presets (intent, direction, softness, relative intensity and temperature) rather than baked directional light inside reusable furniture. Blender and RealityKit numeric values are implementation-specific; visual intent is the portable contract.
