#!/usr/bin/env python3
"""Read-only exact SKU/UPC reconciliation for two CSV datasets."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


OUTPUT_MATRIX = "REVIEW_FIRST_identifier_reconciliation.csv"
OUTPUT_GAPS = "REVIEW_FIRST_identifier_conflicts_and_gaps.csv"
OUTPUT_SUMMARY = "AUDIT_identifier_reconciliation_summary.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile exact SKU and UPC identifiers without online writes."
    )
    parser.add_argument("--truth", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--truth-sku", required=True)
    parser.add_argument("--truth-upc", required=True)
    parser.add_argument("--target-sku", required=True)
    parser.add_argument("--target-upc", required=True)
    parser.add_argument("--truth-title")
    parser.add_argument("--target-title")
    parser.add_argument("--truth-group")
    parser.add_argument("--target-group")
    parser.add_argument("--truth-id")
    parser.add_argument("--target-id")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def text(value: str | None) -> str:
    return "" if value is None else unicodedata.normalize("NFKC", str(value)).strip()


def normalize_sku(value: str | None) -> str:
    return text(value)


def normalize_upc(value: str | None) -> tuple[str, str]:
    raw = text(value)
    compact = re.sub(r"[\s-]+", "", raw)
    if not compact:
        return "", "MISSING"
    if not compact.isdigit():
        return compact, "NON_DIGIT"
    if len(compact) not in {8, 12, 13, 14}:
        return compact, f"NON_STANDARD_LENGTH_{len(compact)}"
    return compact, "VALID" if valid_gtin_check_digit(compact) else "INVALID_CHECK_DIGIT"


def valid_gtin_check_digit(value: str) -> bool:
    if not value.isdigit() or len(value) not in {8, 12, 13, 14}:
        return False
    body = value[:-1]
    total = 0
    for offset, digit in enumerate(reversed(body), start=1):
        total += int(digit) * (3 if offset % 2 == 1 else 1)
    expected = (10 - total % 10) % 10
    return expected == int(value[-1])


def read_csv(path: Path, mappings: dict[str, str | None], label: str) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        required = {mappings["sku"], mappings["upc"]}
        missing = sorted(column for column in required if column not in columns)
        if missing:
            raise ValueError(f"{label} missing columns: {', '.join(missing)}")
        for optional in ("title", "group", "id"):
            column = mappings.get(optional)
            if column and column not in columns:
                raise ValueError(f"{label} missing optional mapped column: {column}")

        rows = []
        for row_number, row in enumerate(reader, start=2):
            upc, upc_quality = normalize_upc(row.get(mappings["upc"]))
            rows.append(
                {
                    "source": label,
                    "row_number": row_number,
                    "sku_raw": text(row.get(mappings["sku"])),
                    "sku": normalize_sku(row.get(mappings["sku"])),
                    "upc_raw": text(row.get(mappings["upc"])),
                    "upc": upc,
                    "upc_quality": upc_quality,
                    "title": text(row.get(mappings.get("title"))) if mappings.get("title") else "",
                    "group": text(row.get(mappings.get("group"))) if mappings.get("group") else "",
                    "item_id": text(row.get(mappings.get("id"))) if mappings.get("id") else "",
                }
            )
    return rows


def index_rows(rows: list[dict], field: str) -> dict[str, list[int]]:
    index: dict[str, list[int]] = defaultdict(list)
    for position, row in enumerate(rows):
        value = row[field]
        if value:
            index[value].append(position)
    return index


def duplicate_values(index: dict[str, list[int]]) -> dict[str, list[int]]:
    return {value: positions for value, positions in index.items() if len(positions) > 1}


def proposal_for(
    truth_row: dict,
    truth_position: int,
    target_rows: list[dict],
    truth_sku_index: dict[str, list[int]],
    truth_upc_index: dict[str, list[int]],
    target_sku_index: dict[str, list[int]],
    target_upc_index: dict[str, list[int]],
) -> dict:
    sku = truth_row["sku"]
    upc = truth_row["upc"]

    truth_duplicate = (
        (sku and len(truth_sku_index.get(sku, [])) > 1)
        or (upc and len(truth_upc_index.get(upc, [])) > 1)
    )
    sku_candidates = target_sku_index.get(sku, []) if sku else []
    upc_candidates = target_upc_index.get(upc, []) if upc else []
    target_duplicate = len(sku_candidates) > 1 or len(upc_candidates) > 1

    result = {
        "truth_position": truth_position,
        "target_position": None,
        "status": "",
        "match_mode": "NONE",
        "reason": "",
    }

    if not sku and not upc:
        result.update(
            status="MISSING_IDENTIFIERS",
            reason="Truth row has neither usable SKU nor UPC.",
        )
        return result

    if truth_duplicate or target_duplicate:
        result.update(
            status="DUPLICATE_CONFLICT",
            reason="SKU or UPC is duplicated in truth or target; automatic matching stopped.",
        )
        return result

    sku_target = sku_candidates[0] if len(sku_candidates) == 1 else None
    upc_target = upc_candidates[0] if len(upc_candidates) == 1 else None

    if sku_target is not None and upc_target is not None and sku_target != upc_target:
        result.update(
            status="CROSS_IDENTIFIER_CONFLICT",
            match_mode="CONFLICT",
            reason=(
                f"Exact SKU points to target row {target_rows[sku_target]['row_number']} "
                f"while exact UPC points to row {target_rows[upc_target]['row_number']}."
            ),
        )
        return result

    target_position = upc_target if upc_target is not None else sku_target
    if target_position is None:
        result.update(
            status="TRUTH_ONLY",
            reason="No exact unique SKU or UPC target match.",
        )
        return result

    target = target_rows[target_position]
    result["target_position"] = target_position

    if upc_target is not None:
        result["match_mode"] = "UPC_EXACT"
        if sku:
            if not target["sku"]:
                status = "MATCH_BY_UPC_SKU_MISSING_TARGET"
                reason = "Exact unique UPC match; target SKU is blank."
            elif target["sku"] == sku:
                status = "EXACT_BOTH"
                reason = "Exact unique UPC and SKU agree."
            else:
                status = "MATCH_BY_UPC_SKU_CONFLICT"
                reason = "Exact unique UPC match; SKU values disagree."
        else:
            status = "EXACT_UPC_ONLY"
            reason = "Exact unique UPC match; truth SKU is blank."
    else:
        result["match_mode"] = "SKU_EXACT"
        if upc:
            if not target["upc"]:
                status = "MATCH_BY_SKU_UPC_MISSING_TARGET"
                reason = "Exact unique SKU match; target UPC is blank."
            elif target["upc"] == upc:
                status = "EXACT_BOTH"
                reason = "Exact unique SKU and UPC agree."
            else:
                status = "MATCH_BY_SKU_UPC_CONFLICT"
                reason = "Exact unique SKU match; UPC values disagree."
        else:
            status = "EXACT_SKU_ONLY"
            reason = "Exact unique SKU match; truth UPC is blank."

    result.update(status=status, reason=reason)
    return result


def matrix_row(status: str, mode: str, reason: str, truth: dict | None, target: dict | None) -> dict:
    return {
        "status": status,
        "match_mode": mode,
        "truth_row": truth["row_number"] if truth else "",
        "target_row": target["row_number"] if target else "",
        "truth_item_id": truth["item_id"] if truth else "",
        "target_item_id": target["item_id"] if target else "",
        "truth_sku_raw": truth["sku_raw"] if truth else "",
        "target_sku_raw": target["sku_raw"] if target else "",
        "truth_sku_normalized": truth["sku"] if truth else "",
        "target_sku_normalized": target["sku"] if target else "",
        "truth_upc_raw": truth["upc_raw"] if truth else "",
        "target_upc_raw": target["upc_raw"] if target else "",
        "truth_upc_normalized": truth["upc"] if truth else "",
        "target_upc_normalized": target["upc"] if target else "",
        "truth_upc_quality": truth["upc_quality"] if truth else "",
        "target_upc_quality": target["upc_quality"] if target else "",
        "truth_title": truth["title"] if truth else "",
        "target_title": target["title"] if target else "",
        "truth_group": truth["group"] if truth else "",
        "target_group": target["group"] if target else "",
        "reason": reason,
        "safe_for_automatic_write": "false",
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = list(rows[0].keys()) if rows else [
        "status",
        "match_mode",
        "reason",
        "safe_for_automatic_write",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    truth_path = Path(args.truth).expanduser().resolve()
    target_path = Path(args.target).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    truth_map = {
        "sku": args.truth_sku,
        "upc": args.truth_upc,
        "title": args.truth_title,
        "group": args.truth_group,
        "id": args.truth_id,
    }
    target_map = {
        "sku": args.target_sku,
        "upc": args.target_upc,
        "title": args.target_title,
        "group": args.target_group,
        "id": args.target_id,
    }

    truth_rows = read_csv(truth_path, truth_map, "truth")
    target_rows = read_csv(target_path, target_map, "target")
    truth_sku_index = index_rows(truth_rows, "sku")
    truth_upc_index = index_rows(truth_rows, "upc")
    target_sku_index = index_rows(target_rows, "sku")
    target_upc_index = index_rows(target_rows, "upc")

    proposals = [
        proposal_for(
            row,
            position,
            target_rows,
            truth_sku_index,
            truth_upc_index,
            target_sku_index,
            target_upc_index,
        )
        for position, row in enumerate(truth_rows)
    ]

    proposed_target_counts = Counter(
        p["target_position"] for p in proposals if p["target_position"] is not None
    )
    for proposal in proposals:
        position = proposal["target_position"]
        if position is not None and proposed_target_counts[position] > 1:
            proposal.update(
                target_position=None,
                status="TARGET_REUSED_CONFLICT",
                match_mode="CONFLICT",
                reason=(
                    f"Multiple truth rows would match target row "
                    f"{target_rows[position]['row_number']}."
                ),
            )

    matrix = []
    used_targets: set[int] = set()
    for proposal in proposals:
        truth = truth_rows[proposal["truth_position"]]
        position = proposal["target_position"]
        target = target_rows[position] if position is not None else None
        if position is not None:
            used_targets.add(position)
        matrix.append(
            matrix_row(
                proposal["status"],
                proposal["match_mode"],
                proposal["reason"],
                truth,
                target,
            )
        )

    for position, target in enumerate(target_rows):
        if position not in used_targets:
            matrix.append(
                matrix_row(
                    "TARGET_ONLY",
                    "NONE",
                    "Target row was not consumed by a final exact match.",
                    None,
                    target,
                )
            )

    gaps = [row for row in matrix if row["status"] != "EXACT_BOTH"]
    write_csv(output_dir / OUTPUT_MATRIX, matrix)
    write_csv(output_dir / OUTPUT_GAPS, gaps)

    status_counts = Counter(row["status"] for row in matrix)
    truth_duplicate_skus = duplicate_values(truth_sku_index)
    truth_duplicate_upcs = duplicate_values(truth_upc_index)
    target_duplicate_skus = duplicate_values(target_sku_index)
    target_duplicate_upcs = duplicate_values(target_upc_index)

    truth_matrix_rows = sum(1 for row in matrix if row["truth_row"] != "")
    target_accounted_rows = sum(1 for row in matrix if row["target_row"] != "")
    controls = {
        "truth_rows_appear_once": truth_matrix_rows == len(truth_rows),
        "target_rows_appear_once": target_accounted_rows == len(target_rows),
        "final_target_reuse_count": len(used_targets) - len(set(used_targets)),
        "matrix_rows_equal_truth_plus_target_only": (
            len(matrix) == len(truth_rows) + status_counts["TARGET_ONLY"]
        ),
    }

    summary = {
        "status": "PASS" if all(
            [
                controls["truth_rows_appear_once"],
                controls["target_rows_appear_once"],
                controls["final_target_reuse_count"] == 0,
                controls["matrix_rows_equal_truth_plus_target_only"],
            ]
        ) else "FAIL",
        "truth_file": str(truth_path),
        "target_file": str(target_path),
        "column_mappings": {"truth": truth_map, "target": target_map},
        "truth_rows": len(truth_rows),
        "target_rows": len(target_rows),
        "truth_unique_skus": len(truth_sku_index),
        "truth_unique_upcs": len(truth_upc_index),
        "target_unique_skus": len(target_sku_index),
        "target_unique_upcs": len(target_upc_index),
        "truth_duplicate_skus": {
            value: [truth_rows[p]["row_number"] for p in positions]
            for value, positions in truth_duplicate_skus.items()
        },
        "truth_duplicate_upcs": {
            value: [truth_rows[p]["row_number"] for p in positions]
            for value, positions in truth_duplicate_upcs.items()
        },
        "target_duplicate_skus": {
            value: [target_rows[p]["row_number"] for p in positions]
            for value, positions in target_duplicate_skus.items()
        },
        "target_duplicate_upcs": {
            value: [target_rows[p]["row_number"] for p in positions]
            for value, positions in target_duplicate_upcs.items()
        },
        "truth_upc_quality": dict(Counter(row["upc_quality"] for row in truth_rows)),
        "target_upc_quality": dict(Counter(row["upc_quality"] for row in target_rows)),
        "status_counts": dict(status_counts),
        "matrix_rows": len(matrix),
        "gap_rows": len(gaps),
        "controls": controls,
        "outputs": {
            "matrix": str(output_dir / OUTPUT_MATRIX),
            "conflicts_and_gaps": str(output_dir / OUTPUT_GAPS),
            "summary": str(output_dir / OUTPUT_SUMMARY),
        },
        "safe_for_automatic_write": False,
        "online_connections": 0,
        "online_writes": 0,
    }
    (output_dir / OUTPUT_SUMMARY).write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, indent=2))
        sys.exit(1)
