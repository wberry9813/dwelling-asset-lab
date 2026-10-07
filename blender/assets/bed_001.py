import math
from blender.common import material, rounded_box, superellipsoid, draped_sheet

def build_bed(location=(0, 0, 0), name_prefix="Bed001"):
    ox, oy, oz = location

    oak = material("Bed001 Natural Oak", (0.28, 0.16, 0.07), 0.56)
    mattress_mat = material("Bed001 Mattress", (0.68, 0.65, 0.59), 0.95)
    sheet = material("Bed001 Sheet", (0.79, 0.77, 0.71), 0.98)
    duvet_mat = material("Bed001 Duvet", (0.56, 0.50, 0.43), 0.97)
    accent = material("Bed001 Throw", (0.24, 0.16, 0.11), 0.95)
    shadow = material("Bed001 Shadow Gap", (0.035, 0.030, 0.028), 0.78)

    objects = []

    def box(suffix, loc, dims, mat, bevel=0.04, segments=5, rot=(0, 0, 0)):
        obj = rounded_box(
            f"{name_prefix}_{suffix}",
            (ox + loc[0], oy + loc[1], oz + loc[2]),
            dims, mat, bevel, segments, rot
        )
        objects.append(obj)
        return obj

    def soft(suffix, loc, dims, mat, nxy=4.0, nz=3.0, rot=(0, 0, 0), deform=None):
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

    def pillow_deform(x, y, z, a, b, c):
        # A shallow central depression and fuller corners give a much more
        # pillow-like silhouette without using a cloth simulation.
        if z > 0:
            r2 = (x / max(a, 1e-6)) ** 2 + (y / max(b, 1e-6)) ** 2
            z -= 0.030 * math.exp(-r2 / 0.28)
        return x, y, z

    # Hard structure.
    box("Frame", (0, 0.00, 0.23), (1.96, 2.10, 0.28), oak, 0.045, 5)
    box("ShadowPlinth", (0, 0.02, 0.040), (1.68, 1.82, 0.08), shadow, 0.016, 3)
    box("Headboard", (0, 0.99, 0.84), (1.98, 0.12, 1.36), oak, 0.045, 5)

    # Mattress retains a stable geometric footprint; textile layers above it
    # are intentionally softer and less symmetrical.
    box("Mattress", (0, -0.03, 0.48), (1.82, 1.92, 0.25), mattress_mat, 0.095, 8)
    box("BottomSheet", (0, -0.04, 0.625), (1.78, 1.86, 0.07), sheet, 0.055, 7)

    duvet = draped_sheet(
        f"{name_prefix}_Duvet",
        (ox, oy - 0.11, oz + 0.755),
        width=1.77,
        depth=1.50,
        mat=duvet_mat,
        top_z=0.0,
        side_drop=0.075,
        foot_drop=0.27,
        foot_start=-0.34,
        nx=43,
        ny=47,
        thickness=0.040,
        wrinkle=0.010,
    )
    objects.append(duvet)

    # Pillows sit with slight non-uniform rotations and real soft volume.
    soft(
        "Pillow_L",
        (-0.43, 0.53, 0.785),
        (0.73, 0.43, 0.19),
        sheet,
        3.6,
        2.8,
        (math.radians(-8), math.radians(2), math.radians(-4)),
        pillow_deform,
    )
    soft(
        "Pillow_R",
        (0.40, 0.50, 0.795),
        (0.73, 0.43, 0.19),
        sheet,
        3.6,
        2.8,
        (math.radians(-9), math.radians(-2), math.radians(5)),
        pillow_deform,
    )

    throw = draped_sheet(
        f"{name_prefix}_Throw",
        (ox, oy - 0.52, oz + 0.835),
        width=1.68,
        depth=0.48,
        mat=accent,
        top_z=0.0,
        side_drop=0.045,
        foot_drop=0.065,
        foot_start=-0.08,
        nx=39,
        ny=25,
        thickness=0.030,
        wrinkle=0.008,
        rotation=(0, 0, math.radians(1.2)),
    )
    objects.append(throw)

    return {
        "name": "bed-001",
        "version": "0.2",
        "front_axis": "-Y",
        "nominal_dimensions_m": [1.98, 2.10, 1.52],
        "objects": objects,
    }
