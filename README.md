# Academic PDF to Markdown

An agent-portable skill and standalone CLI for converting born-digital or scanned academic PDFs into reusable, page-anchored Markdown. Convert a source once, verify it, and let your research workflow reuse the Markdown instead of asking an LLM to parse or OCR the PDF again on every use.

The skill keeps the original PDF as the source of record and creates:

- a searchable Markdown surrogate with one marker per physical PDF page;
- a machine-readable conversion report with page-level warnings;
- SHA-256 hashes that bind both outputs to the exact source file.

Extraction and optional OCR run locally. The toolkit requires no model-provider API key and does not use an LLM or network service as its extraction engine.

Use it with Codex, Claude Code, another agent that supports `SKILL.md`, or directly from the command line without an AI assistant.

## What “page-faithful” means

The converter preserves physical page boundaries, extracted line order, and within-line spacing where the PDF permits it. It does not claim visual identity with the PDF and does not invent headings, tables, formulas, citations, footnotes, or missing words.

Complex tables, equations, multi-column layouts, marginalia, and poor scans can still require visual checking against the original PDF.

## Choose how to install it

### Standalone CLI or another agent

Clone the repository anywhere convenient:

```bash
git clone https://github.com/luqav/academic-pdf-to-markdown-skill.git
cd academic-pdf-to-markdown-skill
```

Agents without native skill discovery can still use the toolkit: give the agent access to the repository, ask it to read [SKILL.md](SKILL.md), and have it execute the included scripts. You can also ignore the agent instructions and use the CLI directly.

### Codex

Clone the repository into your Codex skills directory:

```bash
git clone https://github.com/luqav/academic-pdf-to-markdown-skill.git \
  "${CODEX_HOME:-$HOME/.codex}/skills/academic-pdf-to-markdown"
cd "${CODEX_HOME:-$HOME/.codex}/skills/academic-pdf-to-markdown"
```

Start a new Codex task after installation so the skill is discovered. Invoke it explicitly with `$academic-pdf-to-markdown`, or describe a matching PDF-conversion task.

### Claude Code

Install it as a personal Claude Code skill available across projects:

```bash
git clone https://github.com/luqav/academic-pdf-to-markdown-skill.git \
  "$HOME/.claude/skills/academic-pdf-to-markdown"
cd "$HOME/.claude/skills/academic-pdf-to-markdown"
```

Claude Code can discover the skill from its description or invoke it directly as `/academic-pdf-to-markdown`. A project-local installation can instead live at `.claude/skills/academic-pdf-to-markdown/`. See the official [Claude Code skills documentation](https://code.claude.com/docs/en/skills) for discovery scopes and invocation behavior.

### Install the Python dependency

Whichever location you choose, create an isolated environment inside the cloned repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Python 3.10 or newer is required.

## Use it with an agent

Attach or identify the PDF files and give your agent a concrete request.

Codex example:

```text
Use $academic-pdf-to-markdown to convert these papers into page-anchored
Markdown, run OCR only where necessary, and verify every output bundle.
```

Claude Code example:

```text
/academic-pdf-to-markdown Convert /path/to/papers into /path/to/research-cache.
Use English and German OCR, verify every bundle, and report all warned pages.
```

Generic agent example:

```text
Read SKILL.md in this repository and follow it to convert /path/to/papers.
Keep page anchors, run OCR only where necessary, verify every output, and report
which pages need manual comparison with the original PDF.
```

The portable workflow in [SKILL.md](SKILL.md) tells the agent to run the deterministic scripts, inspect warnings, preserve provenance, and avoid inventing missing content.

## Use the CLI directly

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
