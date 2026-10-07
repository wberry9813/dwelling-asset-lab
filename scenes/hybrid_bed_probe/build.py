import bpy
import json
import math
import pathlib
import sys

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
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

# ---------------------------------------------------------------------------
# CC0 reference: only keep the naturally authored pillow topology.
# ---------------------------------------------------------------------------

with bpy.data.libraries.load(str(source_path), link=False) as (src, dst):
    dst.objects = list(src.objects)
for obj in dst.objects:
    if obj is not None:
        bpy.context.collection.objects.link(obj)

source_meshes = [o for o in scene.objects if o.type == "MESH"]
for obj in list(source_meshes):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")

parts = [o for o in scene.objects if o.type == "MESH"]

def recenter_origin(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")

def size_of(obj):
    return tuple(float(v) for v in obj.dimensions)

for p in parts:
    recenter_origin(p)

pillow_candidates = [
    p for p in parts
    if 0.5 < size_of(p)[0] < 1.0
    and size_of(p)[1] > 0.45
    and 0.18 < size_of(p)[2] < 0.45
]
if not pillow_candidates:
    raise RuntimeError("Unable to classify CC0 pillow reference")

pillow_src = sorted(
    pillow_candidates,
    key=lambda o: len(o.data.polygons),
    reverse=True,
)[0]
pillow_source_dimensions = [round(v, 4) for v in size_of(pillow_src)]

pillow_l = pillow_src.copy()
pillow_l.data = pillow_src.data.copy()
bpy.context.collection.objects.link(pillow_l)
pillow_r = pillow_src.copy()
pillow_r.data = pillow_src.data.copy()
bpy.context.collection.objects.link(pillow_r)

for obj in parts:
    bpy.data.objects.remove(obj, do_unlink=True)

# ---------------------------------------------------------------------------
# Materials and modern hard structure.
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

# Low-profile filled body under the cloth shell.
duvet_loft = rounded_box(
    "HybridBed_DuvetLoft",
    (0, -0.20, 0.610),
    (1.58, 1.24, 0.080),
    linen,
    0.065,
    8,
)

# Collision surfaces for authoring-time cloth simulation.
for obj in (mattress, duvet_loft):
    collision = obj.modifiers.new("Authoring Collision", "COLLISION")
    if hasattr(obj, "collision"):
        if hasattr(obj.collision, "thickness_outer"):
            obj.collision.thickness_outer = 0.006

# ---------------------------------------------------------------------------
# Real Blender Cloth authoring pass.
# ---------------------------------------------------------------------------

bpy.ops.mesh.primitive_grid_add(
    x_subdivisions=45,
    y_subdivisions=51,
    size=2.0,
    location=(0.0, -0.20, 0.755),
)
duvet_shell = bpy.context.object
duvet_shell.name = "HybridBed_DuvetShell_Cloth"
# Intentionally larger than the loft volume so the free edges can drape.
# Width stays within the 1.98m outer frame contract.
duvet_shell.scale = (0.965, 0.805, 1.0)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

# Add a few millimetres of deterministic asymmetry before the solve.
for v in duvet_shell.data.vertices:
    x, y, z = v.co
    # Low-amplitude asymmetry creates natural wrinkle seeds while the larger
    # free border supplies the actual gravity-driven drape.
    v.co.z += 0.008 * math.sin(4.0 * x + 1.1) * math.sin(3.2 * y - 0.7)
    v.co.z += 0.004 * math.sin(7.5 * x - 2.4 * y)
    v.co.x += 0.004 * math.sin(2.6 * y + 0.9)

duvet_shell.data.materials.append(linen)

cloth_mod = duvet_shell.modifiers.new("Authoring Cloth", "CLOTH")
settings = cloth_mod.settings
for attr, value in [
    ("quality", 7),
    ("mass", 0.22),
    ("air_damping", 3.0),
    ("tension_stiffness", 14.0),
    ("compression_stiffness", 14.0),
    ("shear_stiffness", 7.0),
    ("bending_stiffness", 0.22),
]:
    if hasattr(settings, attr):
        setattr(settings, attr, value)

scene.frame_start = 1
scene.frame_end = 58
for frame_no in range(scene.frame_start, scene.frame_end + 1):
    scene.frame_set(frame_no)

# Freeze the accepted simulated state into actual geometry for this build.
bpy.ops.object.select_all(action="DESELECT")
duvet_shell.select_set(True)
bpy.context.view_layer.objects.active = duvet_shell
scene.frame_set(scene.frame_end)
bpy.ops.object.modifier_apply(modifier=cloth_mod.name)

solidify = duvet_shell.modifiers.new("Fabric Thickness", "SOLIDIFY")
solidify.thickness = 0.003
solidify.offset = -0.3
bpy.ops.object.modifier_apply(modifier=solidify.name)

subsurf = duvet_shell.modifiers.new("Fabric Smoothing", "SUBSURF")
subsurf.subdivision_type = "CATMULL_CLARK"
subsurf.levels = 1
subsurf.render_levels = 1
bpy.ops.object.modifier_apply(modifier=subsurf.name)

for poly in duvet_shell.data.polygons:
    poly.use_smooth = True

# ---------------------------------------------------------------------------
# CC0 pillow normalization.
# ---------------------------------------------------------------------------

for obj in (pillow_l, pillow_r):
    obj.data.materials.clear()
    obj.data.materials.append(sheet)
    for poly in obj.data.polygons:
        poly.use_smooth = True

def setup_pillow(obj, name, loc, rot_z):
    obj.name = name
    obj.dimensions = (0.70, 0.46, 0.16)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = loc
    obj.rotation_euler = (
        math.radians(-8),
        math.radians(2 if loc[0] < 0 else -2),
        math.radians(rot_z),
    )

setup_pillow(pillow_l, "HybridBed_Pillow_L_CC0Base", (-0.40, 0.59, 0.680), -5)
setup_pillow(pillow_r, "HybridBed_Pillow_R_CC0Base", (0.40, 0.56, 0.690), 5)

# ---------------------------------------------------------------------------
# Review scene.
# ---------------------------------------------------------------------------

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

# Save/export prototype for inspection.
blend_path = OUT / "hybrid-bed-prototype.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

bed_objects = [
    frame, plinth, headboard, headboard_pad, mattress, sheet_layer,
    duvet_loft, duvet_shell, pillow_l, pillow_r,
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
    "authoringMethod": "parametric hard structure + Blender Cloth baked shell + CC0 pillow topology",
    "simulation": {
        "frames": scene.frame_end,
        "grid": [45, 51],
        "fabricThicknessMeters": 0.003,
    },
    "selectedSoftParts": {
        "pillowSourceDimensionsBeforeNormalize": pillow_source_dimensions,
    },
    "prototype": {
        "nominalDimensionsMeters": [1.98, 2.10, 1.40],
        "note": "Experimental hybrid authored bed. Cloth solve is applied before export.",
    },
}
(OUT / "hybrid-bed-report.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
