#!/usr/bin/env python3
"""Stage byte-identical copies of READY product image assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path


REQUIRED = {"asset_id", "resolved_path", "proposed_filename", "sha256", "status"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    args = parse_args()
    audit = Path(args.audit).resolve()
    output_dir = Path(args.output_dir).resolve()
    files_dir = output_dir / "files"
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit(f"Refusing non-empty output directory: {output_dir}")
    files_dir.mkdir(parents=True, exist_ok=True)

    with audit.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing audit columns: {', '.join(sorted(missing))}")
        rows = [row for row in reader if row.get("status") == "READY"]

    names = [row["proposed_filename"].strip() for row in rows]
    duplicate_names = sorted(
        name for name, count in Counter(names).items() if name and count > 1
    )
    if duplicate_names:
        raise SystemExit(
            f"Duplicate proposed filenames: {', '.join(duplicate_names)}"
        )

    staged = []
    for row in rows:
        source = Path(row["resolved_path"]).resolve()
        if not source.is_file():
            raise SystemExit(f"READY source is missing: {source}")
        before = digest(source)
        if before != row["sha256"]:
            raise SystemExit(f"Source drift detected for {row['asset_id']}")
        destination = files_dir / row["proposed_filename"].strip()
        if destination.exists():
            raise SystemExit(f"Refusing overwrite: {destination}")
        shutil.copy2(source, destination)
        after = digest(destination)
        if before != after:
            raise SystemExit(f"Hash mismatch after staging: {row['asset_id']}")
        staged.append(
            {
                "asset_id": row["asset_id"],
                "source_path": str(source),
                "staged_path": str(destination),
                "filename": destination.name,
                "sha256": after,
                "byte_identical": "true",
                "upc": row.get("upc", ""),
                "sku": row.get("sku", ""),
                "variant_key": row.get("variant_key", ""),
                "asset_role": row.get("asset_role", ""),
            }
        )

    manifest_path = output_dir / "STAGED_image_asset_manifest.csv"
    fields = (
        list(staged[0].keys())
        if staged
        else [
            "asset_id",
            "source_path",
            "staged_path",
            "filename",
            "sha256",
            "byte_identical",
            "upc",
            "sku",
            "variant_key",
            "asset_role",
        ]
    )
    with manifest_path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(staged)

    summary = {
        "status": "PASS",
        "audit": str(audit),
        "ready_rows": len(rows),
        "staged_rows": len(staged),
        "hash_matches": len(staged),
        "source_pixels_modified": 0,
        "online_writes": 0,
        "manifest": str(manifest_path),
    }
    summary_path = output_dir / "STAGED_image_asset_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
