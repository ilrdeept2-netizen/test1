# CLAUDE.md

Guide for AI assistants working with this repository.

## Project Overview

This is a **Patent Document Tools Suite** (특허 문서 변환기) — a Python-based toolkit for Korean patent document management. It provides:

1. **Patent Format Converter** — Converts Word/HWP/PDF documents to Korean Patent Office (KIPO) HLT XML format
2. **Prior Art Patent Search** — Searches KIPRIS database for similar patents based on uploaded documents
3. **AI News Digest** — Collects and summarizes daily AI/LLM news from major company feeds
4. **PDF to PowerPoint Converter** — Converts PDF slides into PowerPoint presentations

## Repository Structure

```
├── app.py                         # Flask web server for converter (port 5000)
├── patent_format_converter.py     # Core: Word/HWP/PDF -> HLT conversion engine
├── patent_search_app.py           # Core: Prior art search engine (KIPRIS)
├── patent_search_web.py           # Streamlit web UI for patent search
├── ai_news_digest.py              # RSS-based AI news collector
├── pdf_to_ppt.py                  # PDF -> PowerPoint converter
├── EASY_START.py                  # All-in-one launcher (auto-installs deps)
├── start_converter.py             # Converter launcher with dep check
├── start_patent_search.py         # Patent search launcher
├── example.py                     # Usage examples for PDF converter
├── templates/
│   └── index.html                 # Drag-and-drop web UI for converter
├── .github/workflows/
│   └── ai_news_digest.yml         # Daily news collection (cron: UTC 23:00)
├── requirements.txt               # Python dependencies
├── test_patent_converter.py       # Tests for patent format converter
├── test_patent_search.py          # Tests for patent search app
├── test_converter.py              # Tests for PDF converter
├── test_patent.docx               # Test fixture: sample Word document
├── test_patent.hlt                # Test fixture: sample HLT file
└── *.bat / *.sh                   # Platform-specific launchers
```

## Tech Stack

- **Language:** Python 3.7+ (3.11 recommended)
- **Web Frameworks:** Flask (converter UI), Streamlit (patent search UI)
- **Key Libraries:** python-docx, olefile, PyPDF2, lxml, pdf2image, python-pptx, Pillow, feedparser, beautifulsoup4
- **CI/CD:** GitHub Actions (daily news digest)

## Development Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# System dependency for PDF conversion (pdf2image requires poppler)
# macOS: brew install poppler
# Ubuntu/Debian: sudo apt-get install poppler-utils
```

## Running the Applications

```bash
# Patent converter web UI (Flask, port 5000)
python3 app.py

# Patent search web UI (Streamlit)
python3 patent_search_web.py
# or: streamlit run patent_search_web.py

# AI news digest (CLI)
python3 ai_news_digest.py --days 1 --save --output .

# PDF to PowerPoint
python3 pdf_to_ppt.py input.pdf -o output.pptx --dpi 200

# All-in-one launcher (auto-installs deps)
python3 EASY_START.py
```

## Running Tests

Tests use custom test functions (not pytest/unittest runners). Run each directly:

```bash
python3 test_patent_converter.py    # Patent format converter tests
python3 test_patent_search.py       # Patent search app tests
python3 test_converter.py           # PDF converter tests
```

Exit code 0 = all passed, 1 = failures. Test output is in Korean with `[PASS]`/`[FAIL]` markers.

## Key Architecture Details

### Patent Format Converter (`patent_format_converter.py`)
- `PatentFormatConverter` — Main class: orchestrates reading input and generating HLT
- `WordReader` — Reads .docx files into paragraph lists
- `detect_section(text)` — Identifies Korean patent section headers (e.g., `【발명의 명칭】`)
- `parse_claims(lines)` — Parses patent claims from various numbering formats
- `HLTGenerator` — Generates KIPO-standard XML (HLT) output
- `SECTION_DEFINITIONS` — Dict mapping section IDs to Korean header patterns

### Patent Search (`patent_search_app.py`)
- `TextExtractor` — Extracts text from multiple file formats (.docx, .hwp, .pdf, .pptx, .xlsx, .txt)
- `KeywordExtractor` — Extracts search keywords from document text
- `KIPRISSearcher` — Queries KIPRIS API for similar patents
- `SimilarityAnalyzer` — Compares document similarity
- `PatentSearchApp` — Orchestrates the full search workflow

### Web Server (`app.py`)
- Flask app with routes: `/` (UI), `/convert` (POST file upload), `/api/status`, `/health`
- Accepts .docx, .hwp, .pdf uploads (50MB limit)
- Returns converted .hlt file as download

## Code Conventions

- **Language:** Code comments and UI text are primarily in Korean; function/variable names use English
- **Style:** PEP 8 conventions (no formal linter configured)
- **No formal formatter:** No .flake8, .pylintrc, or pyproject.toml configured
- **Encoding:** Files use UTF-8 with `# -*- coding: utf-8 -*-` headers
- **Imports:** Standard library first, then third-party, then local modules
- **Error handling:** Try/except with Korean error messages printed to console

## CI/CD

The only automated workflow is `.github/workflows/ai_news_digest.yml`:
- **Schedule:** Daily at UTC 23:00 (KST 08:00)
- **What it does:** Runs `ai_news_digest.py`, uploads digest as artifact, creates a GitHub issue with the summary
- **Manual trigger:** Supports `workflow_dispatch`

## Important Notes

- `pyhwpx` (HWP reading) is disabled in requirements.txt — it only works on Windows
- `konlpy` (Korean NLP) is optional and requires Java runtime
- The `.gitignore` excludes `test_*.pdf`, `test_*.pptx`, and `*.pptx` output files
- Test fixture files (`test_patent.docx`, `test_patent.hlt`) are committed to the repo
- Windows batch files (`.bat`) use Korean filenames with EUC-KR encoding
