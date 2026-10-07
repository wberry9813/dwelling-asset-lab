import bpy
import math

from blender.common import material, rounded_box, cylinder

MODULE_WIDTH = 0.600
BODY_DEPTH = 0.560
CARCASS_HEIGHT = 0.770
PLINTH_HEIGHT = 0.100
OVERALL_HEIGHT = PLINTH_HEIGHT + CARCASS_HEIGHT

PANEL = 0.018
BACK = 0.006
DOOR = 0.019
REVEAL = 0.002
CENTER_GAP = 0.003

def _parent_keep_world(obj, parent):
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world

def build_kitchen_base_600(location=(0, 0, 0), name_prefix="KitchenBase600"):
    ox, oy, oz = location

    carcass_mat = material("Cabinet Birch Interior", (0.54, 0.36, 0.19), 0.62)
    front_mat = material("Cabinet Muted Olive", (0.18, 0.255, 0.145), 0.55)
    edge_mat = material("Cabinet Edge Shadow", (0.065, 0.060, 0.050), 0.74)
    metal_mat = material("Cabinet Dark Hardware", (0.035, 0.040, 0.042), 0.26, 0.38)

    objects = []
    semantic = {}

    def box(suffix, loc, dims, mat, bevel=0.0015, segments=3):
        obj = rounded_box(
            f"{name_prefix}_{suffix}",
            (ox + loc[0], oy + loc[1], oz + loc[2]),
            dims,
            mat,
            bevel,
            segments,
        )
        objects.append(obj)
        semantic[suffix] = obj
        return obj

    inner_width = MODULE_WIDTH - 2 * PANEL
    body_center_z = PLINTH_HEIGHT + CARCASS_HEIGHT / 2
    body_bottom = PLINTH_HEIGHT
    body_top = PLINTH_HEIGHT + CARCASS_HEIGHT

    # Casework panels.
    box(
        "Carcass_Left",
        (-MODULE_WIDTH / 2 + PANEL / 2, 0, body_center_z),
        (PANEL, BODY_DEPTH, CARCASS_HEIGHT),
        carcass_mat,
    )
    box(
        "Carcass_Right",
        (MODULE_WIDTH / 2 - PANEL / 2, 0, body_center_z),
        (PANEL, BODY_DEPTH, CARCASS_HEIGHT),
        carcass_mat,
    )
    box(
        "Carcass_Bottom",
        (0, 0, body_bottom + PANEL / 2),
        (inner_width, BODY_DEPTH, PANEL),
        carcass_mat,
    )

    # Front/back stretchers leave the top visually credible under a future
    # continuous Dwelling countertop without baking a countertop into module width.
    stretcher_depth = 0.075
    box(
        "Stretcher_Front",
        (0, -BODY_DEPTH / 2 + stretcher_depth / 2, body_top - PANEL / 2),
        (inner_width, stretcher_depth, PANEL),
        carcass_mat,
    )
    box(
        "Stretcher_Back",
        (0, BODY_DEPTH / 2 - stretcher_depth / 2, body_top - PANEL / 2),
        (inner_width, stretcher_depth, PANEL),
        carcass_mat,
    )

    # Recessed back and adjustable shelf.
    box(
        "Back",
        (0, BODY_DEPTH / 2 - PANEL - BACK / 2, body_center_z),
        (inner_width, BACK, CARCASS_HEIGHT - 2 * PANEL),
        carcass_mat,
        bevel=0.0005,
        segments=2,
    )
    box(
        "Shelf",
        (0, 0.020, PLINTH_HEIGHT + 0.390),
        (inner_width - 0.004, BODY_DEPTH - 0.050, PANEL),
        carcass_mat,
    )

    # Recessed toe kick. It intentionally stops short of the 600 mm module width
    # so adjacent cabinets form a continuous run without doubled visible edges.
    kick_y = -BODY_DEPTH / 2 + 0.060
    box(
        "ToeKick",
        (0, kick_y, PLINTH_HEIGHT / 2),
        (MODULE_WIDTH - 0.040, PANEL, PLINTH_HEIGHT),
        edge_mat,
        bevel=0.001,
        segments=2,
    )

    # Four hidden adjustable legs reinforce believable construction.
    for sx in (-0.225, 0.225):
        for sy in (-0.175, 0.175):
            leg = cylinder(
                f"{name_prefix}_Leg_{'L' if sx < 0 else 'R'}_{'F' if sy < 0 else 'B'}",
                (ox + sx, oy + sy, oz + PLINTH_HEIGHT / 2),
                0.022,
                PLINTH_HEIGHT,
                metal_mat,
                vertices=32,
                bevel=0.003,
            )
            objects.append(leg)

    # Door pivots are first-class semantics. Front axis = -Y.
    left_pivot = bpy.data.objects.new(f"{name_prefix}_DoorPivot_L", None)
    left_pivot.empty_display_type = "PLAIN_AXES"
    left_pivot.location = (
        ox - MODULE_WIDTH / 2 + REVEAL,
        oy - BODY_DEPTH / 2 - DOOR / 2,
        oz + body_center_z,
    )
    bpy.context.collection.objects.link(left_pivot)
    objects.append(left_pivot)

    right_pivot = bpy.data.objects.new(f"{name_prefix}_DoorPivot_R", None)
    right_pivot.empty_display_type = "PLAIN_AXES"
    right_pivot.location = (
        ox + MODULE_WIDTH / 2 - REVEAL,
        oy - BODY_DEPTH / 2 - DOOR / 2,
        oz + body_center_z,
    )
    bpy.context.collection.objects.link(right_pivot)
    objects.append(right_pivot)

    door_width = (MODULE_WIDTH - 2 * REVEAL - CENTER_GAP) / 2
    door_height = CARCASS_HEIGHT - 2 * REVEAL
    door_y = -BODY_DEPTH / 2 - DOOR / 2
    door_z = body_center_z

    left_center_x = -MODULE_WIDTH / 2 + REVEAL + door_width / 2
    right_center_x = MODULE_WIDTH / 2 - REVEAL - door_width / 2

    left_door = box(
        "Door_L",
        (left_center_x, door_y, door_z),
        (door_width, DOOR, door_height),
        front_mat,
        bevel=0.006,
        segments=5,
    )
    right_door = box(
        "Door_R",
        (right_center_x, door_y, door_z),
        (door_width, DOOR, door_height),
        front_mat,
        bevel=0.006,
        segments=5,
    )
    _parent_keep_world(left_door, left_pivot)
    _parent_keep_world(right_door, right_pivot)

    # Vertical bar pulls near the meeting stile.
    handle_h = 0.160
    handle_x_offset = 0.030
    handle_y = -BODY_DEPTH / 2 - DOOR - 0.012
    handle_z = body_top - 0.160

    left_handle = box(
        "Handle_L",
        (-CENTER_GAP / 2 - handle_x_offset, handle_y, handle_z),
        (0.014, 0.020, handle_h),
        metal_mat,
        bevel=0.004,
        segments=4,
    )
    right_handle = box(
        "Handle_R",
        (CENTER_GAP / 2 + handle_x_offset, handle_y, handle_z),
        (0.014, 0.020, handle_h),
        metal_mat,
        bevel=0.004,
        segments=4,
    )
    _parent_keep_world(left_handle, left_pivot)
    _parent_keep_world(right_handle, right_pivot)

    # Small hinge plates are visible in the open-door review.
    hinge_zs = (body_bottom + 0.120, body_top - 0.120)
    for side, x in (("L", -MODULE_WIDTH / 2 + PANEL + 0.010), ("R", MODULE_WIDTH / 2 - PANEL - 0.010)):
        for idx, z in enumerate(hinge_zs):
            hinge = box(
                f"Hinge_{side}_{idx+1}",
                (x, -BODY_DEPTH / 2 + 0.018, z),
                (0.035, 0.012, 0.050),
                metal_mat,
                bevel=0.003,
                segments=3,
            )

    return {
        "name": "kitchen-base-600",
        "version": "0.1",
        "front_axis": "-Y",
        "module_width_m": MODULE_WIDTH,
        "nominal_dimensions_m": [MODULE_WIDTH, 0.601, OVERALL_HEIGHT],
        "installation_footprint_m": [MODULE_WIDTH, BODY_DEPTH, OVERALL_HEIGHT],
        "objects": objects,
        "meshes": [o for o in objects if o.type == "MESH"],
        "door_pivots": [left_pivot, right_pivot],
        "semantic": semantic,
    }
