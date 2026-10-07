import bpy
import math
from mathutils import Vector

def material(name, color, roughness=0.55, metallic=0.0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return m

def rounded_box(name, location, dimensions, mat, bevel=0.04, segments=5, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("Soft edges", "BEVEL")
        mod.width = min(bevel, min(dimensions) * 0.42)
        mod.segments = segments
    obj.data.materials.append(mat)
    return obj

def cylinder(name, location, radius, depth, mat, vertices=48, bevel=0.012):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if bevel > 0:
        mod = obj.modifiers.new("Soft edges", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    obj.data.materials.append(mat)
    return obj

def point_at(obj, target=(0, 0, 0.5)):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]

def world_bounds(objects):
    points = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    if not points:
        return {"min": [0, 0, 0], "max": [0, 0, 0], "size": [0, 0, 0]}
    mins = [min(p[i] for p in points) for i in range(3)]
    maxs = [max(p[i] for p in points) for i in range(3)]
    return {
        "min": [round(v, 4) for v in mins],
        "max": [round(v, 4) for v in maxs],
        "size": [round(maxs[i] - mins[i], 4) for i in range(3)],
    }

def mesh_stats(objects):
    meshes = [o for o in objects if o.type == "MESH"]
    return {
        "objects": len(meshes),
        "vertices": sum(len(o.data.vertices) for o in meshes),
        "polygons": sum(len(o.data.polygons) for o in meshes),
    }
