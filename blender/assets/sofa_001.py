import math
from blender.common import material, rounded_box, superellipsoid

def build_sofa(location=(0, 0, 0), name_prefix="Sofa001"):
    ox, oy, oz = location

    # Deliberately deeper values than the v0.1 review so form survives warm
    # lighting without turning into an all-white block.
    linen = material("Sofa001 Linen", (0.34, 0.29, 0.23), 0.93)
    seam = material("Sofa001 Seam", (0.20, 0.16, 0.12), 0.88)
    wood = material("Sofa001 Walnut Leg", (0.085, 0.040, 0.020), 0.50)
    shadow = material("Sofa001 Shadow Gap", (0.035, 0.030, 0.028), 0.78)

    objects = []

    def box(suffix, loc, dims, mat, bevel=0.04, segments=5, rot=(0, 0, 0)):
        obj = rounded_box(
            f"{name_prefix}_{suffix}",
            (ox + loc[0], oy + loc[1], oz + loc[2]),
            dims, mat, bevel, segments, rot
        )
        objects.append(obj)
        return obj

    def soft(suffix, loc, dims, mat, nxy=4.4, nz=3.4, rot=(0, 0, 0), deform=None):
        obj = superellipsoid(
            f"{name_prefix}_{suffix}",
            (ox + loc[0], oy + loc[1], oz + loc[2]),
            dims,
            mat,
            n_xy=nxy,
            n_z=nz,
            segments=64,
            rings=30,
            rotation=rot,
            deform=deform,
        )
        objects.append(obj)
        return obj

    def seat_deform(x, y, z, a, b, c):
        # Gentle body-weight depression and slightly relaxed front lip.
        if z > 0:
            cx = max(0.0, 1.0 - (x / a) ** 2)
            cy = max(0.0, 1.0 - (y / b) ** 2)
            z -= 0.030 * cx * cy
            front = max(0.0, -y / b)
            z -= 0.010 * front ** 4
        return x, y, z

    def back_deform(x, y, z, a, b, c):
        # Compress the visual center of each back cushion so it does not read
        # as an inflated rounded cube.
        center = max(0.0, 1.0 - (x / a) ** 2) * max(0.0, 1.0 - (z / c) ** 2)
        if y < 0:
            y += 0.018 * center
        return x, y, z

    # Structural body stays intentionally simple; softness belongs to the
    # upholstery pieces, not the load-bearing base.
    box("Base", (0, 0.025, 0.265), (2.03, 0.77, 0.21), linen, 0.065, 6)
    box("ShadowGap", (0, -0.01, 0.145), (1.84, 0.66, 0.055), shadow, 0.018, 3)
    box("BackShell", (0, 0.39, 0.565), (1.91, 0.14, 0.61), linen, 0.060, 6)

    # Soft arms: superellipsoid geometry produces continuously curved corners
    # instead of bevel bands.
    for side, x in (("L", -0.99), ("R", 0.99)):
        soft(f"Arm_{side}", (x, 0.015, 0.515), (0.18, 0.91, 0.56), linen, 5.6, 4.6)

    seat_specs = [
        ("L", -0.48, math.radians(0.45)),
        ("R", 0.48, math.radians(-0.45)),
    ]
    for side, x, rz in seat_specs:
        soft(
            f"Seat_{side}",
            (x, -0.055, 0.485),
            (0.91, 0.70, 0.22),
            linen,
            4.8,
            3.0,
            (0, 0, rz),
            seat_deform,
        )
        # Fine piping at the front edge; geometry remains neutral to lighting.
        box(f"Piping_{side}", (x, -0.405, 0.490), (0.76, 0.014, 0.018), seam, 0.006, 3)

    for side, x, rz in seat_specs:
        soft(
            f"BackCushion_{side}",
            (x, 0.235, 0.680),
            (0.89, 0.205, 0.43),
            linen,
            4.7,
            3.2,
            (math.radians(-8), 0, rz),
            back_deform,
        )

    # Slightly splayed dark timber feet.
    for sx in (-0.87, 0.87):
        for sy in (-0.27, 0.27):
            box(
                f"Leg_{'L' if sx < 0 else 'R'}_{'F' if sy < 0 else 'B'}",
                (sx, sy, 0.080),
                (0.085, 0.085, 0.15),
                wood,
                0.012,
                3,
                (0, math.radians(6 if sx < 0 else -6), 0),
            )

    return {
        "name": "sofa-001",
        "version": "0.2",
        "front_axis": "-Y",
        "nominal_dimensions_m": [2.16, 0.91, 0.91],
        "objects": objects,
    }
