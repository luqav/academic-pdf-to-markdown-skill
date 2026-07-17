# Runtime setup

## Required

- Python 3.10 or newer
- `pdfplumber` from `requirements.txt`

Install the Python dependency in an isolated environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Native-text PDFs need no additional system package.

## One-time OCR for scanned pages

Automatic OCR requires OCRmyPDF plus Tesseract and Ghostscript. Install the system package rather than silently switching to model-based vision.

macOS with Homebrew:

```bash
brew install ocrmypdf tesseract tesseract-lang
```

Ubuntu or Debian:

```bash
sudo apt-get update
sudo apt-get install -y ocrmypdf tesseract-ocr tesseract-ocr-eng tesseract-ocr-deu
```

Check installed OCR languages:

```bash
tesseract --list-langs
```

Pass a matching language set, for example `--language eng`, `--language deu`, or `--language eng+deu`. OCR quality depends on scan quality, typography, columns, equations, and the installed language data. OCR is a cached extraction step, not proof of correctness.

## Troubleshooting

- If `pdfplumber` is missing, activate the intended environment and install `requirements.txt`.
- If automatic OCR reports that `ocrmypdf` is missing, install it or rerun with `--ocr never` only when incomplete image-only pages are acceptable.
- If a PDF is encrypted, create an authorized decrypted working copy outside this skill, then preserve both provenance and access restrictions.
- If OCR fails, keep the native extraction and report the failure. Do not fill gaps with generated text.
