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

def extension_score(text):
    if ".jpg" in text or ".jpeg" in text:
        return 8
    if ".png" in text:
        return 7
    if ".exr" in text:
        return 4
    return -1000

def score_diffuse(trail, url):
    s = (" ".join(trail) + " " + url).lower()
    ext = extension_score(s)
    if ext < 0:
        return ext
    if not any(k in s for k in ("diffuse", "albedo", "basecolor", "base_color")):
        return -1000
    if any(k in s for k in ("preview", "thumb", "thumbnail")):
        return -1000
    score = 100 + ext
    score += 30 if "1k" in s else (15 if "2k" in s else 0)
    return score

def score_normal(trail, url):
    s = (" ".join(trail) + " " + url).lower()
    ext = extension_score(s)
    if ext < 0:
        return ext
    if not ("nor_gl" in s or "normal_gl" in s or ("normal" in s and "gl" in s)):
        return -1000
    score = 100 + ext
    score += 30 if "1k" in s else (15 if "2k" in s else 0)
    score -= 80 if "dx" in s else 0
    return score

def score_roughness(trail, url):
    s = (" ".join(trail) + " " + url).lower()
    ext = extension_score(s)
    if ext < 0:
        return ext
    if "rough" not in s:
        return -1000
    score = 100 + ext
    score += 30 if "1k" in s else (15 if "2k" in s else 0)
    if "arm" in s or "ao_rough" in s or "ao/rough" in s:
        score -= 60
    return score

def choose(entries, scorer, label):
    ranked = sorted(entries, key=lambda x: scorer(x[0], x[1]), reverse=True)
    ranked = [x for x in ranked if scorer(x[0], x[1]) > 0]
    if not ranked:
        raise RuntimeError(f"No suitable {label} texture URL found")
    return ranked[0]

def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=180) as r, dest.open("wb") as f:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
            f.write(chunk)
    return h.hexdigest()

def suffix_for(url):
    path = pathlib.Path(url.split("?", 1)[0])
    return path.suffix if path.suffix else ".bin"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("asset_id")
    ap.add_argument("--out", required=True)
    ap.add_argument("--expected-files-hash")
    args = ap.parse_args()

    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    info = get_json(f"{API}/info/{args.asset_id}")
    files = get_json(f"{API}/files/{args.asset_id}")

    files_hash = info.get("files_hash")
    if args.expected_files_hash and files_hash != args.expected_files_hash:
        raise RuntimeError(
            f"Poly Haven files_hash changed for {args.asset_id}: "
            f"expected {args.expected_files_hash}, got {files_hash}"
        )

    entries = collect_urls(files)
    diffuse_trail, diffuse_url = choose(entries, score_diffuse, "diffuse")
    normal_trail, normal_url = choose(entries, score_normal, "OpenGL normal")
    rough_trail, rough_url = choose(entries, score_roughness, "roughness")

    diffuse_path = out / ("diffuse" + suffix_for(diffuse_url))
    normal_path = out / ("normal" + suffix_for(normal_url))
    rough_path = out / ("roughness" + suffix_for(rough_url))

    diffuse_sha = download(diffuse_url, diffuse_path)
    normal_sha = download(normal_url, normal_path)
    rough_sha = download(rough_url, rough_path)

    metadata = {
        "provider": "Poly Haven",
        "poweredBy": "Poly Haven",
        "assetId": args.asset_id,
        "assetName": info.get("name"),
        "license": "CC0",
        "filesHash": files_hash,
        "maps": {
            "diffuse": {
                "trail": list(diffuse_trail),
                "url": diffuse_url,
                "file": str(diffuse_path),
                "sha256": diffuse_sha,
            },
            "normal": {
                "trail": list(normal_trail),
                "url": normal_url,
                "file": str(normal_path),
                "sha256": normal_sha,
            },
            "roughness": {
                "trail": list(rough_trail),
                "url": rough_url,
                "file": str(rough_path),
                "sha256": rough_sha,
            },
        },
    }
    (out / "texture-metadata.json").write_text(json.dumps(metadata, indent=2))
    print(json.dumps(metadata, indent=2))

if __name__ == "__main__":
    main()
