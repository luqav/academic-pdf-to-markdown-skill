# Academic PDF to Markdown Skill

Convert born-digital or scanned academic PDFs into reusable, page-anchored Markdown without asking an LLM to parse or OCR the document again on every use.

The skill keeps the original PDF as the source of record and creates:

- a searchable Markdown surrogate with one marker per physical PDF page;
- a machine-readable conversion report with page-level warnings;
- SHA-256 hashes that bind both outputs to the exact source file.

Extraction and optional OCR run locally. The skill requires no API key and does not use an LLM or network service as its extraction engine.

## What “page-faithful” means

The converter preserves physical page boundaries, extracted line order, and within-line spacing where the PDF permits it. It does not claim visual identity with the PDF and does not invent headings, tables, formulas, citations, footnotes, or missing words.

Complex tables, equations, multi-column layouts, marginalia, and poor scans can still require visual checking against the original PDF.

## Install as a Codex skill

Clone the repository into your Codex skills directory:

```bash
git clone https://github.com/luqav/academic-pdf-to-markdown-skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/academic-pdf-to-markdown"
cd "${CODEX_HOME:-$HOME/.codex}/skills/academic-pdf-to-markdown"
```

Create an isolated Python environment and install the required package:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Python 3.10 or newer is required. Start a new Codex task after installation so the skill is discovered.

## Use it with Codex

Attach or identify the PDF files and ask Codex, for example:

```text
Use $academic-pdf-to-markdown to convert these papers into page-anchored
Markdown, run OCR only where necessary, and verify every output bundle.
```

For a specific folder:

```text
Use $academic-pdf-to-markdown on /path/to/papers. Store the Markdown files in
/path/to/research-cache, use English and German OCR, and report all warned pages.
```

Codex follows [SKILL.md](SKILL.md), runs the deterministic scripts, reviews warnings, and reports which pages need manual comparison with the PDF.

## Use the converter directly

Check the local runtime:

```bash
python scripts/pdf_to_markdown.py --check
```

Convert one PDF:

```bash
python scripts/pdf_to_markdown.py "/path/to/paper.pdf" \
  --output "/path/to/paper.md" \
  --language eng+deu
```

Convert a directory recursively:

```bash
python scripts/pdf_to_markdown.py "/path/to/pdfs" \
  --output "/path/to/markdown" \
  --recursive \
  --language eng+deu
```

The default `--ocr auto` policy first tries native PDF text extraction. If it detects image-only pages, it runs OCRmyPDF once and then extracts the searchable result. Use `--ocr never` only when explicit incomplete-page warnings are acceptable.

Existing Markdown and report files are protected by default. Use `--force` only when you intentionally want to replace them.

## OCR for scanned PDFs

Native-text PDFs only require the Python dependency above. Scanned PDFs additionally need OCRmyPDF, Tesseract, language data, and Ghostscript.

macOS with Homebrew:

```bash
brew install ocrmypdf tesseract tesseract-lang
```

Ubuntu or Debian:

```bash
sudo apt-get update
sudo apt-get install -y ocrmypdf tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
```

List installed OCR languages with:

```bash
tesseract --list-langs
```

## Output and verification

For `paper.pdf`, the conversion produces:

```text
paper.pdf                  original, unchanged source of record
paper.md                   page-anchored searchable text
paper.conversion.json      provenance, hashes, warnings, and page statistics
```

Verify the bundle at any time:

```bash
python scripts/verify_conversion.py "/path/to/paper.md" \
  --source "/path/to/paper.pdf"
```

Verification checks the source and Markdown hashes, page count, page-marker sequence, report schema, and report completeness. For academic quotation, also compare the relevant rendered PDF page visually and cite the publication’s printed or PDF pagination rather than Markdown line numbers.

See [the output contract](references/output-contract.md) for the exact Markdown and JSON invariants and [the setup reference](references/setup.md) for troubleshooting.

## Privacy and security

- Conversion runs locally and requires no API token.
- Source PDFs are not uploaded by the included scripts.
- Host-specific absolute paths are not written into portable metadata.
- The original PDF is never modified or replaced.
- Passwords, paywalls, DRM, and other access controls must not be bypassed.

Keep private PDFs and generated full text in access-controlled storage appropriate for the source material.

## Copyright and responsible use

Only process PDFs you are legally entitled to access and transform. A lawful copy, academic purpose, or non-commercial intent does not automatically permit public redistribution of the source or converted full text.

Respect licenses, machine-readable rights reservations, retention requirements, quotation limits, and institutional access conditions. The MIT license in this repository covers the skill’s original code and documentation; it does not grant rights to third-party PDFs or their converted text.

## License

The original code and documentation in this repository are released under the [MIT License](LICENSE).
