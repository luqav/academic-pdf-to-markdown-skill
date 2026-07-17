#!/usr/bin/env python3
"""Convert PDFs into page-anchored Markdown without model-based parsing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
MIN_PYTHON = (3, 10)


class ConversionError(RuntimeError):
    """A conversion cannot be completed without risking silent data loss."""


@dataclass
class PageExtraction:
    number: int
    text: str
    character_count: int
    word_count: int
    image_count: int
    flags: list[str]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_text(value: str | None, *, collapse_blank_runs: bool = False) -> str:
    if not value:
        return ""
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    lines = [line.rstrip() for line in value.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if collapse_blank_runs:
        compacted: list[str] = []
        blank_count = 0
        for line in lines:
            if line.strip():
                blank_count = 0
                compacted.append(line)
            else:
                blank_count += 1
                if blank_count <= 2:
                    compacted.append("")
        lines = compacted
    return "\n".join(lines)


def portable_metadata(raw: dict[str, Any] | None) -> dict[str, str]:
    if not raw:
        return {}
    result: dict[str, str] = {}
    for key, value in sorted(raw.items(), key=lambda item: str(item[0]).lower()):
        normalized_key = str(key).lstrip("/").strip()
        if not normalized_key or value is None:
            continue
        normalized_value = clean_text(str(value))
        if normalized_value:
            result[normalized_key] = normalized_value
    return result


def extract_pdf(path: Path, min_chars: int) -> tuple[list[PageExtraction], dict[str, str], str]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise ConversionError(
            "Missing dependency 'pdfplumber'. Install requirements.txt in the skill folder."
        ) from exc

    pages: list[PageExtraction] = []
    try:
        with pdfplumber.open(path) as pdf:
            metadata = portable_metadata(pdf.metadata)
            for number, page in enumerate(pdf.pages, start=1):
                try:
                    text = clean_text(page.extract_text(layout=True) or "", collapse_blank_runs=True)
                except Exception as exc:  # page-specific parser failures must be visible
                    text = ""
                    extraction_error = f"extraction_error:{type(exc).__name__}"
                else:
                    extraction_error = ""

                character_count = len(re.sub(r"\s+", "", text))
                word_count = len(re.findall(r"\S+", text))
                image_count = len(page.images or [])
                flags: list[str] = []
                if extraction_error:
                    flags.append(extraction_error)
                if character_count == 0 and image_count == 0:
                    flags.append("blank_or_unextractable")
                if character_count == 0 and image_count > 0:
                    flags.append("image_only")
                elif 0 < character_count < min_chars:
                    flags.append("low_text")

                pages.append(
                    PageExtraction(
                        number=number,
                        text=text,
                        character_count=character_count,
                        word_count=word_count,
                        image_count=image_count,
                        flags=flags,
                    )
                )
    except ConversionError:
        raise
    except Exception as exc:
        raise ConversionError(f"Could not open or parse PDF: {exc}") from exc

    if not pages:
        raise ConversionError("The PDF contains no pages.")
    return pages, metadata, pdfplumber.__version__


def command_version(command: str) -> str:
    try:
        result = subprocess.run(
            [command, "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return (result.stdout or result.stderr).strip().splitlines()[0]


def run_ocr(source: Path, target: Path, language: str) -> tuple[str, str]:
    executable = shutil.which("ocrmypdf")
    if not executable:
        raise ConversionError(
            "Image-only pages require one-time OCR, but 'ocrmypdf' is unavailable. "
            "Install OCRmyPDF or rerun with --ocr never to retain explicit warnings."
        )

    command = [
        executable,
        "--skip-text",
        "--rotate-pages",
        "--deskew",
        "--language",
        language,
        "--output-type",
        "pdf",
        str(source),
        str(target),
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        diagnostic = (result.stderr or result.stdout).strip()
        if len(diagnostic) > 1200:
            diagnostic = diagnostic[-1200:]
        raise ConversionError(f"OCRmyPDF failed: {diagnostic or 'unknown error'}")
    return executable, command_version(executable)


def fence_for(text: str) -> str:
    runs = [len(match.group(0)) for match in re.finditer(r"`+", text)]
    return "`" * max(3, (max(runs) + 1) if runs else 3)


def yaml_value(value: Any) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return json.dumps(str(value), ensure_ascii=False)


def build_markdown(
    source: Path,
    source_hash: str,
    source_size: int,
    pages: list[PageExtraction],
    extractor_version: str,
    ocr_policy: str,
    ocr_status: str,
    metadata: dict[str, str],
) -> str:
    frontmatter = {
        "schema_version": SCHEMA_VERSION,
        "source_file": source.name,
        "source_sha256": source_hash,
        "source_size_bytes": source_size,
        "pdf_pages": len(pages),
        "extraction_engine": f"pdfplumber {extractor_version}",
        "extraction_mode": "page-faithful-layout",
        "ocr_policy": ocr_policy,
        "ocr_status": ocr_status,
    }
    lines = ["---"]
    lines.extend(f"{key}: {yaml_value(value)}" for key, value in frontmatter.items())
    lines.extend(
        [
            "---",
            "",
            f"# {source.stem}",
            "",
            "## Source record",
            "",
            f"- Source file: `{source.name}`",
            f"- Source SHA-256: `{source_hash}`",
            f"- Physical PDF pages: {len(pages)}",
            f"- Extraction engine: pdfplumber {extractor_version}",
            f"- OCR status: {ocr_status}",
        ]
    )
    if metadata.get("Title"):
        lines.append(f"- PDF metadata title: {metadata['Title']}")
    if metadata.get("Author"):
        lines.append(f"- PDF metadata author: {metadata['Author']}")

    for page in pages:
        page_text = page.text or "[No extractable text on this PDF page.]"
        fence = fence_for(page_text)
        lines.extend(
            [
                "",
                f'<a id="pdf-page-{page.number}"></a>',
                f"<!-- pdf-page: {page.number} -->",
                f"## PDF page {page.number}",
                "",
                f"{fence}text",
                page_text,
                fence,
            ]
        )
    return "\n".join(lines) + "\n"


def build_report(
    source: Path,
    source_hash: str,
    source_size: int,
    markdown_path: Path,
    markdown_hash: str,
    pages: list[PageExtraction],
    metadata: dict[str, str],
    extractor_version: str,
    ocr_policy: str,
    ocr_ran: bool,
    ocr_language: str,
    ocr_version: str | None,
) -> dict[str, Any]:
    warnings: list[str] = []
    for page in pages:
        for flag in page.flags:
            warning = f"page_{page.number}:{flag}"
            if warning not in warnings:
                warnings.append(warning)
    return {
        "schema_version": SCHEMA_VERSION,
        "source": {
            "file": source.name,
            "size_bytes": source_size,
            "sha256": source_hash,
        },
        "markdown": {
            "file": markdown_path.name,
            "sha256": markdown_hash,
        },
        "pdf": {
            "page_count": len(pages),
            "metadata": metadata,
        },
        "extraction": {
            "engine": "pdfplumber",
            "engine_version": extractor_version,
            "mode": "page-faithful-layout",
        },
        "ocr": {
            "policy": ocr_policy,
            "ran": ocr_ran,
            "language": ocr_language if ocr_ran else None,
            "engine": "OCRmyPDF" if ocr_ran else None,
            "engine_version": ocr_version,
        },
        "pages": [
            {
                "page": page.number,
                "character_count": page.character_count,
                "word_count": page.word_count,
                "image_count": page.image_count,
                "flags": page.flags,
            }
            for page in pages
        ],
        "warnings": warnings,
    }


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def convert_one(
    source: Path,
    markdown_path: Path,
    ocr_policy: str,
    language: str,
    min_chars: int,
    force: bool,
) -> tuple[Path, Path, list[str], bool]:
    report_path = markdown_path.with_name(f"{markdown_path.stem}.conversion.json")
    if not force:
        existing = [str(path) for path in (markdown_path, report_path) if path.exists()]
        if existing:
            raise ConversionError(f"Refusing to overwrite existing output: {', '.join(existing)}")

    source_hash = sha256_file(source)
    source_size = source.stat().st_size
    pages, metadata, extractor_version = extract_pdf(source, min_chars)
    original_page_count = len(pages)
    image_only_pages = [page.number for page in pages if "image_only" in page.flags]
    ocr_ran = False
    ocr_version: str | None = None

    if image_only_pages and ocr_policy == "auto":
        with tempfile.TemporaryDirectory(prefix="academic-pdf-ocr-") as temp_dir:
            searchable_pdf = Path(temp_dir) / "searchable.pdf"
            _, ocr_version = run_ocr(source, searchable_pdf, language)
            pages, _, extractor_version = extract_pdf(searchable_pdf, min_chars)
            if len(pages) != original_page_count:
                raise ConversionError(
                    f"OCR changed page count from {original_page_count} to {len(pages)}; no output written."
                )
            ocr_ran = True

    if ocr_ran:
        ocr_status = "performed-once"
    elif image_only_pages and ocr_policy == "never":
        ocr_status = "disabled-with-image-only-pages"
    else:
        ocr_status = "not-needed"

    markdown = build_markdown(
        source=source,
        source_hash=source_hash,
        source_size=source_size,
        pages=pages,
        extractor_version=extractor_version,
        ocr_policy=ocr_policy,
        ocr_status=ocr_status,
        metadata=metadata,
    )
    markdown_bytes = markdown.encode("utf-8")
    report = build_report(
        source=source,
        source_hash=source_hash,
        source_size=source_size,
        markdown_path=markdown_path,
        markdown_hash=sha256_bytes(markdown_bytes),
        pages=pages,
        metadata=metadata,
        extractor_version=extractor_version,
        ocr_policy=ocr_policy,
        ocr_ran=ocr_ran,
        ocr_language=language,
        ocr_version=ocr_version,
    )
    report_bytes = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

    atomic_write(markdown_path, markdown_bytes)
    try:
        atomic_write(report_path, report_bytes)
    except Exception:
        markdown_path.unlink(missing_ok=True)
        raise
    return markdown_path, report_path, report["warnings"], ocr_ran


def collect_sources(source: Path, recursive: bool) -> list[Path]:
    if source.is_file():
        if source.suffix.lower() != ".pdf":
            raise ConversionError(f"Input is not a PDF: {source}")
        return [source]
    if not source.is_dir():
        raise ConversionError(f"Input does not exist: {source}")
    pattern = "**/*.pdf" if recursive else "*.pdf"
    sources = sorted((path for path in source.glob(pattern) if path.is_file()), key=lambda p: str(p).lower())
    if not sources:
        raise ConversionError(f"No PDF files found in {source}")
    return sources


def output_for(source_root: Path, source: Path, output: Path | None) -> Path:
    if source_root.is_file():
        if output is None:
            return source.with_suffix(".md")
        if output.exists() and output.is_dir():
            return output / f"{source.stem}.md"
        if output.suffix.lower() != ".md":
            raise ConversionError("For a single PDF, --output must be a .md file or an existing directory.")
        return output

    output_root = output or (source_root / "markdown")
    if output_root.suffix.lower() == ".md":
        raise ConversionError("For a PDF directory, --output must be a directory.")
    relative = source.relative_to(source_root)
    return output_root / relative.with_suffix(".md")


def check_runtime() -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python >= 3.10", sys.version_info >= MIN_PYTHON, sys.version.split()[0]))
    try:
        import pdfplumber
    except ImportError:
        checks.append(("pdfplumber", False, "missing"))
    else:
        checks.append(("pdfplumber", True, pdfplumber.__version__))
    ocr = shutil.which("ocrmypdf")
    checks.append(("OCRmyPDF (optional)", bool(ocr), command_version(ocr) if ocr else "missing"))

    for label, available, detail in checks:
        status = "OK" if available else ("OPTIONAL" if label.startswith("OCRmyPDF") else "MISSING")
        print(f"[{status}] {label}: {detail}")
    return 0 if all(available for label, available, _ in checks if not label.startswith("OCRmyPDF")) else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a PDF or directory of PDFs into page-anchored Markdown and integrity reports."
    )
    parser.add_argument("source", nargs="?", type=Path, help="PDF file or directory")
    parser.add_argument("--output", type=Path, help="Markdown file or output directory")
    parser.add_argument("--recursive", action="store_true", help="Recurse when SOURCE is a directory")
    parser.add_argument("--ocr", choices=("auto", "never"), default="auto", help="One-time OCR policy")
    parser.add_argument("--language", default="eng", help="Tesseract language set, e.g. eng+deu")
    parser.add_argument("--min-chars", type=int, default=40, help="Flag nonempty pages below this character count")
    parser.add_argument("--force", action="store_true", help="Replace existing Markdown and report")
    parser.add_argument("--check", action="store_true", help="Check runtime dependencies and exit")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        return check_runtime()
    if args.source is None:
        print("error: SOURCE is required unless --check is used", file=sys.stderr)
        return 2
    if args.min_chars < 0:
        print("error: --min-chars must be non-negative", file=sys.stderr)
        return 2

    source_root = args.source.expanduser().resolve()
    output = args.output.expanduser().resolve() if args.output else None
    failures: list[str] = []
    try:
        sources = collect_sources(source_root, args.recursive)
    except ConversionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for source in sources:
        try:
            markdown_path = output_for(source_root, source, output)
            markdown, report, warnings, ocr_ran = convert_one(
                source=source,
                markdown_path=markdown_path,
                ocr_policy=args.ocr,
                language=args.language,
                min_chars=args.min_chars,
                force=args.force,
            )
        except ConversionError as exc:
            failures.append(f"{source}: {exc}")
            print(f"[FAILED] {source}: {exc}", file=sys.stderr)
            continue
        except Exception as exc:
            failures.append(f"{source}: unexpected {type(exc).__name__}: {exc}")
            print(f"[FAILED] {source}: unexpected {type(exc).__name__}: {exc}", file=sys.stderr)
            continue

        warning_text = ", ".join(warnings) if warnings else "none"
        print(f"[OK] {source} -> {markdown}")
        print(f"     report={report} ocr={'yes' if ocr_ran else 'no'} warnings={warning_text}")

    if failures:
        print(f"Completed with {len(failures)} failure(s).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
