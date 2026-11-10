#!/usr/bin/env python3
"""Validate a moderate-completeness Shopify listing manifest locally."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED_COLUMNS = [
    "product_key",
    "variant_key",
    "handle",
    "title",
    "vendor",
    "category",
    "product_type",
    "status",
    "option1_name",
    "option1_value",
    "option2_name",
    "option2_value",
    "option3_name",
    "option3_value",
    "sku",
    "barcode",
    "price",
    "compare_at_price",
    "weight",
    "weight_unit",
    "body_html",
    "original_description_ref",
    "seo_title",
    "seo_description",
    "keyword_intent",
    "category_profile",
    "category_facts_json",
    "content_mode",
    "content_change_summary",
    "unresolved_content_gaps",
    "tags",
    "collections",
    "metafields_json",
    "main_image_ref",
    "main_image_status",
    "variant_image_required",
    "variant_image_ref",
    "variant_image_status",
    "alt_text",
    "image_manifest_ref",
    "product_source",
    "identity_source",
    "price_source",
    "content_source",
    "supplement_sources",
    "approval_status",
]

PRODUCT_LEVEL_FIELDS = [
    "handle",
    "title",
    "vendor",
    "category",
    "product_type",
    "status",
    "body_html",
    "original_description_ref",
    "seo_title",
    "seo_description",
    "keyword_intent",
    "category_profile",
    "category_facts_json",
    "content_mode",
    "content_change_summary",
    "unresolved_content_gaps",
    "tags",
    "collections",
    "metafields_json",
    "main_image_ref",
    "main_image_status",
    "image_manifest_ref",
    "product_source",
    "content_source",
    "supplement_sources",
]

BASE_REQUIRED_PRODUCT_FIELDS = [
    "product_key",
    "handle",
    "title",
    "vendor",
    "category",
    "product_type",
    "status",
    "body_html",
    "original_description_ref",
    "seo_title",
    "seo_description",
    "keyword_intent",
    "category_profile",
    "category_facts_json",
    "content_mode",
    "content_change_summary",
    "unresolved_content_gaps",
    "product_source",
    "content_source",
]

BASE_REQUIRED_VARIANT_FIELDS = [
    "variant_key",
    "option1_name",
    "option1_value",
    "price",
    "identity_source",
    "price_source",
    "approval_status",
]

ALLOWED_STATUS = {"draft", "active", "archived"}
ALLOWED_CONTENT_MODES = {
    "OPTIMIZE_SUPPLIED",
    "SOURCE_BACKED_SUPPLEMENT",
    "SOURCE_BACKED_CREATE",
}
ALLOWED_APPROVAL = {"DRAFT", "REVIEW_FIRST", "USER_APPROVED"}
ALLOWED_IMAGE_STATUS = {"READY", "REVIEW", "BLOCKED"}
ALLOWED_VARIANT_IMAGE_STATUS = ALLOWED_IMAGE_STATUS | {"NOT_REQUIRED"}
ALLOWED_WEIGHT_UNIT = {"g", "kg", "oz", "lb"}
DISALLOWED_IDENTITY_SOURCE_TERMS = {
    "TITLE",
    "FUZZY",
    "INFERRED",
    "GUESSED",
    "IMAGE",
    "FILENAME",
    "SEQUENCE",
}
HANDLE_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HTML_TAG_RE = re.compile(r"<[^>]+>")


def norm(value: object) -> str:
    return "" if value is None else str(value).strip()


def plain_text(value: str) -> str:
    value = HTML_TAG_RE.sub(" ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def decimal_value(value: str) -> Decimal | None:
    value = norm(value)
    if not value:
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def truthy(value: str) -> bool | None:
    value = norm(value).upper()
    if value in {"TRUE", "YES", "1"}:
        return True
    if value in {"FALSE", "NO", "0"}:
        return False
    return None


def load_profile(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as handle:
        profile = json.load(handle)
    if norm(profile.get("completeness_tier")).upper() != "MODERATE":
        raise ValueError("profile completeness_tier must be MODERATE")
    if not isinstance(profile.get("category_profiles"), dict):
        raise ValueError("profile category_profiles must be an object")
    return profile


def add_issue(
    issues: list[dict],
    row_number: int | str,
    product_key: str,
    variant_key: str,
    severity: str,
    code: str,
    field: str,
    detail: str,
) -> None:
    issues.append(
        {
            "row_number": str(row_number),
            "product_key": product_key,
            "variant_key": variant_key,
            "severity": severity,
            "code": code,
            "field": field,
            "detail": detail,
        }
    )


def duplicate_values(rows: list[dict], field: str) -> dict[str, list[int]]:
    found: dict[str, list[int]] = defaultdict(list)
    for index, row in enumerate(rows, start=2):
        value = norm(row.get(field))
        if value:
            found[value.casefold()].append(index)
    return {key: value for key, value in found.items() if len(value) > 1}


def validate(manifest: Path, profile: dict) -> tuple[list[dict], list[dict], dict]:
    with manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        missing_columns = [name for name in REQUIRED_COLUMNS if name not in headers]
        if missing_columns:
            raise ValueError(
                "manifest missing required columns: " + ", ".join(missing_columns)
            )
        rows = [{key: norm(value) for key, value in row.items()} for row in reader]

    issues: list[dict] = []
    banned_inventory_columns = [
        name
        for name in headers
        if "inventory" in name.casefold()
        and name not in {"image_manifest_ref"}
    ]
    for column in banned_inventory_columns:
        if any(norm(row.get(column)) for row in rows):
            add_issue(
                issues,
                "*",
                "",
                "",
                "BLOCKER",
                "INVENTORY_FIELD_NOT_ALLOWED",
                column,
                "Inventory does not belong in this listing package.",
            )

    required_product = list(
        dict.fromkeys(
            BASE_REQUIRED_PRODUCT_FIELDS
            + [norm(x) for x in profile.get("required_product_fields", [])]
        )
    )
    required_variant = list(
        dict.fromkeys(
            BASE_REQUIRED_VARIANT_FIELDS
            + [norm(x) for x in profile.get("required_variant_fields", [])]
        )
    )

    require_sku = bool(profile.get("require_sku", True))
    require_barcode = bool(profile.get("require_barcode", False))
    require_weight = bool(profile.get("require_weight", True))
    require_main_image = bool(profile.get("require_main_image", True))
    seo_min = int(profile.get("seo_description_min", 120))
    seo_max = int(profile.get("seo_description_max", 160))
    body_min = int(profile.get("body_text_min_chars", 120))
    category_profiles = profile["category_profiles"]

    product_rows: dict[str, list[tuple[int, dict]]] = defaultdict(list)
    option_tuples: dict[str, dict[tuple[str, ...], list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for row_number, row in enumerate(rows, start=2):
        product_key = row["product_key"]
        variant_key = row["variant_key"]
        product_rows[product_key].append((row_number, row))

        for field in required_product:
            if not norm(row.get(field)):
                add_issue(
                    issues,
                    row_number,
                    product_key,
                    variant_key,
                    "BLOCKER",
                    "MISSING_REQUIRED_PRODUCT_FIELD",
                    field,
                    "Required product-level field is blank.",
                )
        for field in required_variant:
            if not norm(row.get(field)):
                add_issue(
                    issues,
                    row_number,
                    product_key,
                    variant_key,
                    "BLOCKER",
                    "MISSING_REQUIRED_VARIANT_FIELD",
                    field,
                    "Required variant-level field is blank.",
                )

        if row["status"].casefold() not in ALLOWED_STATUS:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_STATUS",
                "status",
                f"Expected one of {sorted(ALLOWED_STATUS)}.",
            )
        if row["handle"] and not HANDLE_RE.fullmatch(row["handle"]):
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_HANDLE",
                "handle",
                "Handle must contain lowercase letters, digits, and hyphens only.",
            )
        if row["content_mode"] not in ALLOWED_CONTENT_MODES:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_CONTENT_MODE",
                "content_mode",
                f"Expected one of {sorted(ALLOWED_CONTENT_MODES)}.",
            )
        if row["content_mode"] == "SOURCE_BACKED_CREATE":
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "WARNING",
                "CONTENT_CREATED_AS_EXCEPTION",
                "content_mode",
                "Merchant-supplied content was not optimized; verify the creation exception.",
            )
        if row["content_mode"] in {
            "SOURCE_BACKED_SUPPLEMENT",
            "SOURCE_BACKED_CREATE",
        } and not row["supplement_sources"]:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "SUPPLEMENT_SOURCE_REQUIRED",
                "supplement_sources",
                "Supplemented or newly created content requires approved sources.",
            )
        if row["unresolved_content_gaps"].upper() != "NONE":
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "WARNING",
                "UNRESOLVED_CONTENT_GAPS_DECLARED",
                "unresolved_content_gaps",
                "The product has declared unresolved content gaps.",
            )
        if row["approval_status"] not in ALLOWED_APPROVAL:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_APPROVAL_STATUS",
                "approval_status",
                f"Expected one of {sorted(ALLOWED_APPROVAL)}.",
            )

        body_length = len(plain_text(row["body_html"]))
        if row["body_html"] and body_length < body_min:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "WARNING",
                "BODY_TOO_SHORT_FOR_MODERATE",
                "body_html",
                f"Body text is {body_length} characters; profile minimum is {body_min}.",
            )
        seo_length = len(plain_text(row["seo_description"]))
        if row["seo_description"] and not (seo_min <= seo_length <= seo_max):
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "WARNING",
                "SEO_DESCRIPTION_LENGTH",
                "seo_description",
                f"SEO description is {seo_length} characters; profile range is {seo_min}-{seo_max}.",
            )

        price = decimal_value(row["price"])
        compare_at = decimal_value(row["compare_at_price"])
        if price is None or price <= 0:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_PRICE",
                "price",
                "Price must be a positive decimal.",
            )
        if row["compare_at_price"] and (
            compare_at is None or compare_at <= 0 or (price is not None and compare_at < price)
        ):
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_COMPARE_AT_PRICE",
                "compare_at_price",
                "Compare-at price must be blank or a positive value not below price.",
            )

        if require_sku and not row["sku"]:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "SKU_REQUIRED_BY_PROFILE",
                "sku",
                "Store profile requires SKU.",
            )
        if not row["barcode"]:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER" if require_barcode else "WARNING",
                "BARCODE_MISSING",
                "barcode",
                "Barcode is missing.",
            )
        identity_source_upper = row["identity_source"].upper()
        if any(term in identity_source_upper for term in DISALLOWED_IDENTITY_SOURCE_TERMS):
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "NON_DETERMINISTIC_IDENTITY_SOURCE",
                "identity_source",
                "Identity source indicates title, fuzzy, inferred, image, filename, or sequence matching.",
            )

        if require_weight:
            weight = decimal_value(row["weight"])
            if weight is None or weight <= 0:
                add_issue(
                    issues,
                    row_number,
                    product_key,
                    variant_key,
                    "BLOCKER",
                    "WEIGHT_REQUIRED_BY_PROFILE",
                    "weight",
                    "Store profile requires a positive weight.",
                )
            if row["weight_unit"].casefold() not in ALLOWED_WEIGHT_UNIT:
                add_issue(
                    issues,
                    row_number,
                    product_key,
                    variant_key,
                    "BLOCKER",
                    "INVALID_WEIGHT_UNIT",
                    "weight_unit",
                    f"Expected one of {sorted(ALLOWED_WEIGHT_UNIT)}.",
                )

        for slot in (2, 3):
            name = row[f"option{slot}_name"]
            value = row[f"option{slot}_value"]
            if bool(name) != bool(value):
                add_issue(
                    issues,
                    row_number,
                    product_key,
                    variant_key,
                    "BLOCKER",
                    "INCOMPLETE_OPTION_PAIR",
                    f"option{slot}",
                    "Option name and value must both be populated or both be blank.",
                )
        option_tuple = tuple(
            row[f"option{slot}_value"].casefold() for slot in (1, 2, 3)
        )
        option_tuples[product_key][option_tuple].append(row_number)

        if row["main_image_status"] not in ALLOWED_IMAGE_STATUS:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_MAIN_IMAGE_STATUS",
                "main_image_status",
                f"Expected one of {sorted(ALLOWED_IMAGE_STATUS)}.",
            )
        if require_main_image and (
            not row["main_image_ref"] or row["main_image_status"] != "READY"
        ):
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "MAIN_IMAGE_NOT_READY",
                "main_image_ref",
                "Profile requires an approved READY main image.",
            )
        variant_required = truthy(row["variant_image_required"])
        if variant_required is None:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_VARIANT_IMAGE_REQUIRED",
                "variant_image_required",
                "Expected TRUE or FALSE.",
            )
        if row["variant_image_status"] not in ALLOWED_VARIANT_IMAGE_STATUS:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "INVALID_VARIANT_IMAGE_STATUS",
                "variant_image_status",
                f"Expected one of {sorted(ALLOWED_VARIANT_IMAGE_STATUS)}.",
            )
        if variant_required and (
            not row["variant_image_ref"] or row["variant_image_status"] != "READY"
        ):
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "VARIANT_IMAGE_NOT_READY",
                "variant_image_ref",
                "Variant image is required but not READY.",
            )
        if not variant_required and row["variant_image_status"] == "BLOCKED":
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "WARNING",
                "NON_REQUIRED_VARIANT_IMAGE_BLOCKED",
                "variant_image_status",
                "Variant image is not required, but the supplied asset is blocked.",
            )
        if (row["main_image_ref"] or row["variant_image_ref"]) and not row["alt_text"]:
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "WARNING",
                "ALT_TEXT_MISSING",
                "alt_text",
                "Image reference exists but alt text is blank.",
            )

        profile_name = row["category_profile"]
        category_profile = category_profiles.get(profile_name)
        if not isinstance(category_profile, dict):
            add_issue(
                issues,
                row_number,
                product_key,
                variant_key,
                "BLOCKER",
                "CATEGORY_PROFILE_NOT_APPROVED",
                "category_profile",
                "Category profile is not defined in the store profile.",
            )
        else:
            try:
                facts = json.loads(row["category_facts_json"])
                if not isinstance(facts, dict):
                    raise ValueError
            except (json.JSONDecodeError, ValueError):
                facts = {}
                add_issue(
                    issues,
                    row_number,
                    product_key,
                    variant_key,
                    "BLOCKER",
                    "INVALID_CATEGORY_FACTS_JSON",
                    "category_facts_json",
                    "Expected a JSON object.",
                )
            for fact in category_profile.get("required_facts", []):
                if fact not in facts or facts[fact] in ("", None, [], {}):
                    add_issue(
                        issues,
                        row_number,
                        product_key,
                        variant_key,
                        "BLOCKER",
                        "MISSING_REQUIRED_CATEGORY_FACT",
                        str(fact),
                        "Required category decision or legal/safety fact is missing.",
                    )
            for fact in category_profile.get("important_facts", []):
                if fact not in facts or facts[fact] in ("", None, [], {}):
                    add_issue(
                        issues,
                        row_number,
                        product_key,
                        variant_key,
                        "WARNING",
                        "MISSING_IMPORTANT_CATEGORY_FACT",
                        str(fact),
                        "Useful moderate-completeness category fact is missing.",
                    )

        for json_field in ("metafields_json",):
            if row[json_field]:
                try:
                    parsed = json.loads(row[json_field])
                    if not isinstance(parsed, (dict, list)):
                        raise ValueError
                except (json.JSONDecodeError, ValueError):
                    add_issue(
                        issues,
                        row_number,
                        product_key,
                        variant_key,
                        "BLOCKER",
                        "INVALID_JSON",
                        json_field,
                        "Expected a JSON object or array.",
                    )

    for product_key, grouped in product_rows.items():
        if not product_key:
            continue
        for field in PRODUCT_LEVEL_FIELDS:
            values = {row[field] for _, row in grouped}
            if len(values) > 1:
                add_issue(
                    issues,
                    ",".join(str(number) for number, _ in grouped),
                    product_key,
                    "",
                    "BLOCKER",
                    "PRODUCT_LEVEL_INCONSISTENCY",
                    field,
                    "Rows in the same product_key do not agree.",
                )
        for option_tuple, row_numbers in option_tuples[product_key].items():
            if len(row_numbers) > 1:
                add_issue(
                    issues,
                    ",".join(str(number) for number in row_numbers),
                    product_key,
                    "",
                    "BLOCKER",
                    "DUPLICATE_OPTION_TUPLE",
                    "options",
                    f"Duplicate option tuple {option_tuple}.",
                )

    for field, code in (
        ("product_key", "DUPLICATE_PRODUCT_KEY"),
        ("variant_key", "DUPLICATE_VARIANT_KEY"),
        ("sku", "DUPLICATE_SKU"),
        ("barcode", "DUPLICATE_BARCODE"),
    ):
        duplicates = duplicate_values(rows, field)
        if field == "product_key":
            continue
        for value, row_numbers in duplicates.items():
            add_issue(
                issues,
                ",".join(str(number) for number in row_numbers),
                "",
                "",
                "BLOCKER",
                code,
                field,
                f"Duplicate value {value}.",
            )

    seo_by_value: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row["seo_description"]:
            seo_by_value[row["seo_description"].casefold()].add(row["product_key"])
    for value, product_keys in seo_by_value.items():
        if len(product_keys) > 1:
            add_issue(
                issues,
                "*",
                ",".join(sorted(product_keys)),
                "",
                "BLOCKER",
                "DUPLICATE_SEO_DESCRIPTION",
                "seo_description",
                f"Identical SEO description is used by {len(product_keys)} products.",
            )

    row_severity: dict[int, set[str]] = defaultdict(set)
    for issue in issues:
        for token in issue["row_number"].split(","):
            if token.isdigit():
                row_severity[int(token)].add(issue["severity"])

    normalized: list[dict] = []
    for row_number, row in enumerate(rows, start=2):
        severities = row_severity[row_number]
        if "BLOCKER" in severities:
            readiness = "BLOCKED"
        elif "WARNING" in severities:
            readiness = "READY_WITH_WARNINGS"
        else:
            readiness = "READY"
        normalized.append({"readiness": readiness, **row})

    severity_counts = Counter(issue["severity"] for issue in issues)
    readiness_counts = Counter(row["readiness"] for row in normalized)
    product_readiness: dict[str, str] = {}
    for product_key, grouped in product_rows.items():
        states = {
            normalized[number - 2]["readiness"]
            for number, _ in grouped
        }
        if "BLOCKED" in states:
            product_readiness[product_key] = "BLOCKED"
        elif "READY_WITH_WARNINGS" in states:
            product_readiness[product_key] = "READY_WITH_WARNINGS"
        else:
            product_readiness[product_key] = "READY"

    summary = {
        "status": "PASS" if not severity_counts["BLOCKER"] else "BLOCKED",
        "completeness_tier": "MODERATE",
        "manifest": str(manifest),
        "store_name": profile.get("store_name", ""),
        "row_count": len(rows),
        "product_count": len(product_rows),
        "variant_count": len({row["variant_key"] for row in rows if row["variant_key"]}),
        "unique_sku_count": len({row["sku"] for row in rows if row["sku"]}),
        "unique_barcode_count": len(
            {row["barcode"] for row in rows if row["barcode"]}
        ),
        "readiness_counts": dict(readiness_counts),
        "product_readiness_counts": dict(Counter(product_readiness.values())),
        "issue_counts": dict(severity_counts),
        "issue_code_counts": dict(Counter(issue["code"] for issue in issues)),
        "inventory_columns_with_values": banned_inventory_columns,
        "control_checks": {
            "rows_equal_ready_warning_blocked": len(rows)
            == sum(readiness_counts.values()),
            "products_equal_product_readiness": len(product_rows)
            == len(product_readiness),
        },
        "online_writes": 0,
    }
    return normalized, issues, summary


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    try:
        profile = load_profile(args.profile)
        normalized, issues, summary = validate(args.manifest, profile)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    normalized_path = args.output_dir / "REVIEW_FIRST_listing_normalized.csv"
    issues_path = args.output_dir / "REVIEW_FIRST_listing_gaps.csv"
    summary_path = args.output_dir / "AUDIT_listing_summary.json"

    write_csv(
        normalized_path,
        normalized,
        ["readiness", *REQUIRED_COLUMNS],
    )
    write_csv(
        issues_path,
        issues,
        [
            "row_number",
            "product_key",
            "variant_key",
            "severity",
            "code",
            "field",
            "detail",
        ],
    )
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
