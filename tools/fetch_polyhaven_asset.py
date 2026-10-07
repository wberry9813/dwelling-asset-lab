#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib
import urllib.request

API = "https://api.polyhaven.com"
UA = "DwellingAssetLab/0.1 (+https://github.com/wberry9813/dwelling-asset-lab)"

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def collect_urls(node, trail=()):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.extend(collect_urls(v, trail + (str(k),)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.extend(collect_urls(v, trail + (str(i),)))
    elif isinstance(node, str) and node.startswith(("http://", "https://")):
        out.append((trail, node))
    return out

def score(trail, url):
    s = (" ".join(trail) + " " + url).lower()
    score = 0
    if ".blend" in s:
        score += 100
    elif ".glb" in s:
        score += 80
    elif ".gltf" in s:
        score += 70
    elif ".zip" in s:
        score += 20
    else:
        return -1000
    if "1k" in s:
        score += 30
    elif "2k" in s:
        score += 20
    elif "4k" in s:
        score += 10
    if "blend" in " ".join(trail).lower():
        score += 15
    return score

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset_id")
    ap.add_argument("--out", default="build/external_probe/source")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    info = get_json(f"{API}/info/{args.asset_id}")
    files = get_json(f"{API}/files/{args.asset_id}")
    candidates = sorted(
        collect_urls(files),
        key=lambda item: score(item[0], item[1]),
        reverse=True,
    )
    candidates = [c for c in candidates if score(c[0], c[1]) > 0]
    if not candidates:
        raise SystemExit("No downloadable Blender/glTF candidate found")

    trail, url = candidates[0]
    suffix = pathlib.Path(url.split("?", 1)[0]).suffix or ".bin"
    dest = out / f"{args.asset_id}{suffix}"

    req = urllib.request.Request(url, headers={"User-Agent": UA})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=180) as r, dest.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            f.write(chunk)

    metadata = {
        "provider": "Poly Haven",
        "poweredBy": "Poly Haven",
        "assetId": args.asset_id,
        "assetName": info.get("name"),
        "license": "CC0",
        "filesHash": info.get("files_hash"),
        "selectedTrail": list(trail),
        "selectedUrl": url,
        "downloadedFile": str(dest),
        "sha256": h.hexdigest(),
        "candidateCount": len(candidates),
    }
    (out / "source-metadata.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
