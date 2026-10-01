#!/usr/bin/env python3
"""Validate ScanFix Golden Dataset manifests and repository hygiene."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "datasets" / "golden" / "manifest.schema.json"
BOOTSTRAP = ROOT / "datasets" / "golden" / "bootstrap"
SAMPLES = ROOT / "datasets" / "golden" / "samples"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def tracked_sample_files() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "datasets/golden/samples"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
    except Exception:
        return []
    allowed = {"datasets/golden/samples/README.md"}
    return [x for x in result.stdout.splitlines() if x and x not in allowed]


def validate_manifest(path: Path, validator: Draft202012Validator) -> list[str]:
    data = load_json(path)
    errors = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        location = ".".join(str(p) for p in err.path) or "<root>"
        errors.append(f"{path}: {location}: {err.message}")

    # Practical invariant: never permit reconstruction in any fixture.
    if data.get("expected", {}).get("content_reconstruction_allowed") is not False:
        errors.append(f"{path}: content_reconstruction_allowed must be false")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", action="store_true",
                    help="Also validate local datasets/golden/samples/*/metadata.json")
    args = ap.parse_args()

    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema)

    manifests = sorted(BOOTSTRAP.glob("*/metadata.json"))
    if args.local:
        manifests += sorted(SAMPLES.glob("GD-*/metadata.json"))

    errors: list[str] = []
    if len(list(BOOTSTRAP.glob("*/metadata.json"))) < 10:
        errors.append("Bootstrap dataset must contain at least 10 manifest fixtures.")

    seen = set()
    for path in manifests:
        data = load_json(path)
        cid = data.get("case_id")
        if cid in seen:
            errors.append(f"Duplicate case_id: {cid}")
        seen.add(cid)
        errors.extend(validate_manifest(path, validator))

    leaked = tracked_sample_files()
    if leaked:
        errors.append(
            "Real/local sample files are tracked by Git: " + ", ".join(leaked)
        )

    if errors:
        print("FAIL")
        for item in errors:
            print(f"- {item}")
        return 1

    print("PASS")
    print(f"Validated manifests: {len(manifests)}")
    print(f"Bootstrap fixtures: {len(list(BOOTSTRAP.glob('*/metadata.json')))}")
    print("Tracked local sample files: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
