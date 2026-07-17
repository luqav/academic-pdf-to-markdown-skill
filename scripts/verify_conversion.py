#!/usr/bin/env python3
"""Verify the hashes, page anchors, and report of a PDF-to-Markdown bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_frontmatter(markdown: str) -> dict[str, Any]:
    match = re.match(r"\A---\n(.*?)\n---\n", markdown, flags=re.DOTALL)
    if not match:
        raise ValueError("missing YAML frontmatter")
    values: dict[str, Any] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid frontmatter line: {line!r}")
        key, raw_value = line.split(":", 1)
        raw_value = raw_value.strip()
        try:
            values[key.strip()] = json.loads(raw_value)
        except json.JSONDecodeError:
            values[key.strip()] = raw_value
    return values


def fail_if(errors: list[str], condition: bool, message: str) -> None:
    if condition:
        errors.append(message)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify an academic PDF-to-Markdown conversion bundle.")
    parser.add_argument("markdown", type=Path, help="Converted Markdown file")
    parser.add_argument("--source", required=True, type=Path, help="Original PDF file")
    parser.add_argument("--report", type=Path, help="Conversion report; defaults beside Markdown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown_path = args.markdown.expanduser().resolve()
    source_path = args.source.expanduser().resolve()
    report_path = (
        args.report.expanduser().resolve()
        if args.report
        else markdown_path.with_name(f"{markdown_path.stem}.conversion.json")
    )
    missing = [str(path) for path in (markdown_path, source_path, report_path) if not path.is_file()]
    if missing:
        print(f"[FAILED] Missing file(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    errors: list[str] = []
    try:
        markdown_text = markdown_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(markdown_text)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"[FAILED] Markdown cannot be verified: {exc}", file=sys.stderr)
        return 1
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"[FAILED] Report cannot be verified: {exc}", file=sys.stderr)
        return 1

    source_hash = sha256_file(source_path)
    markdown_hash = sha256_file(markdown_path)
    markers = [int(value) for value in re.findall(r"<!-- pdf-page: ([1-9]\d*) -->", markdown_text)]

    expected_pages = frontmatter.get("pdf_pages")
    fail_if(errors, frontmatter.get("schema_version") != 1, "unsupported Markdown schema_version")
    fail_if(errors, frontmatter.get("source_file") != source_path.name, "source filename mismatch")
    fail_if(errors, frontmatter.get("source_sha256") != source_hash, "source SHA-256 mismatch")
    fail_if(errors, frontmatter.get("source_size_bytes") != source_path.stat().st_size, "source size mismatch")
    fail_if(errors, not isinstance(expected_pages, int) or expected_pages < 1, "invalid PDF page count")
    if isinstance(expected_pages, int) and expected_pages >= 1:
        fail_if(errors, markers != list(range(1, expected_pages + 1)), "page markers are missing, duplicated, or unordered")

    fail_if(errors, report.get("schema_version") != 1, "unsupported report schema_version")
    fail_if(errors, report.get("source", {}).get("file") != source_path.name, "report source filename mismatch")
    fail_if(errors, report.get("source", {}).get("sha256") != source_hash, "report source SHA-256 mismatch")
    fail_if(errors, report.get("source", {}).get("size_bytes") != source_path.stat().st_size, "report source size mismatch")
    fail_if(errors, report.get("markdown", {}).get("file") != markdown_path.name, "report Markdown filename mismatch")
    fail_if(errors, report.get("markdown", {}).get("sha256") != markdown_hash, "report Markdown SHA-256 mismatch")
    fail_if(errors, report.get("pdf", {}).get("page_count") != expected_pages, "report page count mismatch")

    report_pages = report.get("pages")
    if not isinstance(report_pages, list):
        errors.append("report pages must be a list")
    elif isinstance(expected_pages, int):
        report_numbers = [page.get("page") for page in report_pages if isinstance(page, dict)]
        fail_if(errors, report_numbers != list(range(1, expected_pages + 1)), "report page entries are incomplete or unordered")

    if errors:
        print("[FAILED] Conversion bundle is not valid:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    warnings = report.get("warnings") or []
    print(f"[OK] Verified {source_path.name}: {expected_pages} page(s)")
    print(f"     source_sha256={source_hash}")
    print(f"     markdown_sha256={markdown_hash}")
    print(f"     warnings={', '.join(warnings) if warnings else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
