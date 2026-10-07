import bpy
import json
import pathlib
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "build" / "external_probe" / "source"
OUT = ROOT / "build" / "external_probe" / "result"
OUT.mkdir(parents=True, exist_ok=True)

metadata = json.loads((SRC / "source-metadata.json").read_text())
source_path = pathlib.Path(metadata["downloadedFile"])
if not source_path.is_absolute():
    source_path = ROOT / source_path

bpy.ops.wm.read_factory_settings(use_empty=True)

ext = source_path.suffix.lower()
if ext == ".blend":
    with bpy.data.libraries.load(str(source_path), link=False) as (src, dst):
        dst.objects = list(src.objects)
    for obj in dst.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
elif ext in {".gltf", ".glb"}:
    bpy.ops.import_scene.gltf(filepath=str(source_path))
else:
    raise RuntimeError(f"Unsupported probe source: {source_path}")

mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]
if not mesh_objects:
    raise RuntimeError("External asset contains no mesh objects")

# Split source meshes by disconnected geometry. Many library assets are
# delivered as one Blender object even when mattress, pillow, blanket and
# frame are topologically separate islands.
for source_obj in list(mesh_objects):
    bpy.ops.object.select_all(action="DESELECT")
    source_obj.select_set(True)
    bpy.context.view_layer.objects.active = source_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")

mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]

source_mesh_object_count = len(mesh_objects)

# Split disconnected geometry islands into separate objects. Many production
# assets are exported as a single object even when cushions, quilt and frame
# are not topologically connected.
for obj in list(mesh_objects):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")

mesh_objects = [o for o in bpy.context.scene.objects if o.type == "MESH"]

points = []
for obj in mesh_objects:
    for corner in obj.bound_box:
        points.append(obj.matrix_world @ Vector(corner))
mins = [min(p[i] for p in points) for i in range(3)]
maxs = [max(p[i] for p in points) for i in range(3)]
size = [maxs[i] - mins[i] for i in range(3)]
center = Vector([(mins[i] + maxs[i]) / 2 for i in range(3)])

objects = []
for o in mesh_objects:
    obj_points = [o.matrix_world @ Vector(corner) for corner in o.bound_box]
    obj_mins = [min(p[i] for p in obj_points) for i in range(3)]
    obj_maxs = [max(p[i] for p in obj_points) for i in range(3)]
    obj_size = [obj_maxs[i] - obj_mins[i] for i in range(3)]
    obj_center = [(obj_mins[i] + obj_maxs[i]) / 2 for i in range(3)]
    objects.append({
        "name": o.name,
        "vertices": len(o.data.vertices),
        "polygons": len(o.data.polygons),
        "materials": [slot.material.name if slot.material else None for slot in o.material_slots],
        "bounds": {
            "min": [round(v, 4) for v in obj_mins],
            "max": [round(v, 4) for v in obj_maxs],
            "size": [round(v, 4) for v in obj_size],
            "center": [round(v, 4) for v in obj_center],
        },
    })

objects.sort(key=lambda item: item["polygons"], reverse=True)

materials = [{"name": m.name, "useNodes": bool(m.use_nodes)} for m in bpy.data.materials]

clay = bpy.data.materials.new("Probe Clay")
clay.use_nodes = True
bsdf = clay.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.42, 0.38, 0.33, 1.0)
bsdf.inputs["Roughness"].default_value = 0.78
for o in mesh_objects:
    o.data.materials.clear()
    o.data.materials.append(clay)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"

world = bpy.data.worlds.new("Probe World")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs["Color"].default_value = (0.06, 0.05, 0.045, 1.0)
bg.inputs["Strength"].default_value = 0.25

bpy.ops.mesh.primitive_plane_add(
    size=max(size[0], size[1]) * 2.2,
    location=(center.x, center.y, mins[2] - 0.002),
)
floor = bpy.context.object
floor.data.materials.append(clay)

bpy.ops.object.light_add(
    type="AREA",
    location=(center.x - size[0]*1.6, center.y - size[1]*1.8, maxs[2] + size[2]*1.8),
)
key = bpy.context.object
key.data.energy = 1050
key.data.size = max(size[0], size[1]) * 1.8
key.rotation_euler = (center - key.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.object.light_add(
    type="AREA",
    location=(center.x + size[0]*1.4, center.y - size[1]*0.3, maxs[2] + size[2]*0.8),
)
fill = bpy.context.object
fill.data.energy = 260
fill.data.size = max(size[0], size[1]) * 1.3
fill.rotation_euler = (center - fill.location).to_track_quat("-Z", "Y").to_euler()

diag = max(size)
bpy.ops.object.camera_add(
    location=(center.x + diag*1.8, center.y - diag*2.0, center.z + diag*1.25)
)
cam = bpy.context.object
scene.camera = cam
cam.data.lens = 58
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()

scene.render.filepath = str(OUT / "probe-clay-3q.png")
bpy.ops.render.render(write_still=True)

cam.location = (center.x, center.y - diag*2.6, center.z + diag*0.35)
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.render.filepath = str(OUT / "probe-clay-front.png")
bpy.ops.render.render(write_still=True)

# Component review: deterministic distinct materials make loose parts easy to
# evaluate without depending on original textures.
component_palette = [
    (0.18, 0.32, 0.52, 1.0),
    (0.50, 0.24, 0.16, 1.0),
    (0.24, 0.46, 0.28, 1.0),
    (0.54, 0.42, 0.16, 1.0),
    (0.38, 0.24, 0.46, 1.0),
    (0.22, 0.46, 0.48, 1.0),
]
for index, obj in enumerate(mesh_objects):
    mat = bpy.data.materials.new(f"Component_{index:02d}")
    mat.diffuse_color = component_palette[index % len(component_palette)]
    mat.use_nodes = True
    pbsdf = mat.node_tree.nodes.get("Principled BSDF")
    pbsdf.inputs["Base Color"].default_value = component_palette[index % len(component_palette)]
    pbsdf.inputs["Roughness"].default_value = 0.72
    obj.data.materials.clear()
    obj.data.materials.append(mat)

cam.location = (center.x + diag*1.8, center.y - diag*2.0, center.z + diag*1.25)
cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.render.filepath = str(OUT / "probe-components-3q.png")
bpy.ops.render.render(write_still=True)

report = {
    "source": metadata,
    "blenderVersion": bpy.app.version_string,
    "sourceMeshObjects": source_mesh_object_count,
    "loosePartObjects": len(mesh_objects),
    "materialsBeforeClayOverride": materials,
    "bounds": {
        "min": [round(v, 4) for v in mins],
        "max": [round(v, 4) for v in maxs],
        "size": [round(v, 4) for v in size],
    },
    "objects": objects,
}
(OUT / "probe-report.json").write_text(json.dumps(report, indent=2))
print(json.dumps({
    "asset": metadata["assetId"],
    "loosePartObjects": len(mesh_objects),
    "bounds": report["bounds"],
}, indent=2))
