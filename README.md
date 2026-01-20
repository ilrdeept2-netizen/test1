# 특허 문서 변환기 🔄

**Word/HWP 파일 → 한국특허청 HLT 형식 자동 변환**

특허 명세서를 수동으로 복사/붙여넣기 하지 마세요!
파일만 업로드하면 자동으로 HLT로 변환됩니다.

## 📱 모바일에서도 사용 가능!

**설치 없이 바로 사용하기** (모바일/데스크톱 모두 지원)

[![Run on Replit](https://replit.com/badge/github/ilrdeept2-netizen/test1)](https://replit.com/@ilrdeept2-netizen/test1)

👆 **위 버튼 클릭** → Replit에서 Fork → **Run 버튼** 클릭 → 스마트폰/태블릿에서도 사용 가능!

### 🌐 Replit으로 사용하는 방법

1. **위의 "Run on Replit" 버튼 클릭**
2. Replit 계정 로그인 (무료)
3. **Fork** 버튼 클릭하여 자신의 Repl 생성
4. **Run** 버튼 클릭 (또는 자동 실행)
5. 상단에 나타나는 웹뷰에서 바로 사용!
6. 📱 **모바일에서도 접속 가능** - 생성된 URL을 스마트폰에서 열기

**장점:**
- ✅ Python 설치 불필요
- ✅ 스마트폰/태블릿에서 사용 가능
- ✅ 언제 어디서나 접속
- ✅ GitHub에서 바로 실행
- ✅ 자동 의존성 설치

---

## 📥 다운로드 및 설치

### 1️⃣ 파일 다운로드

이 페이지 위쪽의 초록색 **"Code"** 버튼 클릭 → **"Download ZIP"** 클릭

### 2️⃣ 압축 풀기

다운로드한 ZIP 파일을 원하는 폴더에 압축 해제

### 3️⃣ Python 설치 (없는 경우만)

https://www.python.org/downloads/

⚠️ **중요:** 설치할 때 "Add Python to PATH" 체크!

---

## 🚀 실행 방법 (초간단!)

### Windows 사용자

**`실행.bat`** 파일을 **더블클릭!**

### Mac/Linux 사용자

**`EASY_START.py`** 파일을 **더블클릭!**

또는 터미널에서:
```bash
python3 EASY_START.py
```

---

## 💡 사용 방법

1. **실행.bat** 더블클릭
2. 자동으로 브라우저가 열림 (안 열리면 http://127.0.0.1:5000 입력)
3. **Word 파일(.docx)을 드래그 앤 드롭**
4. **HLT 파일 자동 다운로드!**
5. K-Editor에서 열어서 사용하세요

---

## 🎯 주요 기능

- ✅ **Word (.docx) → HLT** 자동 변환
- ✅ **한글 (.hwp) → HLT** 변환 지원
- ✅ **자동 섹션 인식** (발명의 명칭, 기술분야, 청구범위 등)
- ✅ **드래그 앤 드롭** 웹 인터페이스
- ✅ **K-Editor 호환** XML 형식
- ✅ **설치 자동화** - 필요한 프로그램 자동 설치

### 📝 특허 문서 작성 가이드

변환이 제대로 작동하려면 문서에 다음과 같은 섹션 헤더를 사용하세요:

```
【발명의 명칭】
【기술분야】
【발명의 배경이 되는 기술】
【해결하려는 과제】
【과제의 해결 수단】
【발명의 효과】
【도면의 간단한 설명】
【발명을 실시하기 위한 구체적인 내용】
【청구범위】
【요약】
```

### 💡 특허 변환 워크플로우

1. Word 또는 한글로 특허 명세서 초안 작성
2. 웹 인터페이스 또는 CLI로 HLT 변환
3. K-Editor에서 HLT 파일 열기
4. 최종 검토 및 XML 변환 (HLZ)
5. 특허청 전자출원

---

## 📄 PDF to PowerPoint Converter

구글 NotebookLM의 PDF 슬라이드를 편집 가능한 PowerPoint 프레젠테이션으로 변환하는 도구입니다.

Convert Google NotebookLM PDF slides (or any PDF) to editable PowerPoint presentations.

## 🌟 PDF 변환기 주요 기능 (PDF Converter Features)

- ✅ PDF 파일을 편집 가능한 PPT로 변환
- ✅ 고해상도 이미지 품질 지원
- ✅ 슬라이드 비율 자동 조정 (16:9)
- ✅ 간단한 명령줄 인터페이스
- ✅ Convert PDF files to editable PowerPoint
- ✅ High-resolution image quality support
- ✅ Automatic slide ratio adjustment (16:9)
- ✅ Simple command-line interface

## 📋 필요 조건 (Requirements)

### Python
- Python 3.7 이상 (Python 3.7 or higher)

### 시스템 의존성 (System Dependencies)

**macOS:**
```bash
brew install poppler
```

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

**Windows:**
1. Download poppler from: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extract to `C:\Program Files\poppler`
3. Add `C:\Program Files\poppler\Library\bin` to PATH

## 🚀 설치 방법 (Installation)

1. **저장소 클론 (Clone the repository):**
```bash
git clone <repository-url>
cd test1
```

2. **Python 패키지 설치 (Install Python packages):**
```bash
pip install -r requirements.txt
```

또는 가상환경 사용 권장 (Or use virtual environment - recommended):
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 💡 사용 방법 (Usage)

### 기본 사용법 (Basic Usage)

가장 간단한 방법 (Simplest way):
```bash
python pdf_to_ppt.py your_file.pdf
```

이렇게 하면 `your_file.pptx`가 생성됩니다.
This will create `your_file.pptx`.

### 출력 파일명 지정 (Specify Output Filename)

```bash
python pdf_to_ppt.py input.pdf -o my_presentation.pptx
```

### DPI 조정 (Adjust DPI)

더 높은 품질 (Higher quality - larger file, slower):
```bash
python pdf_to_ppt.py input.pdf --dpi 300
```

빠른 변환 (Faster conversion - smaller file):
```bash
python pdf_to_ppt.py input.pdf --dpi 150
```

### 구글 NotebookLM 슬라이드 변환 예시 (Example with Google NotebookLM)

```bash
# NotebookLM에서 다운로드한 PDF를 변환
python pdf_to_ppt.py notebooklm_slides.pdf -o my_editable_slides.pptx --dpi 200

# 변환 완료 후 PowerPoint, Google Slides, LibreOffice 등에서 편집 가능!
```

## 📖 사용 예시 (Examples)

### 예시 1: 기본 변환 (Basic Conversion)
```bash
python pdf_to_ppt.py presentation.pdf
# 결과 (Output): presentation.pptx
```

### 예시 2: 사용자 정의 출력 (Custom Output)
```bash
python pdf_to_ppt.py slides.pdf -o my_slides.pptx
# 결과 (Output): my_slides.pptx
```

### 예시 3: 고품질 변환 (High Quality)
```bash
python pdf_to_ppt.py important_slides.pdf --dpi 400 -o high_quality.pptx
# 고해상도로 변환 (High resolution conversion)
```

### 예시 4: 빠른 변환 (Quick Conversion)
```bash
python pdf_to_ppt.py large_document.pdf --dpi 100
# 빠르게 처리하지만 품질은 낮음 (Fast but lower quality)
```

## 🎯 NotebookLM 슬라이드 편집 워크플로우

### NotebookLM Slide Editing Workflow

1. **NotebookLM에서 슬라이드 덱 생성 및 PDF 다운로드**
   - Create slide deck in NotebookLM and download as PDF

2. **PDF를 PPT로 변환**
   ```bash
   python pdf_to_ppt.py notebooklm_slides.pdf -o editable_slides.pptx
   ```

3. **PowerPoint/Google Slides에서 편집**
   - Edit in PowerPoint/Google Slides
   - 텍스트 추가/수정 (Add/modify text)
   - 이미지 추가 (Add images)
   - 레이아웃 조정 (Adjust layouts)
   - 애니메이션 추가 (Add animations)

4. **최종 프레젠테이션 저장 및 공유**
   - Save and share final presentation

## 🛠️ 고급 사용법 (Advanced Usage)

### Python 코드에서 직접 사용 (Use in Python Code)

```python
from pdf_to_ppt import PDFtoPPTConverter

# 변환기 생성 (Create converter)
converter = PDFtoPPTConverter(
    pdf_path='input.pdf',
    output_path='output.pptx',
    dpi=300
)

# 변환 실행 (Run conversion)
output_file = converter.convert()
print(f"Created: {output_file}")
```

### 배치 처리 (Batch Processing)

여러 PDF 파일을 한 번에 변환 (Convert multiple PDFs at once):

```bash
# Bash/Linux/macOS
for file in *.pdf; do
    python pdf_to_ppt.py "$file"
done
```

```powershell
# Windows PowerShell
Get-ChildItem *.pdf | ForEach-Object {
    python pdf_to_ppt.py $_.Name
}
```

## 🔧 문제 해결 (Troubleshooting)

### "poppler not found" 오류

**해결책 (Solution):**
- macOS: `brew install poppler`
- Ubuntu: `sudo apt-get install poppler-utils`
- Windows: poppler 설치 및 PATH 추가 (Install poppler and add to PATH)

### 변환이 느린 경우 (Slow Conversion)

**해결책 (Solution):**
- DPI를 낮추세요: `--dpi 150` 또는 `--dpi 100`
- Lower DPI: `--dpi 150` or `--dpi 100`

### 메모리 부족 오류 (Out of Memory)

**해결책 (Solution):**
- DPI를 낮추세요 (Lower DPI)
- 큰 PDF를 작은 파일로 나누세요 (Split large PDFs into smaller files)

### 이미지 품질이 낮은 경우 (Low Image Quality)

**해결책 (Solution):**
- DPI를 높이세요: `--dpi 300` 또는 `--dpi 400`
- Increase DPI: `--dpi 300` or `--dpi 400`

## 📝 DPI 가이드 (DPI Guide)

| DPI | 품질 (Quality) | 파일 크기 (File Size) | 속도 (Speed) | 권장 용도 (Recommended Use) |
|-----|---------------|---------------------|-------------|---------------------------|
| 72  | 낮음 (Low)     | 작음 (Small)         | 빠름 (Fast)  | 테스트용 (Testing)         |
| 150 | 보통 (Medium)  | 보통 (Medium)        | 보통 (Medium) | 일반 프레젠테이션 (General) |
| 200 | 좋음 (Good)    | 큰 (Large)           | 느림 (Slow)  | 업무용 (Business)          |
| 300 | 고품질 (High)  | 매우 큰 (Very Large) | 매우 느림 (Very Slow) | 인쇄용 (Print Quality) |
| 400+ | 최고 (Best)   | 거대 (Huge)          | 매우 느림 (Very Slow) | 전문가용 (Professional) |

**권장 (Recommended):** 대부분의 경우 DPI 200-300이면 충분합니다.
For most cases, DPI 200-300 is sufficient.

## 🤝 기여 (Contributing)

이슈나 개선사항이 있으시면 GitHub 이슈를 열어주세요.
Feel free to open GitHub issues for bugs or feature requests.

## 📄 라이선스 (License)

MIT License

## 💬 FAQ

**Q: PowerPoint가 없어도 편집할 수 있나요?**
A: 네! Google Slides, LibreOffice Impress 등에서도 PPTX 파일을 열고 편집할 수 있습니다.

**Q: Can I edit without PowerPoint?**
A: Yes! You can open and edit PPTX files in Google Slides, LibreOffice Impress, etc.

---

**Q: 변환된 슬라이드의 텍스트를 편집할 수 있나요?**
A: 변환된 슬라이드는 이미지로 저장되므로, 기존 텍스트를 직접 편집할 수는 없습니다. 하지만 새로운 텍스트 박스를 추가하거나, 이미지 위에 텍스트를 넣을 수 있습니다.

**Q: Can I edit the text in converted slides?**
A: The converted slides are saved as images, so you can't directly edit existing text. However, you can add new text boxes or overlay text on the images.

---

**Q: 원본 PDF의 품질이 낮으면 어떻게 되나요?**
A: 변환된 PPT의 품질은 원본 PDF의 품질에 의존합니다. 원본이 저화질이면 결과물도 저화질입니다.

**Q: What if the original PDF has low quality?**
A: The converted PPT quality depends on the original PDF quality. Low quality input = low quality output.

---

Made with ❤️ for better presentations
