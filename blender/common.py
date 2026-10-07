import bpy
import bmesh
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

def _signed_pow(value, exponent):
    if abs(value) < 1e-10:
        return 0.0
    return math.copysign(abs(value) ** exponent, value)

def superellipsoid(
    name,
    location,
    dimensions,
    mat,
    n_xy=4.2,
    n_z=3.6,
    segments=64,
    rings=28,
    rotation=(0, 0, 0),
    deform=None,
):
    """Smooth rounded-box primitive for cushions and upholstery."""
    a, b, c = (dimensions[0] / 2, dimensions[1] / 2, dimensions[2] / 2)
    e_xy = 2.0 / n_xy
    e_z = 2.0 / n_z

    verts = [(0.0, 0.0, -c)]
    ring_indices = []

    for i in range(1, rings):
        theta = -math.pi / 2 + math.pi * i / rings
        ct = math.cos(theta)
        st = math.sin(theta)
        row = []
        for j in range(segments):
            phi = 2 * math.pi * j / segments
            cp = math.cos(phi)
            sp = math.sin(phi)

            x = a * _signed_pow(ct, e_z) * _signed_pow(cp, e_xy)
            y = b * _signed_pow(ct, e_z) * _signed_pow(sp, e_xy)
            z = c * _signed_pow(st, e_z)

            if deform is not None:
                x, y, z = deform(x, y, z, a, b, c)

            row.append(len(verts))
            verts.append((x, y, z))
        ring_indices.append(row)

    top_index = len(verts)
    verts.append((0.0, 0.0, c))

    faces = []
    first = ring_indices[0]
    for j in range(segments):
        faces.append((0, first[(j + 1) % segments], first[j]))

    for r in range(len(ring_indices) - 1):
        lower = ring_indices[r]
        upper = ring_indices[r + 1]
        for j in range(segments):
            nj = (j + 1) % segments
            faces.append((lower[j], lower[nj], upper[nj], upper[j]))

    last = ring_indices[-1]
    for j in range(segments):
        faces.append((top_index, last[j], last[(j + 1) % segments]))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)

    for poly in mesh.polygons:
        poly.use_smooth = True

    return obj

def draped_sheet(
    name,
    location,
    width,
    depth,
    mat,
    top_z=0.0,
    side_drop=0.07,
    foot_drop=0.28,
    foot_start=-0.30,
    nx=41,
    ny=45,
    thickness=0.035,
    rotation=(0, 0, 0),
    wrinkle=0.012,
):
    """Generate a textile surface with soft side falloff and a foot drape."""
    verts = []
    faces = []

    half_w = width / 2
    half_d = depth / 2

    for iy in range(ny):
        v = iy / (ny - 1)
        y = -half_d + depth * v
        for ix in range(nx):
            u = ix / (nx - 1)
            x = -half_w + width * u

            edge = min(1.0, (abs(x) / max(half_w, 1e-6)) ** 8)
            z = top_z - side_drop * edge

            if y < foot_start:
                denom = max(foot_start + half_d, 1e-6)
                t = min(1.0, max(0.0, (foot_start - y) / denom))
                t = t * t * (3.0 - 2.0 * t)
                z -= foot_drop * t

            center_weight = max(0.0, 1.0 - (x / max(half_w, 1e-6)) ** 2)
            z += wrinkle * math.sin(7.5 * x + 2.0 * y) * center_weight
            z += wrinkle * 0.45 * math.sin(13.0 * x - 3.0 * y)

            verts.append((x, y, z))

    for iy in range(ny - 1):
        for ix in range(nx - 1):
            a = iy * nx + ix
            b = a + 1
            c = a + nx + 1
            d = a + nx
            faces.append((a, b, c, d))

    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()

    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(mat)

    for poly in mesh.polygons:
        poly.use_smooth = True

    solidify = obj.modifiers.new("Textile thickness", "SOLIDIFY")
    solidify.thickness = thickness
    solidify.offset = -0.25

    subdiv = obj.modifiers.new("Textile smoothing", "SUBSURF")
    subdiv.subdivision_type = "CATMULL_CLARK"
    subdiv.levels = 1
    subdiv.render_levels = 1

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
