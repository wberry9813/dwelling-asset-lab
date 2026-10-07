import bpy
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from blender.common import material, rounded_box, point_at, select_only, world_bounds, mesh_stats
from blender.assets.kitchen_base_600 import build_kitchen_base_600

OUT = ROOT / "build" / "phase_01b"
OUT.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

asset = build_kitchen_base_600()
objects = asset["objects"]
meshes = asset["meshes"]

bounds = world_bounds(meshes)
stats = mesh_stats(meshes)

blend_path = OUT / "kitchen-base-600.blend"
glb_path = OUT / "kitchen-base-600.glb"

# Save the production asset before adding any review context.
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
select_only(objects)
bpy.ops.export_scene.gltf(
    filepath=str(glb_path),
    export_format="GLB",
    use_selection=True,
    export_apply=True,
)

# ---------------------------------------------------------------------------
# Review context only — countertop and wall are not production geometry.
# ---------------------------------------------------------------------------

floor_mat = material("HardSurface Review Floor", (0.48, 0.35, 0.23), 0.72)
wall_mat = material("HardSurface Review Wall", (0.82, 0.79, 0.73), 0.86)
quartz = material("Review Warm Quartz", (0.78, 0.76, 0.71), 0.38)

rounded_box("Review_Floor", (0, 0, -0.025), (3.0, 2.4, 0.05), floor_mat, 0.006, 2)
rounded_box("Review_BackWall", (0, 0.65, 1.25), (3.0, 0.06, 2.5), wall_mat, 0.008, 2)
rounded_box("Review_Countertop", (0, -0.015, 0.885), (0.64, 0.62, 0.030), quartz, 0.008, 4)

scene.render.engine = "BLENDER_EEVEE" if bpy.app.version >= (5, 0, 0) else "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

world = bpy.data.worlds.new("Hard Surface Review World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.065, 0.052, 0.043, 1.0)
bg.inputs["Strength"].default_value = 0.22

bpy.ops.object.light_add(type="AREA", location=(-2.2, -2.4, 3.0))
key = bpy.context.object
key.data.energy = 720
key.data.size = 2.6
key.data.color = (1.0, 0.88, 0.75)
point_at(key, (0, 0, 0.48))

bpy.ops.object.light_add(type="AREA", location=(2.0, -0.6, 2.1))
fill = bpy.context.object
fill.data.energy = 180
fill.data.size = 2.2
fill.data.color = (0.84, 0.90, 1.0)
point_at(fill, (0, 0, 0.46))

bpy.ops.object.camera_add(location=(1.55, -2.2, 1.55))
cam = bpy.context.object
scene.camera = cam
cam.data.lens = 62
point_at(cam, (0, 0.0, 0.48))

scene.render.filepath = str(OUT / "preview-kitchen-base-600-closed.png")
bpy.ops.render.render(write_still=True)

# Open-door inspection proves that pivots and interior construction are real,
# not merely a facade.
left_pivot, right_pivot = asset["door_pivots"]
left_pivot.rotation_euler[2] = -1.72
right_pivot.rotation_euler[2] = 1.72

cam.location = (1.45, -2.35, 1.35)
point_at(cam, (0, -0.02, 0.47))
scene.render.filepath = str(OUT / "preview-kitchen-base-600-open.png")
bpy.ops.render.render(write_still=True)

required_names = {
    "KitchenBase600_Carcass_Left",
    "KitchenBase600_Carcass_Right",
    "KitchenBase600_Carcass_Bottom",
    "KitchenBase600_Back",
    "KitchenBase600_Shelf",
    "KitchenBase600_Door_L",
    "KitchenBase600_Door_R",
    "KitchenBase600_Handle_L",
    "KitchenBase600_Handle_R",
    "KitchenBase600_ToeKick",
}
actual_names = {o.name for o in meshes}
missing_semantics = sorted(required_names - actual_names)

nominal = asset["nominal_dimensions_m"]
measured = bounds["size"]
dimension_error = [round(abs(measured[i] - nominal[i]), 4) for i in range(3)]
ground_offset = round(abs(bounds["min"][2]), 4)

required_outputs = [
    blend_path,
    glb_path,
    OUT / "preview-kitchen-base-600-closed.png",
    OUT / "preview-kitchen-base-600-open.png",
]
missing_outputs = [
    p.name for p in required_outputs
    if not p.exists() or p.stat().st_size == 0
]

report = {
    "phase": "01B",
    "asset": asset["name"],
    "version": asset["version"],
    "front_axis": asset["front_axis"],
    "module_width_m": asset["module_width_m"],
    "nominal_dimensions_m": nominal,
    "measured_bounds_m": bounds,
    "dimension_error_m": dimension_error,
    "ground_offset_m": ground_offset,
    "mesh": stats,
    "missing_semantic_parts": missing_semantics,
    "required_outputs": [p.name for p in required_outputs],
    "missing_outputs": missing_outputs,
    "status": "pass" if (
        max(dimension_error) <= 0.012
        and ground_offset <= 0.005
        and not missing_semantics
        and not missing_outputs
        and stats["objects"] >= 16
    ) else "fail",
}

(OUT / "validation.json").write_text(json.dumps(report, indent=2))
if report["status"] != "pass":
    raise RuntimeError(f"Kitchen base validation failed: {report}")

print(json.dumps(report, indent=2))
