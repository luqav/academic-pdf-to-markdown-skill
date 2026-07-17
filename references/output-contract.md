# Output contract

## Bundle

For `paper.pdf`, create:

```text
paper.pdf
paper.md
paper.conversion.json
```

The PDF remains the source of record. The Markdown is a searchable working surrogate. The JSON report records provenance, extraction conditions, page-level quality signals, and hashes.

## Markdown invariants

The Markdown file must contain:

1. YAML frontmatter with schema version, source filename, source SHA-256, byte size, page count, engine, extraction mode, and OCR status.
2. A short source record.
3. Exactly one ordered `<!-- pdf-page: N -->` marker for every PDF page.
4. One fenced `text` block per page, preserving within-line spacing and extracted line order while collapsing long vertical runs of blank lines.
5. An explicit placeholder for pages with no extracted text.

Do not infer heading levels, lists, tables, references, reading order, or formula semantics. Such enrichment can be created separately, but must not replace this faithful layer.

## Report invariants

The JSON report must contain:

- `schema_version`;
- source filename, size, and SHA-256;
- Markdown filename and SHA-256;
- PDF page count and normalized document metadata when available;
- extractor name and version;
- OCR policy, whether OCR ran, language, and OCR tool version when used;
- page entries with page number, extracted character and word counts, image count, and flags;
- document-level warnings.

Paths in portable metadata must be filenames or relative paths, never host-specific absolute paths.

## Meaning of page fidelity

`pdf-page: N` means the Nth physical page in the PDF file. It may not equal a printed page label such as `xii` or `143`. The converter intentionally retains visible printed page labels as extracted text and does not assert that they are bibliographic pagination.

Tables, equations, columns, ligatures, footnotes, annotations, and reading order can differ from the visual PDF even when all text is present. Any formal quotation or evidence that depends on layout must be visually checked against the unchanged PDF.
