import bpy
import json
import math
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from blender.common import material, rounded_box, point_at, select_only, world_bounds, mesh_stats
from blender.assets.sofa_001 import build_sofa
from blender.assets.bed_001 import build_bed

OUT = os.path.join(ROOT, "build", "phase_01a")
os.makedirs(OUT, exist_ok=True)

REVIEW_MODE = os.environ.get("DWELLING_REVIEW_MODE", "hero").strip().lower()
if REVIEW_MODE not in {"fast", "hero"}:
    raise ValueError(f"Unsupported DWELLING_REVIEW_MODE: {REVIEW_MODE}")

LIGHTING_PRESET = {
    "preset": "dwelling-warm-daylight-v0.1",
    "intent": "soft warm residential daylight with readable material separation",
    "semantic": {
        "keyDirection": "front-left-above",
        "keySoftness": "large-window-soft",
        "keyIntensity": 1.0,
        "environmentIntensity": 0.28,
        "fillIntensity": 0.22,
        "warmPracticalIntensity": 0.10,
        "approxColorTemperatureKelvin": 5200
    },
    "note": "Semantic recipe. Blender and RealityKit numeric values are implementation-specific."
}

def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene

def setup_review_shell():
    floor_mat = material("Review Floor", (0.50, 0.35, 0.22), 0.70)
    wall_mat = material("Review Wall", (0.82, 0.79, 0.72), 0.86)

    shell = [
        rounded_box("Review_Floor", (0, 0, 0.025), (8.0, 6.0, 0.05), floor_mat, 0.008, 2),
        rounded_box("Review_BackWall", (0, 2.76, 1.50), (8.0, 0.08, 3.0), wall_mat, 0.01, 2),
        rounded_box("Review_LeftWall", (-3.96, 0.85, 1.50), (0.08, 3.9, 3.0), wall_mat, 0.01, 2),
    ]
    return shell

def setup_lighting_and_camera():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE" if bpy.app.version >= (5, 0, 0) else "BLENDER_EEVEE_NEXT"
    if REVIEW_MODE == "fast":
        scene.render.resolution_x = 768
        scene.render.resolution_y = 576
    else:
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    world = bpy.data.worlds.new("Dwelling Review World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.12, 0.10, 0.085, 1.0)
    bg.inputs["Strength"].default_value = 0.18

    # Window-like soft key.
    bpy.ops.object.light_add(type="AREA", location=(-3.8, -3.6, 4.7))
    key = bpy.context.object
    key.name = "WarmDaylight_Key"
    key.data.energy = 720
    key.data.shape = "RECTANGLE"
    key.data.size = 4.0
    key.data.size_y = 3.0
    key.data.color = (1.0, 0.88, 0.74)
    point_at(key, (0.0, 0.0, 0.65))

    # Cool-neutral fill from the opposite side to preserve form.
    bpy.ops.object.light_add(type="AREA", location=(3.4, -1.2, 3.4))
    fill = bpy.context.object
    fill.name = "WarmDaylight_Fill"
    fill.data.energy = 140
    fill.data.size = 3.2
    fill.data.color = (0.82, 0.88, 1.0)
    point_at(fill, (0.0, 0.1, 0.7))

    # Small warm practical/rim component.
    bpy.ops.object.light_add(type="AREA", location=(1.6, 2.2, 2.7))
    rim = bpy.context.object
    rim.name = "WarmDaylight_Practical"
    rim.data.energy = 85
    rim.data.size = 1.4
    rim.data.color = (1.0, 0.56, 0.30)
    point_at(rim, (0.0, 0.0, 0.65))

    bpy.ops.object.camera_add(location=(4.4, -5.1, 3.25))
    cam = bpy.context.object
    cam.name = "Review_Camera"
    cam.data.type = "PERSP"
    cam.data.lens = 55
    scene.camera = cam
    point_at(cam, (0, 0, 0.58))
    return cam

def render(filename, cam, location, target, lens=55):
    cam.location = location
    cam.data.lens = lens
    point_at(cam, target)
    bpy.context.scene.render.filepath = os.path.join(OUT, filename)
    bpy.ops.render.render(write_still=True)

def export_asset(asset, basename):
    objects = asset["objects"]
    select_only(objects)

    blend_path = os.path.join(OUT, f"{basename}.blend")
    glb_path = os.path.join(OUT, f"{basename}.glb")

    # The .blend is saved before the review shell is added, so it remains an
    # editable asset source rather than a scene package.
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format="GLB",
        use_selection=True,
        export_apply=True,
    )
    return blend_path, glb_path

