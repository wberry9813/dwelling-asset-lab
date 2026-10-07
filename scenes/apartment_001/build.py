import bpy
import json
import math
import os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "build")
os.makedirs(OUT, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------

def material(name, color, roughness=0.55, metallic=0.0, transmission=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, alpha)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if "Transmission Weight" in bsdf.inputs:
        bsdf.inputs["Transmission Weight"].default_value = transmission
    if transmission > 0:
        bsdf.inputs["IOR"].default_value = 1.45
    return m

WALL = material("Warm Plaster", (0.86, 0.83, 0.76), 0.78)
FLOOR = material("Light Oak Floor", (0.52, 0.34, 0.18), 0.56)
OAK = material("Natural Oak", (0.53, 0.31, 0.14), 0.50)
DARK_WOOD = material("Dark Walnut", (0.18, 0.09, 0.045), 0.48)
OLIVE = material("Muted Olive", (0.22, 0.31, 0.15), 0.67)
LINEN = material("Warm Linen", (0.72, 0.67, 0.57), 0.92)
CREAM = material("Soft Cream", (0.91, 0.87, 0.78), 0.86)
BEDDING = material("Bedding", (0.78, 0.74, 0.67), 0.96)
DARK = material("Dark Metal", (0.035, 0.04, 0.045), 0.26, 0.35)
METAL = material("Brushed Metal", (0.32, 0.34, 0.35), 0.34, 0.72)
CERAMIC = material("Warm Ceramic", (0.93, 0.91, 0.86), 0.28)
RUG = material("Woven Rug", (0.47, 0.36, 0.28), 0.98)
GLASS = material("Window Glass", (0.50, 0.67, 0.72), 0.12, 0.0, 0.72)
PLANT = material("Plant Green", (0.10, 0.27, 0.09), 0.76)
TERRACOTTA = material("Terracotta", (0.44, 0.20, 0.105), 0.72)
ACCENT = material("Warm Accent", (0.52, 0.17, 0.095), 0.74)

# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def cube(name, loc, dims, mat, bevel=0.02, rot_z=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.rotation_euler[2] = math.radians(rot_z)
    if bevel > 0:
        mod = o.modifiers.new("Soft edges", "BEVEL")
        mod.width = min(bevel, min(dims) * 0.35)
        mod.segments = 3
    o.data.materials.append(mat)
    return o

def cylinder(name, loc, radius, depth, mat, vertices=48, bevel=0.015):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    o = bpy.context.object
    o.name = name
    if bevel > 0:
        mod = o.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    o.data.materials.append(mat)
    return o

def sphere(name, loc, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    return o

def point_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def chair(name, x, y, rot=0):
    cube(f"{name}_Seat", (x, y, 0.48), (0.46, 0.48, 0.10), OAK, 0.035, rot)
    back_offset = Vector((0, 0.19))
    ang = math.radians(rot)
    dx = back_offset.x * math.cos(ang) - back_offset.y * math.sin(ang)
    dy = back_offset.x * math.sin(ang) + back_offset.y * math.cos(ang)
    cube(f"{name}_Back", (x + dx, y + dy, 0.78), (0.46, 0.08, 0.58), OAK, 0.035, rot)
    for sx in (-0.17, 0.17):
        for sy in (-0.17, 0.17):
            rx = sx * math.cos(ang) - sy * math.sin(ang)
            ry = sx * math.sin(ang) + sy * math.cos(ang)
            cube(f"{name}_Leg", (x + rx, y + ry, 0.245), (0.045, 0.045, 0.43), DARK_WOOD, 0.01)

def add_plant(name, x, y, z=0.0, scale=1.0):
    cylinder(f"{name}_Pot", (x, y, z + 0.18 * scale), 0.18 * scale, 0.36 * scale, TERRACOTTA, 36, 0.018)
    sphere(f"{name}_Leaf_A", (x, y, z + 0.65 * scale), (0.22 * scale, 0.18 * scale, 0.42 * scale), PLANT)
    sphere(f"{name}_Leaf_B", (x - 0.15 * scale, y + 0.03 * scale, z + 0.55 * scale), (0.16 * scale, 0.13 * scale, 0.32 * scale), PLANT)
    sphere(f"{name}_Leaf_C", (x + 0.14 * scale, y - 0.04 * scale, z + 0.59 * scale), (0.17 * scale, 0.14 * scale, 0.35 * scale), PLANT)

def wall_x(name, y, x1, x2, height=2.8, thickness=0.16):
    cube(name, ((x1 + x2) / 2, y, height / 2), (x2 - x1, thickness, height), WALL, 0.012)

def wall_y(name, x, y1, y2, height=2.8, thickness=0.16):
    cube(name, (x, (y1 + y2) / 2, height / 2), (thickness, y2 - y1, height), WALL, 0.012)

def horizontal_window(name, y, x_center, width, sill=0.92, height=1.22):
    # Window sits in an already-segmented X wall.
    zc = sill + height / 2
    cube(f"{name}_Glass", (x_center, y, zc), (width, 0.035, height), GLASS, 0.006)
    frame = 0.055
    cube(f"{name}_Frame_L", (x_center - width/2 + frame/2, y - 0.025, zc), (frame, 0.09, height + 0.10), DARK, 0.01)
    cube(f"{name}_Frame_R", (x_center + width/2 - frame/2, y - 0.025, zc), (frame, 0.09, height + 0.10), DARK, 0.01)
    cube(f"{name}_Frame_T", (x_center, y - 0.025, sill + height), (width, 0.09, frame), DARK, 0.01)
    cube(f"{name}_Frame_B", (x_center, y - 0.025, sill), (width, 0.09, frame), DARK, 0.01)
    cube(f"{name}_Mullion", (x_center, y - 0.03, zc), (frame, 0.10, height), DARK, 0.01)
    cube(f"{name}_Sill", (x_center, y - 0.11, sill - 0.035), (width + 0.16, 0.22, 0.07), OAK, 0.02)

def door_frame_x(name, y, x_center, width=0.86, height=2.15):
    t = 0.07
    cube(f"{name}_Frame_L", (x_center-width/2, y, height/2), (t, 0.20, height), DARK_WOOD, 0.015)
    cube(f"{name}_Frame_R", (x_center+width/2, y, height/2), (t, 0.20, height), DARK_WOOD, 0.015)
    cube(f"{name}_Frame_T", (x_center, y, height), (width+t, 0.20, t), DARK_WOOD, 0.015)

def door_frame_y(name, x, y_center, width=0.86, height=2.15):
    t = 0.07
    cube(f"{name}_Frame_L", (x, y_center-width/2, height/2), (0.20, t, height), DARK_WOOD, 0.015)
    cube(f"{name}_Frame_R", (x, y_center+width/2, height/2), (0.20, t, height), DARK_WOOD, 0.015)
    cube(f"{name}_Frame_T", (x, y_center, height), (0.20, width+t, t), DARK_WOOD, 0.015)

# ---------------------------------------------------------------------------
# Architectural shell — 8.4 m x 6.2 m, approximately 52 m²
# ---------------------------------------------------------------------------

cube("Floor_Slab", (0, 0, 0.055), (8.4, 6.2, 0.11), FLOOR, 0.01)

# Back wall with a proper bedroom window opening.
wall_x("BackWall_Left", 3.0, -4.2, 1.78)
wall_x("BackWall_Window_Bottom", 3.0, 1.78, 3.52, height=0.92)
cube("BackWall_Window_Top", (2.65, 3.0, 2.56), (1.74, 0.16, 0.48), WALL, 0.012)
wall_x("BackWall_Right", 3.0, 3.52, 4.2)
horizontal_window("Bedroom_Window", 3.0, 2.65, 1.62, 0.92, 1.22)

# Left outer wall; full height retains the miniature-house silhouette.
wall_y("LeftWall", -4.1, -3.1, 3.1)

# Right side is intentionally cut to 1.15 m for review visibility.
wall_y("RightWall_Cutaway", 4.1, -3.1, 3.1, height=1.15)

# Bedroom divider at x=1.15 with an 0.9 m doorway.
wall_y("BedroomDivider_Front", 1.15, 0.55, 1.18)
wall_y("BedroomDivider_Back", 1.15, 2.08, 3.1)
door_frame_y("BedroomDoor", 1.15, 1.63, 0.90)
# Open door leaf.
cube("BedroomDoor_Leaf", (1.52, 1.83, 1.04), (0.06, 0.82, 2.06), OAK, 0.025, -38)

# Bathroom at rear centre-left, with door opening.
wall_y("Bathroom_Left", -1.35, 1.18, 3.1)
wall_x("Bathroom_Front_Left", 1.18, -1.35, -0.30)
wall_x("Bathroom_Front_Right", 1.18, 0.58, 1.15)
door_frame_x("BathroomDoor", 1.18, 0.14, 0.88)

# Baseboards add the first architectural detail layer.
for name, loc, dims in [
    ("Baseboard_BackL", (-1.1, 2.89, 0.08), (5.75, 0.035, 0.12)),
    ("Baseboard_Left", (-3.99, 0.0, 0.08), (0.035, 5.9, 0.12)),
    ("Baseboard_Bed", (1.25, 2.55, 0.08), (0.035, 0.78, 0.12)),
]:
    cube(name, loc, dims, CREAM, 0.008)

# ---------------------------------------------------------------------------
# Kitchen — modular, readable and credible
# ---------------------------------------------------------------------------

# Tall refrigerator and pantry.
cube("Fridge_Body", (-3.64, 1.55, 0.99), (0.68, 0.68, 1.92), CREAM, 0.05)
cube("Fridge_Door_Line", (-3.285, 1.55, 1.01), (0.025, 0.58, 1.65), DARK, 0.006)
cube("Pantry_Tall", (-2.94, 1.55, 1.05), (0.58, 0.62, 2.04), OLIVE, 0.035)

# Base cabinets along left/back zone.
cab_xs = [-3.64, -3.02, -2.40, -1.78]
for i, x in enumerate(cab_xs):
    cube(f"Kitchen_Base_{i+1}", (x, 0.48, 0.46), (0.58, 0.62, 0.86), OLIVE, 0.028)
    cube(f"Kitchen_Base_Handle_{i+1}", (x, 0.145, 0.68), (0.24, 0.025, 0.025), DARK, 0.006)

cube("Kitchen_Counter", (-2.71, 0.48, 0.925), (2.47, 0.69, 0.075), CERAMIC, 0.025)
cube("Kitchen_Backsplash", (-2.71, 0.805, 1.22), (2.47, 0.035, 0.55), CREAM, 0.008)

# Sink + faucet.
cube("Kitchen_Sink", (-3.10, 0.47, 0.955), (0.52, 0.38, 0.055), METAL, 0.03)
cylinder("Kitchen_Faucet_Base", (-3.10, 0.70, 1.05), 0.035, 0.18, METAL, 32, 0.006)
cube("Kitchen_Faucet_Neck", (-3.10, 0.70, 1.20), (0.05, 0.05, 0.28), METAL, 0.012)
cube("Kitchen_Faucet_Spout", (-3.10, 0.57, 1.31), (0.05, 0.27, 0.05), METAL, 0.012)

# Cooktop and hood.
cube("Cooktop", (-2.04, 0.45, 0.972), (0.54, 0.40, 0.025), DARK, 0.012)
cube("Hood", (-2.04, 0.72, 1.82), (0.65, 0.34, 0.18), DARK, 0.025)

# Upper cabinets.
for i, x in enumerate([-3.15, -2.48, -1.81]):
    cube(f"Kitchen_Upper_{i+1}", (x, 0.77, 1.72), (0.61, 0.31, 0.72), OLIVE, 0.025)
    cube(f"Kitchen_Upper_Handle_{i+1}", (x, 0.59, 1.55), (0.23, 0.02, 0.022), DARK, 0.005)

# ---------------------------------------------------------------------------
# Dining
# ---------------------------------------------------------------------------

cylinder("Dining_Table_Top", (-0.18, -0.85, 0.75), 0.72, 0.075, OAK, 64, 0.025)
cylinder("Dining_Table_Pedestal", (-0.18, -0.85, 0.39), 0.16, 0.68, DARK_WOOD, 48, 0.02)
cylinder("Dining_Table_Foot", (-0.18, -0.85, 0.08), 0.38, 0.07, DARK_WOOD, 48, 0.018)
chair("DiningChair_N", -0.18, 0.08, 180)
chair("DiningChair_S", -0.18, -1.78, 0)
chair("DiningChair_W", -1.15, -0.85, -90)
chair("DiningChair_E", 0.79, -0.85, 90)

# Small pendant over dining table.
cylinder("Pendant_Shade", (-0.18, -0.85, 2.35), 0.23, 0.20, DARK, 48, 0.02)
cube("Pendant_Cord", (-0.18, -0.85, 2.68), (0.018, 0.018, 0.48), DARK, 0.004)

# ---------------------------------------------------------------------------
# Living room
# ---------------------------------------------------------------------------

# Rug first so furniture reads as a composed zone.
cube("Living_Rug", (2.15, -1.10, 0.105), (3.15, 2.00, 0.035), RUG, 0.03)

# Sofa facing the TV on the right cutaway wall.
cube("Sofa_Platform", (1.02, -0.82, 0.31), (0.86, 2.15, 0.32), LINEN, 0.075)
cube("Sofa_Back", (0.70, -0.82, 0.76), (0.18, 2.15, 0.70), LINEN, 0.07)
cube("Sofa_Arm_N", (1.02, 0.16, 0.56), (0.86, 0.18, 0.50), LINEN, 0.065)
cube("Sofa_Arm_S", (1.02, -1.80, 0.56), (0.86, 0.18, 0.50), LINEN, 0.065)
cube("Sofa_Cushion_A", (1.18, -0.30, 0.56), (0.50, 0.78, 0.16), CREAM, 0.065)
cube("Sofa_Cushion_B", (1.18, -1.28, 0.56), (0.50, 0.78, 0.16), CREAM, 0.065)
cube("Sofa_Throw_Pillow", (1.06, -1.52, 0.78), (0.28, 0.36, 0.30), ACCENT, 0.08, 10)

# Coffee table.
cylinder("Coffee_Table_Top", (2.15, -1.00, 0.39), 0.56, 0.075, OAK, 64, 0.025)
cylinder("Coffee_Table_Leg", (2.15, -1.00, 0.21), 0.10, 0.34, DARK_WOOD, 36, 0.018)

# TV console and screen.
cube("TV_Console", (3.66, -0.90, 0.34), (0.48, 1.78, 0.54), OAK, 0.04)
cube("TV_Console_ShadowGap", (3.405, -0.90, 0.34), (0.018, 1.55, 0.36), DARK_WOOD, 0.005)
cube("TV_Screen", (3.72, -0.90, 1.22), (0.07, 1.45, 0.84), DARK, 0.018)
cube("TV_Screen_Inset", (3.675, -0.90, 1.22), (0.025, 1.34, 0.73), GLASS, 0.01)

# Floor lamp and plant.
cylinder("FloorLamp_Base", (2.78, 0.16, 0.06), 0.22, 0.06, DARK, 40, 0.015)
cube("FloorLamp_Stem", (2.78, 0.16, 0.86), (0.035, 0.035, 1.58), DARK, 0.008)
cylinder("FloorLamp_Shade", (2.78, 0.16, 1.72), 0.25, 0.36, CREAM, 48, 0.025)
add_plant("Living_Plant", 3.40, -2.20, 0, 1.15)

# ---------------------------------------------------------------------------
# Bedroom
# ---------------------------------------------------------------------------

cube("Bedroom_Rug", (2.66, 1.82, 0.105), (2.70, 2.12, 0.035), CREAM, 0.035)
cube("Bed_Frame", (2.70, 1.92, 0.28), (2.05, 1.98, 0.30), OAK, 0.045)
cube("Mattress", (2.70, 1.88, 0.53), (1.92, 1.88, 0.25), CREAM, 0.10)
cube("Duvet", (2.70, 1.66, 0.72), (1.86, 1.34, 0.18), BEDDING, 0.10)
cube("Headboard", (2.70, 2.69, 1.02), (2.05, 0.12, 1.10), OAK, 0.04)
cube("Pillow_L", (2.28, 2.37, 0.76), (0.65, 0.40, 0.16), CREAM, 0.09)
cube("Pillow_R", (3.12, 2.37, 0.76), (0.65, 0.40, 0.16), CREAM, 0.09)

for x in (1.48, 3.92):
    cube("Bedside_Table", (x, 2.38, 0.36), (0.42, 0.42, 0.58), OAK, 0.035)
    cylinder("Bedside_Lamp", (x, 2.38, 0.86), 0.13, 0.26, CREAM, 36, 0.02)

# Wardrobe along the right side.
cube("Wardrobe", (3.70, 1.05, 1.10), (0.62, 1.35, 2.10), CREAM, 0.035)
cube("Wardrobe_Gap", (3.37, 1.05, 1.10), (0.018, 1.16, 1.92), DARK_WOOD, 0.004)

# ---------------------------------------------------------------------------
# Bathroom
# ---------------------------------------------------------------------------

# Shower tray and glass.
cube("Shower_Tray", (-0.68, 2.48, 0.12), (1.12, 0.92, 0.10), CERAMIC, 0.025)
cube("Shower_Glass", (-0.10, 2.48, 1.12), (0.035, 0.92, 1.90), GLASS, 0.008)
cube("Shower_Rail", (-0.08, 2.84, 1.45), (0.035, 0.035, 1.20), METAL, 0.008)
cylinder("Shower_Head", (-0.08, 2.77, 1.98), 0.10, 0.06, METAL, 32, 0.008)

# Vanity, basin, mirror.
cube("Bathroom_Vanity", (0.55, 2.62, 0.45), (0.92, 0.48, 0.82), OAK, 0.035)
cube("Bathroom_Vanity_Top", (0.55, 2.62, 0.89), (0.98, 0.53, 0.07), CERAMIC, 0.025)
cube("Bathroom_Basin", (0.55, 2.56, 0.98), (0.52, 0.32, 0.16), CERAMIC, 0.055)
cube("Bathroom_Mirror", (0.55, 2.93, 1.62), (0.80, 0.035, 0.85), GLASS, 0.018)

# Toilet.
cylinder("Toilet_Base", (-0.72, 1.62, 0.28), 0.31, 0.48, CERAMIC, 48, 0.05)
cube("Toilet_Cistern", (-0.72, 1.92, 0.72), (0.54, 0.25, 0.68), CERAMIC, 0.055)
cube("Towel", (0.92, 1.74, 1.10), (0.045, 0.48, 0.62), CREAM, 0.025)

# ---------------------------------------------------------------------------
# Small props — enough to stop the room feeling sterile
# ---------------------------------------------------------------------------

for idx, (x, y, h, r) in enumerate([
    (-0.42, -0.77, 0.82, 0.045),
    (-0.14, -0.70, 0.83, 0.05),
    (2.02, -0.92, 0.47, 0.055),
]):
    cylinder(f"Cup_{idx+1}", (x, y, h), r, 0.10, CERAMIC, 32, 0.008)

cube("Book_1", (2.28, -1.08, 0.47), (0.30, 0.21, 0.035), ACCENT, 0.008, 10)
cube("Book_2", (2.29, -1.08, 0.51), (0.27, 0.19, 0.035), CREAM, 0.008, -4)
add_plant("Dining_Plant", -1.66, -2.20, 0, 0.82)

# ---------------------------------------------------------------------------
# Lighting
# ---------------------------------------------------------------------------

bpy.ops.object.light_add(type="AREA", location=(0.2, -0.2, 6.7))
key = bpy.context.object
key.name = "Key_Softbox"
key.data.energy = 1550
key.data.shape = "DISK"
key.data.size = 5.8

bpy.ops.object.light_add(type="AREA", location=(-5.2, -4.8, 4.8))
fill = bpy.context.object
fill.name = "Window_Fill"
fill.data.energy = 900
fill.data.size = 4.5
point_at(fill, (-0.6, -0.3, 0.8))

bpy.ops.object.light_add(type="AREA", location=(4.8, 4.2, 4.4))
rim = bpy.context.object
rim.name = "Warm_Rim"
rim.data.energy = 620
rim.data.size = 3.2
point_at(rim, (1.4, 1.0, 0.9))

# Warm practical lights.
for name, loc, energy in [
    ("Dining_Practical", (-0.18, -0.85, 2.18), 95),
    ("Bedroom_Practical", (2.70, 2.18, 2.35), 70),
]:
    bpy.ops.object.light_add(type="POINT", location=loc)
    lamp = bpy.context.object
    lamp.name = name
    lamp.data.energy = energy
    lamp.data.color = (1.0, 0.68, 0.42)
    lamp.data.shadow_soft_size = 0.45

# ---------------------------------------------------------------------------
# Render setup + multi-angle review
# ---------------------------------------------------------------------------

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False

world = bpy.data.worlds.new("Dwelling World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.045, 0.036, 0.030, 1.0)
bg.inputs["Strength"].default_value = 0.30

bpy.ops.object.camera_add(location=(10.6, -11.8, 10.0))
cam = bpy.context.object
cam.name = "Review_Camera"
scene.camera = cam

def render_view(filename, location, target, ortho_scale=None, lens=48):
    cam.location = location
    point_at(cam, target)
    if ortho_scale is None:
        cam.data.type = "PERSP"
        cam.data.lens = lens
    else:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = ortho_scale
    scene.render.filepath = os.path.join(OUT, filename)
    bpy.ops.render.render(write_still=True)

# Save editable source before rendering.
blend_path = os.path.join(OUT, "dwelling-apartment-001.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# Runtime export.
glb_path = os.path.join(OUT, "dwelling-apartment-001.glb")
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format="GLB",
    export_apply=True,
)

render_view("preview-isometric.png", (10.4, -11.6, 9.4), (0.0, 0.0, 0.75), 10.7)
render_view("preview-top.png", (0.0, -0.15, 14.0), (0.0, 0.0, 0.0), 9.2)
render_view("preview-living.png", (8.2, -8.4, 4.9), (0.65, -0.55, 0.85), None, 54)

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

meshes = [o for o in scene.objects if o.type == "MESH"]
mesh_stats = {
    "objects": len(meshes),
    "vertices": sum(len(o.data.vertices) for o in meshes),
    "polygons": sum(len(o.data.polygons) for o in meshes),
}

required = [
    blend_path,
    glb_path,
    os.path.join(OUT, "preview-isometric.png"),
    os.path.join(OUT, "preview-top.png"),
    os.path.join(OUT, "preview-living.png"),
]
missing = [os.path.basename(p) for p in required if not os.path.exists(p) or os.path.getsize(p) == 0]

report = {
    "asset": "dwelling-apartment-001",
    "version": "0.2",
    "style": "Warm Miniature Realism",
    "unit_system": "METRIC",
    "dimensions_m": [8.4, 6.2, 2.8],
    "mesh": mesh_stats,
    "materials": len(bpy.data.materials),
    "required_outputs": [os.path.basename(p) for p in required],
    "missing_outputs": missing,
    "status": "pass" if len(meshes) >= 80 and not missing else "fail",
}

with open(os.path.join(OUT, "validation.json"), "w") as fp:
    json.dump(report, fp, indent=2)

if report["status"] != "pass":
    raise RuntimeError(f"Apartment validation failed: {report}")

print(json.dumps(report, indent=2))
