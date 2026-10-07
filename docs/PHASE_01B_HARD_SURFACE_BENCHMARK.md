# Phase 01B — Hard Surface Benchmark

Status: **IN PROGRESS**
Date: 2026-10-07

## Purpose

Validate the opposite modeling class from Sofa / Bed:

- precise casework;
- modular dimensions;
- semantic sub-parts;
- mechanical pivots;
- runtime-friendly hierarchy;
- deterministic hard-surface generation.

## First asset

**Kitchen Base 600**

Canonical module:

- module width: 600 mm;
- carcass depth: 560 mm;
- plinth: 100 mm;
- carcass height above plinth: 770 mm;
- overall module height before countertop: 870 mm;
- 18 mm structural panels;
- 19 mm slab doors;
- 2 mm perimeter reveals;
- 3 mm center gap;
- front axis: -Y;
- floor-contact origin: Z = 0.

A continuous countertop is deliberately **not** part of the production module. Review context may show one, but Dwelling should be able to assemble countertop runs independently from cabinet modules.

## Acceptance questions

1. Does the cabinet look like real casework rather than stacked boxes?
2. Are panel thickness, shadow gaps and toe-kick depth believable?
3. Can doors open around explicit hinge pivots?
4. Does the open view reveal credible back/shelf/interior structure?
5. Can adjacent 600/450/300 modules share the same construction language?
6. Does GLB retain useful hierarchy for future RealityKit interaction?

## Dependency decision

Phase 01B intentionally uses no mandatory third-party cabinet framework.

Current external options were either too old for a dependable Blender 5.2 public CI baseline, ambiguously licensed, or broader than Dwelling needs. Their design ideas remain useful references.
