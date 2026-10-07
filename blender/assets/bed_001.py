import math
from blender.common import material, rounded_box

def build_bed(location=(0, 0, 0), name_prefix="Bed001"):
    ox, oy, oz = location
    oak = material("Bed001 Natural Oak", (0.46, 0.27, 0.12), 0.54)
    linen = material("Bed001 Warm Linen", (0.79, 0.75, 0.68), 0.96)
    sheet = material("Bed001 Sheet", (0.90, 0.88, 0.83), 0.98)
    accent = material("Bed001 Throw", (0.37, 0.27, 0.20), 0.94)
    shadow = material("Bed001 Shadow Gap", (0.055, 0.045, 0.04), 0.76)

    objects = []

    def box(suffix, loc, dims, mat, bevel=0.04, segments=5, rot=(0, 0, 0)):
        obj = rounded_box(
            f"{name_prefix}_{suffix}",
            (ox + loc[0], oy + loc[1], oz + loc[2]),
            dims, mat, bevel, segments, rot
        )
        objects.append(obj)
        return obj

    # Frame and recessed plinth.
    box("Frame", (0, 0.00, 0.23), (1.96, 2.10, 0.28), oak, 0.045, 5)
    box("ShadowPlinth", (0, 0.02, 0.115), (1.68, 1.82, 0.09), shadow, 0.018, 3)
    box("Headboard", (0, 0.99, 0.84), (1.98, 0.12, 1.36), oak, 0.055, 5)

    # Mattress and sheet layer.
    box("Mattress", (0, -0.03, 0.48), (1.82, 1.92, 0.25), linen, 0.105, 8)
    box("BottomSheet", (0, -0.04, 0.625), (1.78, 1.86, 0.08), sheet, 0.075, 7)

    # Duvet is composed of a top body plus a soft foot drop. The overlap hides
    # the procedural seam while creating a more textile-like silhouette.
    box("DuvetTop", (0, -0.18, 0.73), (1.76, 1.46, 0.19), linen, 0.13, 9, (math.radians(1.2), 0, 0))
    box("DuvetFootDrop", (0, -0.865, 0.57), (1.74, 0.18, 0.45), linen, 0.105, 8, (math.radians(-4), 0, 0))

    # Two pillows, deliberately not perfectly symmetrical.
    box("Pillow_L", (-0.43, 0.53, 0.77), (0.73, 0.43, 0.17), sheet, 0.095, 9, (math.radians(-7), 0, math.radians(-3)))
    box("Pillow_R", (0.40, 0.51, 0.78), (0.73, 0.43, 0.17), sheet, 0.095, 9, (math.radians(-8), 0, math.radians(4)))

    # Folded throw at the foot tests layered textile/material response.
    box("Throw", (0, -0.56, 0.855), (1.72, 0.45, 0.075), accent, 0.055, 6, (0, 0, math.radians(1.5)))

    return {
        "name": "bed-001",
        "front_axis": "-Y",
        "nominal_dimensions_m": [1.98, 2.10, 1.52],
        "objects": objects,
    }
