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
drape_candidates = [
    p for p in parts
    if size_of(p)[0] > 1.5
    and size_of(p)[1] < 0.35
    and size_of(p)[2] > 0.45
]
pillow_candidates = [
    p for p in parts
    if 0.5 < size_of(p)[0] < 1.0
    and size_of(p)[1] > 0.45
    and 0.18 < size_of(p)[2] < 0.45
]

if not surface_candidates or not drape_candidates or not pillow_candidates:
    raise RuntimeError(
        "Unable to classify reference soft parts: "
        f"surfaces={len(surface_candidates)} drapes={len(drape_candidates)} pillows={len(pillow_candidates)}"
    )

# Use the actual vertically draped quilt island rather than the seat cushion.
duvet_src = sorted(
    drape_candidates,
    key=lambda o: len(o.data.polygons),
    reverse=True,
)[0]
pillow_src = sorted(
    pillow_candidates,
    key=lambda o: len(o.data.polygons),
    reverse=True,
)[0]

# Snapshot reference metrics before removing the full reference asset.
duvet_source_polygons = len(duvet_src.data.polygons)
pillow_source_dimensions = [round(v, 4) for v in size_of(pillow_src)]

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

oak = material("HybridBed Natural Oak", (0.24, 0.135, 0.060), 0.58)
mattress_mat = material("HybridBed Mattress", (0.72, 0.69, 0.63), 0.95)
linen = material("HybridBed Linen", (0.61, 0.57, 0.51), 0.97)
sheet = material("HybridBed Sheet", (0.84, 0.82, 0.78), 0.98)
shadow = material("HybridBed Shadow", (0.035, 0.03, 0.028), 0.78)

frame = rounded_box("HybridBed_Frame", (0, 0, 0.18), (1.98, 2.10, 0.20), oak, 0.040, 5)
plinth = rounded_box("HybridBed_Plith", (0, 0.02, 0.050), (1.72, 1.84, 0.10), shadow, 0.014, 3)
headboard = rounded_box("HybridBed_HeadboardBack", (0, 0.995, 0.79), (1.98, 0.10, 1.22), oak, 0.040, 5)
headboard_pad = rounded_box("HybridBed_HeadboardPad", (0, 0.925, 0.87), (1.82, 0.08, 0.80), linen, 0.080, 8)
mattress = rounded_box("HybridBed_Mattress", (0, -0.03, 0.43), (1.84, 1.92, 0.24), mattress_mat, 0.085, 8)
sheet_layer = rounded_box("HybridBed_FittedSheet", (0, -0.04, 0.554), (1.80, 1.88, 0.012), sheet, 0.009, 4)

# ---------------------------------------------------------------------------
# Reuse only the CC0 soft geometry, normalized into the modern bed.
# ---------------------------------------------------------------------------

for obj in (duvet, pillow_l, pillow_r):
    obj.data.materials.clear()
    obj.data.materials.append(linen)
    for poly in obj.data.polygons:
        poly.use_smooth = True

duvet.name = "HybridBed_Duvet_CC0DrapedBase"
# The source quilt hangs vertically over the day-bed back. Rotate that authored
# drape into a horizontal bedding orientation, then normalize dimensions.
bpy.ops.object.select_all(action="DESELECT")
duvet.select_set(True)
bpy.context.view_layer.objects.active = duvet
duvet.rotation_euler = (math.radians(90), 0, 0)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
duvet.dimensions = (1.76, 1.42, 0.060)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
duvet.select_set(False)
duvet.location = (0.0, -0.23, 0.630)
duvet.rotation_euler = (math.radians(0.8), 0, math.radians(-0.6))

def setup_pillow(obj, name, loc, rot_z):
    obj.name = name
    obj.dimensions = (0.70, 0.46, 0.16)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = loc
    obj.rotation_euler = (math.radians(-8), math.radians(2 if loc[0] < 0 else -2), math.radians(rot_z))

setup_pillow(pillow_l, "HybridBed_Pillow_L_CC0Base", (-0.40, 0.59, 0.680), -5)
setup_pillow(pillow_r, "HybridBed_Pillow_R_CC0Base", (0.40, 0.56, 0.690), 5)

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
    frame, plinth, headboard, headboard_pad, mattress, sheet_layer,
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
        "duvetSourcePolygons": duvet_source_polygons,
        "duvetSourceKind": "Poly Haven draped quilt loose part",
        "pillowSourceDimensionsBeforeNormalize": pillow_source_dimensions,
    },
    "prototype": {
        "nominalDimensionsMeters": [1.98, 2.10, 1.40],
        "note": "Experimental CC0 soft-geometry transfer. Not a promoted production asset.",
    },
}
(OUT / "hybrid-bed-report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
