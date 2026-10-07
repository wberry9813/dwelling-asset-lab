import bpy
import json
import math
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "build")
os.makedirs(OUT, exist_ok=True)

# Clean factory scene.
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, roughness=0.55, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m

WOOD = mat("Warm Oak", (0.48, 0.25, 0.10), 0.48)
WALL = mat("Warm White", (0.82, 0.78, 0.69), 0.72)
FLOOR = mat("Light Oak Floor", (0.56, 0.35, 0.17), 0.58)
GREEN = mat("Muted Olive", (0.18, 0.28, 0.12), 0.68)
FABRIC = mat("Warm Linen", (0.72, 0.68, 0.58), 0.9)
DARK = mat("Dark Metal", (0.035, 0.045, 0.05), 0.28, 0.35)

def cube(name, loc, scale, material, bevel=0.02):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = o.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    o.data.materials.append(material)
    return o

# 8.4 m x 6.2 m compact apartment shell; open front for isometric review.
cube("Floor", (0, 0, 0.06), (8.4, 6.2, 0.12), FLOOR, 0.01)
for name, loc, size in [
    ("Wall_Back", (0, 3.0, 1.4), (8.4, .2, 2.8)),
    ("Wall_Left", (-4.1, 0, 1.4), (.2, 6.2, 2.8)),
    ("Wall_Right", (4.1, 0, 1.4), (.2, 6.2, 2.8)),
    ("Bedroom_Divider", (1.25, 1.45, 1.4), (.16, 3.0, 2.8)),
    ("Wet_Divider", (-1.7, 1.65, 1.4), (2.9, .16, 2.8)),
]:
    cube(name, loc, size, WALL, 0.015)

# Living room benchmark furniture.
cube("Sofa_Base", (1.65, -0.55, .36), (2.25, .88, .42), FABRIC, .07)
cube("Sofa_Back", (1.65, -0.18, .82), (2.25, .16, .75), FABRIC, .06)
for x in (0.65, 2.65):
    cube("Sofa_Arm", (x, -0.55, .63), (.22, .88, .58), FABRIC, .06)
cube("TV_Console", (3.25, -1.65, .32), (1.75, .42, .55), WOOD, .035)
cube("TV", (3.25, -1.58, 1.13), (1.5, .07, .86), DARK, .018)
cube("Coffee_Table", (1.7, -1.72, .31), (1.35, .72, .12), WOOD, .06)

# Dining benchmark.
cube("Dining_Table", (-.45, -1.45, .75), (1.45, .85, .08), WOOD, .035)
for x in (-1.0, .1):
    for y in (-2.05, -.85):
        cube("Dining_Chair", (x, y, .45), (.42, .42, .82), WOOD, .035)

# Bedroom benchmark.
cube("Bed_Frame", (2.55, 1.72, .28), (2.05, 2.15, .32), WOOD, .04)
cube("Mattress", (2.55, 1.72, .52), (1.9, 2.02, .28), FABRIC, .09)
cube("Headboard", (2.55, 2.68, 1.02), (2.05, .13, 1.12), WOOD, .035)

# Kitchen benchmark modules.
for i in range(4):
    cube(f"Kitchen_Base_{i+1}", (-3.55 + i*.62, .25, .45), (.58, .62, .88), GREEN, .025)
cube("Kitchen_Counter", (-2.62, .25, .92), (2.45, .68, .08), WALL, .02)

# Bathroom benchmark.
cube("Vanity", (-3.2, 2.15, .45), (1.05, .52, .82), WOOD, .03)
cube("Vanity_Top", (-3.2, 2.15, .89), (1.1, .57, .08), WALL, .02)

# Lighting.
bpy.ops.object.light_add(type="AREA", location=(0, -0.5, 6.5))
key = bpy.context.object
key.name = "Key_Light"
key.data.energy = 1300
key.data.shape = "DISK"
key.data.size = 5.0

bpy.ops.object.light_add(type="AREA", location=(-4.5, -4.0, 3.8))
fill = bpy.context.object
fill.data.energy = 750
fill.data.size = 4.0
fill.rotation_euler = (math.radians(55), 0, math.radians(-35))

# Camera.
bpy.ops.object.camera_add(location=(10.5, -11.5, 10.2))
cam = bpy.context.object
bpy.context.scene.camera = cam
cam.data.type = "ORTHO"
cam.data.ortho_scale = 11.6

def point_at(obj, target=(0, 0, .5)):
    import mathutils
    direction = mathutils.Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

point_at(cam)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = os.path.join(OUT, "preview-isometric.png")
scene.world.color = (0.055, 0.045, 0.035)

# Save source asset.
blend_path = os.path.join(OUT, "dwelling-apartment-001.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

# Export runtime GLB.
glb_path = os.path.join(OUT, "dwelling-apartment-001.glb")
bpy.ops.export_scene.gltf(filepath=glb_path, export_format="GLB")

# Render review image.
bpy.ops.render.render(write_still=True)

meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
report = {
    "asset": "dwelling-apartment-001",
    "unit_system": "METRIC",
    "mesh_objects": len(meshes),
    "materials": len(bpy.data.materials),
    "dimensions_m": [8.4, 6.2, 2.8],
    "outputs": [os.path.basename(blend_path), os.path.basename(glb_path), "preview-isometric.png"],
    "status": "pass" if len(meshes) >= 20 else "fail",
}
with open(os.path.join(OUT, "validation.json"), "w") as f:
    json.dump(report, f, indent=2)

if report["status"] != "pass":
    raise RuntimeError("Apartment validation failed")
print(json.dumps(report, indent=2))
