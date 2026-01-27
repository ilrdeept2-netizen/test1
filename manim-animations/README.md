# Manim 수학 애니메이션

3Blue1Brown 스타일의 고품질 수학 애니메이션을 만들 수 있는 예제 프로젝트입니다.

## 빠른 시작

### 1단계: 시스템 의존성 설치

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y ffmpeg libcairo2-dev libpango1.0-dev python3-pip python3-venv
# LaTeX (선택사항 - 수학 수식에 필요)
sudo apt install -y texlive texlive-latex-extra
```

**macOS:**
```bash
brew install ffmpeg cairo pango
# LaTeX (선택사항)
brew install --cask mactex-no-gui
```

**Windows:**
- FFmpeg: https://ffmpeg.org/download.html 에서 다운로드
- MiKTeX (LaTeX): https://miktex.org/download 에서 다운로드
- 환경 변수 PATH에 추가 필요

### 2단계: Manim 설치

```bash
# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Manim 설치
pip install manim

# 설치 확인
manim --version
```

또는 자동 설치 스크립트 사용:
```bash
chmod +x setup.sh
./setup.sh
```

### 3단계: 애니메이션 렌더링

```bash
# 가상환경 활성화
source venv/bin/activate

# 예제 실행 (저화질 미리보기)
manim -pql scenes.py BasicShapes
```

## 포함된 예제

| 씬 이름 | 설명 | 실행 명령 |
|---------|------|----------|
| `BasicShapes` | 기본 도형 생성 및 변환 | `manim -pql scenes.py BasicShapes` |
| `PythagoreanTheorem` | 피타고라스 정리 시각화 | `manim -pql scenes.py PythagoreanTheorem` |
| `DerivativeVisualization` | 함수의 미분과 접선 | `manim -pql scenes.py DerivativeVisualization` |
| `FourierSeries` | 푸리에 급수로 사각파 근사 | `manim -pql scenes.py FourierSeries` |
| `Surface3D` | 3D 표면 그래프 | `manim -pql scenes.py Surface3D` |
| `NeuralNetwork` | 뉴럴 네트워크 구조 | `manim -pql scenes.py NeuralNetwork` |
| `BubbleSort` | 버블 정렬 알고리즘 | `manim -pql scenes.py BubbleSort` |
| `EulerFormula` | 오일러 공식 e^(iπ)+1=0 | `manim -pql scenes.py EulerFormula` |

## 품질 옵션

```bash
manim -pql scenes.py SceneName  # 저화질 (480p, 15fps) - 빠른 미리보기
manim -pqm scenes.py SceneName  # 중간 화질 (720p, 30fps)
manim -pqh scenes.py SceneName  # 고화질 (1080p, 60fps)
manim -pqk scenes.py SceneName  # 4K 화질 (2160p, 60fps)
```

**플래그 설명:**
- `-p`: 렌더링 후 자동으로 미리보기
- `-q`: 품질 수준 (l/m/h/k)
- `-a`: 파일 내 모든 씬 렌더링

## 출력 파일

렌더링된 비디오는 `media/videos/` 폴더에 저장됩니다:
```
media/
└── videos/
    └── scenes/
        ├── 480p15/    # 저화질
        ├── 720p30/    # 중간 화질
        ├── 1080p60/   # 고화질
        └── 2160p60/   # 4K
```

## 나만의 씬 만들기

```python
from manim import *

class MyScene(Scene):
    def construct(self):
        # 텍스트 생성
        text = Text("Hello, Manim!")

        # 수학 수식
        formula = MathTex(r"\int_0^1 x^2 dx = \frac{1}{3}")
        formula.next_to(text, DOWN)

        # 애니메이션
        self.play(Write(text))
        self.play(FadeIn(formula))
        self.wait()
```

## 유용한 리소스

- [Manim Community 공식 문서](https://docs.manim.community/)
- [Manim 예제 갤러리](https://docs.manim.community/en/stable/examples.html)
- [3Blue1Brown 채널](https://www.youtube.com/@3blue1brown)
- [manim_skill GitHub](https://github.com/adithya-s-k/manim_skill)

## 문제 해결

**"command not found: manim"**
```bash
# 가상환경 활성화 확인
source venv/bin/activate
# 또는 전체 경로 사용
python -m manim --version
```

**LaTeX 오류**
```bash
# 최소 LaTeX 패키지 설치
sudo apt install texlive-latex-recommended texlive-fonts-recommended
```

**FFmpeg 오류**
```bash
# FFmpeg 설치 확인
ffmpeg -version
```
