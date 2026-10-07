import math
from blender.common import material, rounded_box

def build_sofa(location=(0, 0, 0), name_prefix="Sofa001"):
    ox, oy, oz = location
    linen = material("Sofa001 Linen", (0.62, 0.57, 0.48), 0.92)
    linen_dark = material("Sofa001 Seam", (0.46, 0.41, 0.34), 0.88)
    wood = material("Sofa001 Walnut Leg", (0.12, 0.065, 0.035), 0.48)
    shadow = material("Sofa001 Shadow Gap", (0.055, 0.045, 0.04), 0.72)

    objects = []

    def box(suffix, loc, dims, mat, bevel=0.04, segments=5, rot=(0, 0, 0)):
        obj = rounded_box(
            f"{name_prefix}_{suffix}",
            (ox + loc[0], oy + loc[1], oz + loc[2]),
            dims, mat, bevel, segments, rot
        )
        objects.append(obj)
        return obj

    # Structural body.
    box("Base", (0, 0.03, 0.27), (2.05, 0.78, 0.22), linen, 0.07, 6)
    box("ShadowGap", (0, -0.015, 0.145), (1.84, 0.66, 0.065), shadow, 0.018, 3)
    box("BackShell", (0, 0.375, 0.59), (1.91, 0.18, 0.68), linen, 0.065, 6)

    # Arms use a slightly taller profile than the seat cushion.
    for side, x in (("L", -1.035), ("R", 1.035)):
        box(f"Arm_{side}", (x, 0.015, 0.52), (0.18, 0.91, 0.57), linen, 0.075, 7)

    # Two independent seat cushions with a subtle splay.
    seat_specs = [
        ("L", -0.48, math.radians(0.6)),
        ("R", 0.48, math.radians(-0.6)),
    ]
    for side, x, rz in seat_specs:
        box(f"Seat_{side}", (x, -0.055, 0.49), (0.91, 0.70, 0.20), linen, 0.105, 8, (0, 0, rz))
        # Fine front seam; intentionally geometry rather than baked lighting.
        box(f"SeatSeam_{side}", (x, -0.405, 0.505), (0.80, 0.022, 0.025), linen_dark, 0.010, 3)

    # Back cushions lean slightly into the sofa.
    for side, x, rz in seat_specs:
        box(
            f"BackCushion_{side}",
            (x, 0.235, 0.735),
            (0.89, 0.19, 0.50),
            linen,
            0.105,
            8,
            (math.radians(-7), 0, rz),
        )
        box(f"BackSeam_{side}", (x, 0.135, 0.735), (0.76, 0.022, 0.34), linen_dark, 0.010, 3)

    # Four tapered-looking feet approximated with small rotated blocks.
    for sx in (-0.87, 0.87):
        for sy in (-0.27, 0.27):
            box(
                f"Leg_{'L' if sx < 0 else 'R'}_{'F' if sy < 0 else 'B'}",
                (sx, sy, 0.075),
                (0.095, 0.095, 0.15),
                wood,
                0.016,
                3,
                (0, math.radians(5 if sx < 0 else -5), 0),
            )

    return {
        "name": "sofa-001",
        "front_axis": "-Y",
        "nominal_dimensions_m": [2.16, 0.93, 0.86],
        "objects": objects,
    }
