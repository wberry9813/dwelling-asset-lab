#!/usr/bin/env python3
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "assets" / "manifests"

ALLOWED_SOURCE_TYPES = {"generator", "blend", "geometry-nodes", "external-normalized"}
ALLOWED_FRONT = {"-Y", "+Y", "-X", "+X"}
ALLOWED_RUNTIME = {"glb", "usdz", "none"}

errors = []
manifests = []

for path in sorted(MANIFEST_DIR.glob("*.json")):
    if path.name == "schema.json":
        continue
    try:
        data = json.loads(path.read_text())
    except Exception as exc:
        errors.append(f"{path}: invalid JSON: {exc}")
        continue

    manifests.append((path, data))
    for key in ("id", "sourceType", "source", "frontAxis", "nominalDimensionsMeters", "license", "export"):
        if key not in data:
            errors.append(f"{path}: missing required key {key}")

    if data.get("sourceType") not in ALLOWED_SOURCE_TYPES:
        errors.append(f"{path}: invalid sourceType {data.get('sourceType')}")
    if data.get("frontAxis") not in ALLOWED_FRONT:
        errors.append(f"{path}: invalid frontAxis {data.get('frontAxis')}")

    dims = data.get("nominalDimensionsMeters")
    if not isinstance(dims, list) or len(dims) != 3 or any(not isinstance(v, (int, float)) or v <= 0 for v in dims):
        errors.append(f"{path}: nominalDimensionsMeters must be three positive numbers")

    license_obj = data.get("license")
    if not isinstance(license_obj, dict) or not license_obj.get("geometry"):
        errors.append(f"{path}: license.geometry is required")

    runtime = data.get("export", {}).get("runtime") if isinstance(data.get("export"), dict) else None
    if runtime not in ALLOWED_RUNTIME:
        errors.append(f"{path}: invalid export.runtime {runtime}")

    if data.get("sourceType") in {"generator", "blend", "geometry-nodes"}:
        source = ROOT / str(data.get("source", ""))
        if not source.exists():
            errors.append(f"{path}: local source does not exist: {source.relative_to(ROOT)}")

ids = [data.get("id") for _, data in manifests]
duplicates = sorted({x for x in ids if x and ids.count(x) > 1})
if duplicates:
    errors.append(f"duplicate manifest ids: {', '.join(duplicates)}")

if errors:
    print("Asset manifest validation FAILED")
    for error in errors:
        print(f"- {error}")
    sys.exit(1)

print(f"Asset manifest validation PASS ({len(manifests)} manifests)")
for path, data in manifests:
    print(f"- {data['id']}: {data['sourceType']} -> {data['export']['runtime']}")
