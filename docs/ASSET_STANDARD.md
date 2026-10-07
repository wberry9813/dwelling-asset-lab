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
