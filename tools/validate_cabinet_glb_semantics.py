#!/usr/bin/env python3
import argparse
import json
import struct
import sys

def read_glb_json(path):
    with open(path, "rb") as f:
        magic, version, length = struct.unpack("<III", f.read(12))
        if magic != 0x46546C67:
            raise RuntimeError("Not a GLB file")
        if version != 2:
            raise RuntimeError(f"Unsupported GLB version: {version}")
        while f.tell() < length:
            chunk_len, chunk_type = struct.unpack("<II", f.read(8))
            data = f.read(chunk_len)
            if chunk_type == 0x4E4F534A:
                return json.loads(data.rstrip(b"\x00 ").decode("utf-8"))
    raise RuntimeError("GLB JSON chunk not found")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("glb")
    args = ap.parse_args()

    doc = read_glb_json(args.glb)
    nodes = doc.get("nodes", [])
    by_name = {node.get("name"): (idx, node) for idx, node in enumerate(nodes)}

    expected = {
        "KitchenBase600_DoorPivot_L": {
            "KitchenBase600_Door_L",
            "KitchenBase600_Handle_L",
        },
        "KitchenBase600_DoorPivot_R": {
            "KitchenBase600_Door_R",
            "KitchenBase600_Handle_R",
        },
    }

    errors = []
    for pivot_name, required_children in expected.items():
        entry = by_name.get(pivot_name)
        if entry is None:
            errors.append(f"missing pivot node: {pivot_name}")
            continue
        _, pivot = entry
        child_names = {
            nodes[idx].get("name")
            for idx in pivot.get("children", [])
            if 0 <= idx < len(nodes)
        }
        missing = sorted(required_children - child_names)
        if missing:
            errors.append(f"{pivot_name} missing children: {missing}")

    report = {
        "file": args.glb,
        "nodeCount": len(nodes),
        "expectedPivots": sorted(expected),
        "status": "fail" if errors else "pass",
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    if errors:
        sys.exit(1)

if __name__ == "__main__":
    main()
