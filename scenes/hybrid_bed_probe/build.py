import bpy
import json
import math
import pathlib
import sys
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender.common import material, rounded_box, point_at

SRC = ROOT / "build" / "hybrid_bed_probe" / "source"
OUT = ROOT / "build" / "hybrid_bed_probe" / "result"
OUT.mkdir(parents=True, exist_ok=True)

metadata = json.loads((SRC / "source-metadata.json").read_text())
source_path = pathlib.Path(metadata["downloadedFile"])
if not source_path.is_absolute():
    source_path = ROOT / source_path

bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------------------------------------------------------------------
# Import and split the CC0 reference source.
# ---------------------------------------------------------------------------

with bpy.data.libraries.load(str(source_path), link=False) as (src, dst):
    dst.objects = list(src.objects)
for obj in dst.objects:
    if obj is not None:
        bpy.context.collection.objects.link(obj)

source_meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
for obj in list(source_meshes):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")

parts = [o for o in bpy.context.scene.objects if o.type == "MESH"]

def recenter_origin(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

def size_of(obj):
    return tuple(float(v) for v in obj.dimensions)

for p in parts:
    recenter_origin(p)

# Identify likely soft candidates by geometry proportions.
surface_candidates = [
    p for p in parts
    if size_of(p)[0] > 1.5
    and size_of(p)[1] > 0.5
    and size_of(p)[2] < 0.35
]
pillow_candidates = [
    p for p in parts
    if 0.5 < size_of(p)[0] < 1.0
    and size_of(p)[1] > 0.45
    and 0.18 < size_of(p)[2] < 0.45
]

if not surface_candidates or not pillow_candidates:
    raise RuntimeError(
        f"Unable to classify reference soft parts: surfaces={len(surface_candidates)} pillows={len(pillow_candidates)}"
    )

# Prefer the more detailed wide soft surface.
duvet_src = sorted(
    surface_candidates,
    key=lambda o: len(o.data.polygons),
    reverse=True,
)[0]
pillow_src = sorted(
    pillow_candidates,
    key=lambda o: len(o.data.polygons),
    reverse=True,
)[0]

# Duplicate selected source geometry before removing the full reference asset.
duvet = duvet_src.copy()
duvet.data = duvet_src.data.copy()
bpy.context.collection.objects.link(duvet)

pillow_l = pillow_src.copy()
pillow_l.data = pillow_src.data.copy()
bpy.context.collection.objects.link(pillow_l)

pillow_r = pillow_src.copy()
pillow_r.data = pillow_src.data.copy()
bpy.context.collection.objects.link(pillow_r)

for obj in parts:
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------------------
# Dwelling modern hard structure.
# ---------------------------------------------------------------------------

oak = material("HybridBed Natural Oak", (0.27, 0.15, 0.065), 0.55)
mattress_mat = material("HybridBed Mattress", (0.73, 0.70, 0.64), 0.94)
linen = material("HybridBed Linen", (0.54, 0.49, 0.42), 0.97)
sheet = material("HybridBed Sheet", (0.82, 0.80, 0.75), 0.98)
shadow = material("HybridBed Shadow", (0.035, 0.03, 0.028), 0.78)

frame = rounded_box("HybridBed_Frame", (0, 0, 0.23), (1.98, 2.10, 0.28), oak, 0.045, 5)
plinth = rounded_box("HybridBed_Plith", (0, 0.02, 0.045), (1.70, 1.84, 0.09), shadow, 0.016, 3)
headboard = rounded_box("HybridBed_Headboard", (0, 0.995, 0.82), (1.98, 0.11, 1.30), oak, 0.045, 5)
mattress = rounded_box("HybridBed_Mattress", (0, -0.03, 0.49), (1.84, 1.92, 0.28), mattress_mat, 0.10, 8)
sheet_layer = rounded_box("HybridBed_FittedSheet", (0, -0.04, 0.635), (1.80, 1.88, 0.055), sheet, 0.045, 6)

# ---------------------------------------------------------------------------
# Reuse only the CC0 soft geometry, normalized into the modern bed.
# ---------------------------------------------------------------------------

for obj in (duvet, pillow_l, pillow_r):
    obj.data.materials.clear()
    obj.data.materials.append(linen)
    for poly in obj.data.polygons:
        poly.use_smooth = True

duvet.name = "HybridBed_Duvet_CC0Base"
duvet.dimensions = (1.78, 1.56, 0.18)
bpy.context.view_layer.objects.active = duvet
duvet.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
duvet.select_set(False)
duvet.location = (0.0, -0.18, 0.775)
duvet.rotation_euler = (math.radians(1.5), 0, math.radians(-0.7))

def setup_pillow(obj, name, loc, rot_z):
    obj.name = name
    obj.dimensions = (0.68, 0.44, 0.17)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = loc
    obj.rotation_euler = (math.radians(-8), math.radians(2 if loc[0] < 0 else -2), math.radians(rot_z))

setup_pillow(pillow_l, "HybridBed_Pillow_L_CC0Base", (-0.40, 0.60, 0.79), -5)
setup_pillow(pillow_r, "HybridBed_Pillow_R_CC0Base", (0.40, 0.57, 0.80), 5)

# Add a very thin top textile sheet to soften the transition at the duvet edge.
top_sheet = rounded_box("HybridBed_TopSheetHint", (0, -0.12, 0.69), (1.76, 1.58, 0.025), sheet, 0.020, 5)

# ---------------------------------------------------------------------------
# Review lighting.
# ---------------------------------------------------------------------------

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE" if bpy.app.version >= (5, 0, 0) else "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1024
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

floor_mat = material("Review Floor", (0.48, 0.34, 0.22), 0.72)
wall_mat = material("Review Wall", (0.80, 0.77, 0.70), 0.86)
rounded_box("Review_Floor", (0, 0, -0.025), (5.2, 4.4, 0.05), floor_mat, 0.008, 2)
rounded_box("Review_BackWall", (0, 2.05, 1.45), (5.2, 0.08, 2.9), wall_mat, 0.01, 2)

world = bpy.data.worlds.new("Hybrid Bed World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.07, 0.055, 0.045, 1.0)
bg.inputs["Strength"].default_value = 0.20

bpy.ops.object.light_add(type="AREA", location=(-3.4, -3.7, 4.5))
key = bpy.context.object
key.data.energy = 800
key.data.size = 4.0
key.data.color = (1.0, 0.88, 0.75)
point_at(key, (0, 0, 0.65))

bpy.ops.object.light_add(type="AREA", location=(3.1, -0.6, 3.0))
fill = bpy.context.object
fill.data.energy = 180
fill.data.size = 3.0
fill.data.color = (0.83, 0.89, 1.0)
point_at(fill, (0, 0.1, 0.7))

bpy.ops.object.camera_add(location=(3.7, -4.6, 3.0))
cam = bpy.context.object
scene.camera = cam
cam.data.lens = 58
point_at(cam, (0, 0.0, 0.65))
scene.render.filepath = str(OUT / "hybrid-bed-3q.png")
bpy.ops.render.render(write_still=True)

cam.location = (3.8, -0.05, 2.0)
point_at(cam, (0, 0.0, 0.62))
scene.render.filepath = str(OUT / "hybrid-bed-side.png")
bpy.ops.render.render(write_still=True)

# Save/export prototype for inspection only.
blend_path = OUT / "hybrid-bed-prototype.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

# Export only bed objects, not review shell/lights/camera.
bed_objects = [
    frame, plinth, headboard, mattress, sheet_layer, top_sheet,
    duvet, pillow_l, pillow_r,
]
bpy.ops.object.select_all(action="DESELECT")
for o in bed_objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = frame
glb_path = OUT / "hybrid-bed-prototype.glb"
bpy.ops.export_scene.gltf(
    filepath=str(glb_path),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
)

report = {
    "status": "pass",
    "source": metadata,
    "selectedSoftParts": {
        "duvetSourcePolygons": len(duvet_src.data.polygons) if duvet_src.name in bpy.data.objects else None,
        "pillowSourceDimensionsBeforeNormalize": [round(v, 4) for v in size_of(pillow_src)] if pillow_src.name in bpy.data.objects else None,
    },
    "prototype": {
        "nominalDimensionsMeters": [1.98, 2.10, 1.47],
        "note": "Experimental CC0 soft-geometry transfer. Not a promoted production asset.",
    },
}
(OUT / "hybrid-bed-report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
