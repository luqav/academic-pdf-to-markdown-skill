---
name: academic-pdf-to-markdown
description: Convert born-digital or scanned academic PDF files into deterministic, page-anchored Markdown plus a machine-readable integrity report. Use when ingesting papers, books, chapters, reports, theses, or source collections for repeated research, quotation, note-taking, retrieval, or citation without asking an LLM to OCR or reinterpret the PDF on every use. Detect image-only pages, run one-time OCR only when required, preserve original page boundaries, bind outputs to the source with SHA-256, and verify conversion completeness.
---

# Academic PDF to Markdown

Create a reusable text surrogate for a PDF while preserving the original as the authority. Treat "1:1" as page-faithful text extraction: retain page boundaries and extracted layout without inventing structure or content. Do not claim visual or semantic identity for arbitrary PDFs.

## Non-negotiable contract

- Never modify or replace the source PDF.
- Never use an LLM or vision model as the primary extraction engine.
- Never silently omit unreadable, encrypted, image-only, or low-text pages.
- Never reconstruct missing words, formulas, tables, citations, or footnotes from context.
- Process only PDFs the user is legally entitled to access and transform.
- Never bypass passwords, paywalls, DRM, or other access controls.
- Never publish or redistribute a source PDF or converted full text without permission or another valid legal basis.
- Respect licenses, machine-readable rights reservations, retention duties, and institutional access conditions.
- Keep one `<!-- pdf-page: N -->` marker for every PDF page, including blank pages.
- Bind the Markdown and report to the exact source bytes with SHA-256.
- Cite the publication's printed or PDF page number, not Markdown line numbers. Treat page markers as navigation aids when printed numbering differs.

Read [references/output-contract.md](references/output-contract.md) before changing the output format. Read [references/setup.md](references/setup.md) only when dependencies are missing or OCR is required.

## Workflow

### 1. Locate and protect inputs

Resolve the requested PDF files and output directory. Preserve filenames where practical. Do not overwrite an existing conversion unless the user explicitly requests replacement; pass `--force` only with that authority.

Check the runtime when uncertain:

```bash
python scripts/pdf_to_markdown.py --check
```

### 2. Convert once

Convert one file:

```bash
python scripts/pdf_to_markdown.py SOURCE.pdf --output OUTPUT.md
```

Convert a directory while preserving its relative structure:

```bash
python scripts/pdf_to_markdown.py SOURCE_DIR --output OUTPUT_DIR --recursive
```

The default `--ocr auto` first performs native extraction. If a page appears image-only, it runs OCRmyPDF once and extracts the resulting searchable copy. It never sends pages to an LLM. Use `--ocr never` only when the user accepts flagged pages remaining incomplete.

Use `--language eng+deu` or another installed Tesseract language set for scanned material. Do not guess a language when the document language is unknown; inspect the title page or ask.

### 3. Inspect warnings

Review the console result and each `.conversion.json` report. Investigate:

- `image_only` or `low_text` pages;
- pages containing tables, multi-column layouts, equations, marginalia, or footnotes;
- encrypted or malformed PDFs;
- OCR language mismatches;
- unexpectedly empty pages.

Blank pages are valid when present in the source. A warning is not permission to fabricate content.

### 4. Verify deterministically

Run:

```bash
python scripts/verify_conversion.py OUTPUT.md --source SOURCE.pdf
```

Require a passing source hash, Markdown hash, page sequence, report schema, and page count before treating the conversion as reusable.

For academic use, also spot-check the title/metadata page, one ordinary prose page, every warned page, and representative tables, equations, footnotes, and references against rendered PDF pages. Record limitations in research notes rather than editing extracted text to look correct.

### 5. Hand off the source bundle

Keep these files together:

- the unchanged `.pdf` authority;
- the page-anchored `.md` working surrogate;
- the `.conversion.json` integrity and quality report.

Report the output paths, whether OCR ran, warned pages, and verification result. Explain that downstream agents may read and quote from the Markdown cache, but must preserve the page anchor and use the original publication metadata for formal citations.

## Copyright and lawful use

Treat conversion as copying and transformation, not as permission to reuse a work. Before processing, confirm that the PDF comes from a lawful source and that the intended conversion, storage, quotation, sharing, and retention are permitted by the applicable license, law, and institutional policy. Academic or non-commercial intent alone does not create blanket permission to reproduce or distribute complete works.

Keep source PDFs and converted full texts private unless the user has permission or another valid legal basis to share them. Use only the portions needed when quoting or publishing research, preserve attribution and page references, and do not imply that this skill's MIT license covers third-party publications or derived text. Delete derived copies when the applicable legal basis, license, or retention period no longer permits keeping them.

If authorization is uncertain—especially for complete books, journal issues, licensed databases, commercial use, public datasets, or collaborative repositories—stop before conversion or distribution and ask the user to confirm permission or obtain guidance from their library, institution, or qualified legal counsel.

## Downstream research use

When answering from a converted source:

1. Verify the bundle if it may have moved or changed.
2. Search the Markdown rather than reparsing the PDF.
3. Keep quotations inside a single page block when possible.
4. If a quotation crosses a page boundary, record both page anchors.
5. Distinguish the PDF page index from printed pagination shown in the extracted text.
6. Return to the original PDF only for visual evidence, ambiguous extraction, or formal pagination checks.
