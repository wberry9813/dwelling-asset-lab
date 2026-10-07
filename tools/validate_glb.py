#!/usr/bin/env python3
import argparse
import json
import pathlib
import struct
import sys

JSON_CHUNK = 0x4E4F534A
MAGIC = 0x46546C67

def read_glb_json(path):
    data = pathlib.Path(path).read_bytes()
    if len(data) < 20:
        raise ValueError("GLB is too small")
    magic, version, declared_length = struct.unpack_from("<III", data, 0)
    if magic != MAGIC:
        raise ValueError("Not a GLB file (bad magic)")
    if version != 2:
        raise ValueError(f"Unsupported GLB version: {version}")
    if declared_length != len(data):
        raise ValueError(
            f"GLB length mismatch: header={declared_length}, actual={len(data)}"
        )

    offset = 12
    while offset + 8 <= len(data):
        chunk_length, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + chunk_length]
        offset += chunk_length
        if chunk_type == JSON_CHUNK:
            return json.loads(chunk.rstrip(b" \t\r\n\x00").decode("utf-8"))
    raise ValueError("GLB JSON chunk not found")

def iter_material_texture_infos(material):
    pbr = material.get("pbrMetallicRoughness", {})
    for label in ("baseColorTexture", "metallicRoughnessTexture"):
        info = pbr.get(label)
        if isinstance(info, dict):
            yield f"pbrMetallicRoughness.{label}", info

    for label in ("normalTexture", "occlusionTexture", "emissiveTexture"):
        info = material.get(label)
        if isinstance(info, dict):
            yield label, info

def validate_texture_info(label, info, texture_count, errors):
    index = info.get("index")
    if not isinstance(index, int) or not 0 <= index < texture_count:
        errors.append(f"{label}: invalid texture index {index}")

    texcoord = info.get("texCoord", 0)
    if not isinstance(texcoord, int) or texcoord < 0:
        errors.append(f"{label}: invalid texCoord {texcoord}")

    transform = info.get("extensions", {}).get("KHR_texture_transform")
    if isinstance(transform, dict):
        transformed_coord = transform.get("texCoord", texcoord)
        if not isinstance(transformed_coord, int) or transformed_coord < 0:
            errors.append(
                f"{label}.KHR_texture_transform: invalid texCoord {transformed_coord}"
            )

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    ap.add_argument("--require-textures", action="store_true")
    ap.add_argument("--report")
    args = ap.parse_args()

    try:
        doc = read_glb_json(args.glb)
    except Exception as exc:
        print(f"GLB validation FAILED: {exc}")
        return 1

    errors = []
    textures = doc.get("textures", [])
    images = doc.get("images", [])
    samplers = doc.get("samplers", [])
    materials = doc.get("materials", [])

    if args.require_textures and not textures:
        errors.append("No textures found in GLB")

    for i, texture in enumerate(textures):
        source = texture.get("source")
        if not isinstance(source, int) or not 0 <= source < len(images):
            errors.append(f"texture[{i}]: invalid image source {source}")
        sampler = texture.get("sampler")
        if sampler is not None and (
            not isinstance(sampler, int) or not 0 <= sampler < len(samplers)
        ):
            errors.append(f"texture[{i}]: invalid sampler {sampler}")

    for i, image in enumerate(images):
        has_uri = isinstance(image.get("uri"), str) and bool(image.get("uri"))
        has_buffer_view = isinstance(image.get("bufferView"), int)
        if not has_uri and not has_buffer_view:
            errors.append(f"image[{i}]: missing uri and bufferView")

    texture_usage = []
    for mi, material in enumerate(materials):
        mname = material.get("name", f"material[{mi}]")
        for label, info in iter_material_texture_infos(material):
            full_label = f"{mname}.{label}"
            validate_texture_info(full_label, info, len(textures), errors)
            texture_usage.append({
                "material": mname,
                "slot": label,
                "texture": info.get("index"),
                "texCoord": info.get("texCoord", 0),
                "transformTexCoord": (
                    info.get("extensions", {})
                    .get("KHR_texture_transform", {})
                    .get("texCoord", info.get("texCoord", 0))
                ),
            })

    # Catch invalid KHR_texture_transform texCoord values anywhere in the JSON,
    # including exporter-specific nesting not covered by standard material slots.
    def walk(node, trail="$"):
        if isinstance(node, dict):
            transform = node.get("KHR_texture_transform")
            if isinstance(transform, dict) and "texCoord" in transform:
                value = transform["texCoord"]
                if not isinstance(value, int) or value < 0:
                    errors.append(
                        f"{trail}.KHR_texture_transform.texCoord: invalid value {value}"
                    )
            for key, value in node.items():
                walk(value, f"{trail}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{trail}[{index}]")

    walk(doc)

    report = {
        "file": str(args.glb),
        "materials": len(materials),
        "textures": len(textures),
        "images": len(images),
        "textureUsage": texture_usage,
        "extensionsUsed": doc.get("extensionsUsed", []),
        "extensionsRequired": doc.get("extensionsRequired", []),
        "status": "pass" if not errors else "fail",
        "errors": errors,
    }

    if args.report:
        pathlib.Path(args.report).write_text(json.dumps(report, indent=2))

    print(json.dumps(report, indent=2))
    if errors:
        print("GLB validation FAILED")
        return 1

    print("GLB validation PASS")
    return 0

if __name__ == "__main__":
    sys.exit(main())