def build_review(asset_kind):
    reset_scene()
    if asset_kind == "sofa":
        asset = build_sofa()
        basename = "sofa-001"
        camera_target = (0, 0.0, 0.55)
        three_quarter = (3.7, -4.3, 2.55)
        side = (4.3, -0.10, 1.75)
    else:
        asset = build_bed()
        basename = "bed-001"
        camera_target = (0, 0.02, 0.62)
        three_quarter = (3.9, -4.7, 3.05)
        side = (4.5, -0.05, 2.15)

    blend_path, glb_path = export_asset(asset, basename)
    bounds = world_bounds(asset["objects"])
    stats = mesh_stats(asset["objects"])

    setup_review_shell()
    cam = setup_lighting_and_camera()

    render(f"preview-{basename}-3q.png", cam, three_quarter, camera_target, 58)
    if REVIEW_MODE == "hero":
        render(f"preview-{basename}-side.png", cam, side, camera_target, 62)

    return {
        "name": asset["name"],
        "version": asset.get("version", "0.1"),
        "front_axis": asset["front_axis"],
        "nominal_dimensions_m": asset["nominal_dimensions_m"],
        "measured_bounds_m": bounds,
        "mesh": stats,
        "blend": os.path.basename(blend_path),
        "glb": os.path.basename(glb_path),
    }

sofa_report = build_review("sofa")
bed_report = build_review("bed")

def validate_asset_contract(asset_report):
    measured = asset_report["measured_bounds_m"]["size"]
    nominal = asset_report["nominal_dimensions_m"]
    errors = [round(abs(measured[i] - nominal[i]), 4) for i in range(3)]
    ground_offset = round(abs(asset_report["measured_bounds_m"]["min"][2]), 4)
    asset_report["dimension_error_m"] = errors
    asset_report["ground_offset_m"] = ground_offset
    asset_report["contract_pass"] = max(errors) <= 0.03 and ground_offset <= 0.015
    return asset_report["contract_pass"]

sofa_contract_pass = validate_asset_contract(sofa_report)
bed_contract_pass = validate_asset_contract(bed_report)

with open(os.path.join(OUT, "lighting-preset-warm-daylight.json"), "w") as fp:
    json.dump(LIGHTING_PRESET, fp, indent=2)

required = [
    "sofa-001.blend",
    "sofa-001.glb",
    "bed-001.blend",
    "bed-001.glb",
    "preview-sofa-001-3q.png",
    "preview-bed-001-3q.png",
    "lighting-preset-warm-daylight.json",
]
if REVIEW_MODE == "hero":
    required += [
        "preview-sofa-001-side.png",
        "preview-bed-001-side.png",
    ]
missing = [name for name in required if not os.path.exists(os.path.join(OUT, name)) or os.path.getsize(os.path.join(OUT, name)) == 0]

report = {
    "phase": "01A",
    "benchmark": "mother-assets",
    "review_mode": REVIEW_MODE,
    "style": "Warm Miniature Realism",
    "assets": [sofa_report, bed_report],
    "lighting_preset": LIGHTING_PRESET["preset"],
    "asset_contract": {
        "origin": "world origin on floor contact plane; asset centered around X/Y zero",
        "dimension_tolerance_m": 0.03,
        "ground_tolerance_m": 0.015,
    },
    "required_outputs": required,
    "missing_outputs": missing,
    "status": "pass" if (
        not missing
        and sofa_report["mesh"]["objects"] >= 15
        and bed_report["mesh"]["objects"] >= 8
        and sofa_contract_pass
        and bed_contract_pass
    ) else "fail",
}

with open(os.path.join(OUT, "validation.json"), "w") as fp:
    json.dump(report, fp, indent=2)

if report["status"] != "pass":
    raise RuntimeError(f"Phase 01A validation failed: {report}")

print(json.dumps(report, indent=2))
