# Runtime setup

## Required

- Python 3.10 or newer
- `pdfplumber` from `requirements.txt`

Git is optional. A source ZIP may be downloaded and extracted instead. The converter supports macOS, Linux, 64-bit Windows, and Windows Subsystem for Linux when the required Python and OCR dependencies are available.

Install the Python dependency in an isolated environment.

macOS, Linux, or WSL with bash/zsh:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks `Activate.ps1`, follow Python's documented [`venv` activation guidance](https://docs.python.org/3/library/venv.html) or use Windows Subsystem for Linux. Do not disable security controls system-wide merely to activate the environment.

Native-text PDFs need no additional system package.

Confirm the runtime:

```bash
python scripts/pdf_to_markdown.py --check
```

Python and `pdfplumber` must show `OK`. OCRmyPDF is optional until a scanned or image-only page requires OCR.

## One-time OCR for scanned pages

Automatic OCR requires OCRmyPDF plus Tesseract and Ghostscript. Install the system package rather than silently switching to model-based vision.

macOS with Homebrew:

```bash
brew install ocrmypdf tesseract-lang
```

Ubuntu or Debian 22.04 or newer:

```bash
sudo apt-get update
sudo apt-get install -y ocrmypdf tesseract-ocr-eng tesseract-ocr-deu
```

Fedora:

```bash
sudo dnf install -y ocrmypdf tesseract-osd
```

Windows Subsystem for Linux with Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y python3-venv ocrmypdf tesseract-ocr-eng tesseract-ocr-deu
```

Native 64-bit Windows:

```powershell
winget install -e --id Python.Python.3.12
winget install -e --id UB-Mannheim.TesseractOCR
```

Install the current 64-bit Ghostscript build from Artifex, reopen PowerShell, activate the virtual environment, and install OCRmyPDF into it:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install ocrmypdf
```

OCRmyPDF checks the Windows registry and standard `Program Files` locations for Tesseract and Ghostscript. Native 32-bit Windows is not supported. See the official [OCRmyPDF installation guide](https://ocrmypdf.readthedocs.io/en/latest/installation.html) for current platform details and other Linux distributions.

Check installed OCR languages:

```bash
tesseract --list-langs
```

Pass a matching language set, for example `--language eng`, `--language deu`, or `--language eng+deu`. OCR quality depends on scan quality, typography, columns, equations, and the installed language data. OCR is a cached extraction step, not proof of correctness.

## Troubleshooting

- If `pdfplumber` is missing, activate the intended environment and install `requirements.txt`.
- If automatic OCR reports that `ocrmypdf` is missing, install it or rerun with `--ocr never` only when incomplete image-only pages are acceptable.
- On Windows, reopen the terminal after installing Tesseract or Ghostscript so registry and `PATH` changes are visible.
- If a PDF is encrypted, create an authorized decrypted working copy outside this skill, then preserve both provenance and access restrictions.
- If OCR fails, keep the native extraction and report the failure. Do not fill gaps with generated text.
