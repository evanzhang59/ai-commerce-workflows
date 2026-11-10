#!/usr/bin/env python3
"""Read-only product image manifest auditor."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageStat


REQUIRED_COLUMNS = {
    "asset_id",
    "file_path",
    "product_key",
    "asset_role",
    "approval_status",
    "visual_review_status",
    "identity_basis",
}
ALLOWED_ROLES = {
    "PRODUCT_MAIN",
    "VARIANT_MAIN",
    "PACKAGING",
    "TEXTURE",
    "LIFESTYLE",
    "DETAIL",
    "SWATCH",
    "MODEL",
}
EXACT_IDENTITY = {
    "UPC_EXACT",
    "SKU_EXACT",
    "UPC_AND_SKU_EXACT",
    "EXPLICIT_VARIANT_ID",
    "APPROVED_PRODUCT_LEVEL_FALLBACK",
}
MAIN_ROLES = {"PRODUCT_MAIN", "VARIANT_MAIN"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--asset-root", default=".")
    parser.add_argument(
        "--channel",
        required=True,
        choices=["generic", "nordstrom", "shopify", "target"],
    )
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return value.strip("-._") or "asset"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dhash(image: Image.Image, size: int = 8) -> str:
    gray = image.convert("L").resize((size + 1, size))
    pixels = list(gray.get_flattened_data())
    value = 0
    for row in range(size):
        offset = row * (size + 1)
        for col in range(size):
            value = (value << 1) | int(
                pixels[offset + col] > pixels[offset + col + 1]
            )
    return f"{value:0{size * size // 4}x}"


def edge_white_score(image: Image.Image) -> float:
    rgb = image.convert("RGB")
    width, height = rgb.size
    band = max(1, min(width, height) // 100)
    boxes = [
        (0, 0, width, band),
        (0, height - band, width, height),
        (0, 0, band, height),
        (width - band, 0, width, height),
    ]
    white = 0
    total = 0
    for box in boxes:
        for red, green, blue in rgb.crop(box).get_flattened_data():
            total += 1
            if red >= 250 and green >= 250 and blue >= 250:
                white += 1
    return white / total if total else 0.0


def corners_are_white(image: Image.Image) -> bool:
    rgb = image.convert("RGB")
    width, height = rgb.size
    patch = max(1, min(20, width // 20, height // 20))
    boxes = [
        (0, 0, patch, patch),
        (width - patch, 0, width, patch),
        (0, height - patch, patch, height),
        (width - patch, height - patch, width, height),
    ]
    for box in boxes:
        if any(channel < 250 for channel in ImageStat.Stat(rgb.crop(box)).mean):
            return False
    return True


def has_alpha(image: Image.Image) -> bool:
    if image.mode in {"RGBA", "LA"}:
        return True
    return image.mode == "P" and "transparency" in image.info


def add_code(codes: list[str], code: str) -> None:
    if code and code not in codes:
        codes.append(code)


def default_filename(row: dict[str, str], extension: str) -> str:
    identifier = clean(row.get("upc")) or clean(row.get("sku"))
    role = clean(row.get("asset_role")).lower().replace("_", "-")
    position = clean(row.get("media_position"))
    if position.isdigit():
        index = f"{int(position):02d}"
    elif role in {"product-main", "variant-main"}:
        index = "01"
    else:
        index = "99"
    return f"{safe_name(identifier)}-{index}-{safe_name(role)}{extension.lower()}"


def gap_from(row: dict[str, str], status: str, code: str) -> dict[str, str]:
    return {
        "asset_id": clean(row.get("asset_id")),
        "status": status,
        "code": code,
        "file_path": clean(row.get("resolved_path")) or clean(row.get("file_path")),
        "upc": clean(row.get("upc")),
        "sku": clean(row.get("sku")),
        "variant_key": clean(row.get("variant_key")),
    }


def audit_row(
    row: dict[str, str], asset_root: Path, channel: str
) -> tuple[dict[str, str], list[dict[str, str]]]:
    out = dict(row)
    errors: list[str] = []
    warnings: list[str] = []

    role = clean(row.get("asset_role")).upper()
    upc = clean(row.get("upc"))
    sku = clean(row.get("sku"))
    variant_key = clean(row.get("variant_key"))
    identity_basis = clean(row.get("identity_basis")).upper()
    approval = clean(row.get("approval_status")).upper()
    visual = clean(row.get("visual_review_status")).upper()

    raw_path = Path(clean(row.get("file_path")))
    path = raw_path if raw_path.is_absolute() else asset_root / raw_path
    path = path.resolve()

    if role not in ALLOWED_ROLES:
        add_code(errors, "INVALID_ASSET_ROLE")
    if not upc and not sku:
        add_code(errors, "MISSING_EXACT_IDENTIFIER")
    if identity_basis not in EXACT_IDENTITY:
        add_code(errors, "UNAPPROVED_IDENTITY_BASIS")
    if role == "VARIANT_MAIN" and not variant_key:
        add_code(errors, "VARIANT_MAIN_MISSING_VARIANT_KEY")
    if approval != "APPROVED":
        add_code(errors, "ASSET_NOT_APPROVED")
    if visual != "PASS":
        add_code(errors, "VISUAL_REVIEW_NOT_PASSED")

    out.update(
        {
            "resolved_path": str(path),
            "file_exists": "false",
            "file_size_mb": "",
            "sha256": "",
            "dhash": "",
            "format": "",
            "width": "",
            "height": "",
            "aspect_ratio": "",
            "mode": "",
            "has_alpha": "",
            "corners_white": "",
            "edge_white_score": "",
            "recommended_size": "",
            "proposed_filename": clean(row.get("output_filename")),
            "exact_duplicate_group": "",
            "perceptual_duplicate_group": "",
        }
    )

    if not path.is_file():
        add_code(errors, "FILE_MISSING")
    else:
        out["file_exists"] = "true"
        out["file_size_mb"] = f"{path.stat().st_size / (1024 * 1024):.3f}"
        try:
            out["sha256"] = sha256(path)
            with Image.open(path) as image:
                image.load()
                width, height = image.size
                ratio = width / height if height else 0
                alpha = has_alpha(image)
                corners_white = corners_are_white(image)
                edge_score = edge_white_score(image)
                out.update(
                    {
                        "format": clean(image.format).upper(),
                        "width": str(width),
                        "height": str(height),
                        "aspect_ratio": f"{ratio:.6f}",
                        "mode": image.mode,
                        "has_alpha": str(alpha).lower(),
                        "corners_white": str(corners_white).lower(),
                        "edge_white_score": f"{edge_score:.4f}",
                        "dhash": dhash(image),
                        "recommended_size": str(
                            width >= 2600 and height >= 4000
                        ).lower(),
                    }
                )

                if not out["proposed_filename"]:
                    extension = (
                        ".jpg"
                        if channel in {"nordstrom", "target"}
                        else (path.suffix or ".jpg")
                    )
                    out["proposed_filename"] = default_filename(row, extension)

                if float(out["file_size_mb"]) > 10:
                    add_code(warnings, "FILE_OVER_10MB")

                if role in MAIN_ROLES and channel in {"nordstrom", "target"}:
                    ratio_ok = abs(ratio - (2 / 3)) <= 0.025
                    if width < 1300 or height < 2000:
                        add_code(errors, "BELOW_CHANNEL_MINIMUM_DIMENSIONS")
                    if not ratio_ok or width >= height:
                        add_code(errors, "INVALID_PORTRAIT_2X3_RATIO")
                    if alpha:
                        add_code(errors, "ALPHA_NOT_ALLOWED_FOR_MAIN")
                    if image.mode != "RGB":
                        add_code(errors, "MAIN_NOT_RGB")
                    if not corners_white or edge_score < 0.90:
                        add_code(errors, "MAIN_BACKGROUND_NOT_WHITE")
                    if out["format"] not in {"JPEG", "JPG"}:
                        add_code(warnings, "JPG_PREFERRED")
                    if width < 2600 or height < 4000:
                        add_code(warnings, "BELOW_RECOMMENDED_2600X4000")

                if role in MAIN_ROLES and channel == "shopify":
                    if not corners_white or edge_score < 0.85:
                        add_code(warnings, "SHOPIFY_MAIN_WHITE_BACKGROUND_REVIEW")
                    if (
                        role == "VARIANT_MAIN"
                        and identity_basis == "APPROVED_PRODUCT_LEVEL_FALLBACK"
                    ):
                        add_code(errors, "VARIANT_MAIN_REQUIRES_EXACT_VARIANT_IMAGE")
        except Exception as exc:
            add_code(errors, "CORRUPT_OR_UNSUPPORTED_IMAGE")
            out["read_error"] = f"{type(exc).__name__}: {exc}"

    if errors:
        status = "BLOCKED"
    elif warnings:
        status = "REVIEW"
    else:
        status = "READY"
    out["status"] = status
    out["errors"] = "|".join(errors)
    out["warnings"] = "|".join(warnings)
    gaps = [gap_from(out, "BLOCKED", code) for code in errors]
    gaps.extend(gap_from(out, "REVIEW", code) for code in warnings)
    return out, gaps


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    manifest = Path(args.manifest).resolve()
    asset_root = Path(args.asset_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    with manifest.open("r", newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Missing manifest columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    ids = [clean(row.get("asset_id")) for row in rows]
    duplicate_ids = sorted(
        key for key, count in Counter(ids).items() if key and count > 1
    )
    if duplicate_ids:
        raise SystemExit(f"Duplicate asset_id values: {', '.join(duplicate_ids)}")

    audited: list[dict[str, str]] = []
    gaps: list[dict[str, str]] = []
    for row in rows:
        result, row_gaps = audit_row(row, asset_root, args.channel)
        audited.append(result)
        gaps.extend(row_gaps)

    sha_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    dhash_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in audited:
        if row.get("sha256"):
            sha_groups[row["sha256"]].append(row)
        if row.get("dhash"):
            dhash_groups[row["dhash"]].append(row)

    exact_duplicate_groups = 0
    perceptual_duplicate_groups = 0
    for digest, group in sha_groups.items():
        if len(group) < 2:
            continue
        exact_duplicate_groups += 1
        identities = {
            (clean(item.get("upc")), clean(item.get("sku"))) for item in group
        }
        for item in group:
            item["exact_duplicate_group"] = digest[:12]
            if item["status"] == "READY":
                item["status"] = "REVIEW"
            gaps.append(gap_from(item, "REVIEW", "EXACT_DUPLICATE"))
            if len(identities) > 1:
                gaps.append(
                    gap_from(item, "REVIEW", "CROSS_IDENTITY_EXACT_DUPLICATE")
                )

    for digest, group in dhash_groups.items():
        unique_sha = {item.get("sha256") for item in group}
        if len(group) < 2 or len(unique_sha) < 2:
            continue
        perceptual_duplicate_groups += 1
        for item in group:
            item["perceptual_duplicate_group"] = digest
            if item["status"] == "READY":
                item["status"] = "REVIEW"
            gaps.append(
                gap_from(item, "REVIEW", "PERCEPTUAL_DUPLICATE_CANDIDATE")
            )

    audit_path = output_dir / "REVIEW_FIRST_image_asset_audit.csv"
    gaps_path = output_dir / "REVIEW_FIRST_image_asset_gaps.csv"
    summary_path = output_dir / "AUDIT_image_asset_summary.json"
    write_csv(audit_path, audited)
    write_csv(
        gaps_path,
        gaps
        or [
            {
                "asset_id": "",
                "status": "PASS",
                "code": "NO_GAPS",
                "file_path": "",
                "upc": "",
                "sku": "",
                "variant_key": "",
            }
        ],
    )

    status_counts = Counter(row["status"] for row in audited)
    summary = {
        "status": (
            "PASS"
            if status_counts["BLOCKED"] == 0 and status_counts["REVIEW"] == 0
            else "REVIEW_REQUIRED"
        ),
        "channel": args.channel,
        "manifest": str(manifest),
        "asset_root": str(asset_root),
        "rows": len(audited),
        "unique_asset_ids": len(set(ids)),
        "unique_physical_files": len(
            {
                row["resolved_path"]
                for row in audited
                if row["file_exists"] == "true"
            }
        ),
        "ready": status_counts["READY"],
        "review": status_counts["REVIEW"],
        "blocked": status_counts["BLOCKED"],
        "missing_files": sum(row["file_exists"] == "false" for row in audited),
        "exact_duplicate_groups": exact_duplicate_groups,
        "perceptual_duplicate_candidate_groups": perceptual_duplicate_groups,
        "online_writes": 0,
        "source_pixels_modified": 0,
        "outputs": {
            "audit": str(audit_path),
            "gaps": str(gaps_path),
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if status_counts["BLOCKED"]:
        return 2
    return 1 if status_counts["REVIEW"] else 0


if __name__ == "__main__":
    sys.exit(main())
