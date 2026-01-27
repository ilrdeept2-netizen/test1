#!/bin/bash

# =============================================
# Manim 설치 스크립트
# 3Blue1Brown 스타일 수학 애니메이션 제작
# =============================================

set -e

echo "=========================================="
echo " Manim 애니메이션 환경 설정"
echo "=========================================="

# OS 감지
OS="$(uname -s)"

install_dependencies() {
    echo ""
    echo "[1/3] 시스템 의존성 설치 중..."

    case "$OS" in
        Linux*)
            if command -v apt-get &> /dev/null; then
                # Ubuntu/Debian
                sudo apt update
                sudo apt install -y \
                    ffmpeg \
                    libcairo2-dev \
                    libpango1.0-dev \
                    texlive-full \
                    python3-pip \
                    python3-venv
            elif command -v dnf &> /dev/null; then
                # Fedora
                sudo dnf install -y \
                    ffmpeg \
                    cairo-devel \
                    pango-devel \
                    texlive-scheme-full \
                    python3-pip
            elif command -v pacman &> /dev/null; then
                # Arch Linux
                sudo pacman -S --noconfirm \
                    ffmpeg \
                    cairo \
                    pango \
                    texlive-most \
                    python-pip
            fi
            ;;
        Darwin*)
            # macOS
            if ! command -v brew &> /dev/null; then
                echo "Homebrew가 필요합니다. 설치 중..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install ffmpeg cairo pango
            # LaTeX (선택사항 - 용량이 큼)
            echo "LaTeX 설치는 선택사항입니다. 필요시: brew install --cask mactex"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            # Windows (Git Bash 등)
            echo "Windows에서는 수동 설치가 필요합니다:"
            echo "1. FFmpeg: https://ffmpeg.org/download.html"
            echo "2. MiKTeX (LaTeX): https://miktex.org/download"
            echo "설치 후 PATH에 추가하세요."
            ;;
    esac
}

create_venv() {
    echo ""
    echo "[2/3] Python 가상환경 생성 중..."

    if [ -d "venv" ]; then
        echo "기존 venv 발견, 삭제 중..."
        rm -rf venv
    fi

    python3 -m venv venv

    # 가상환경 활성화
    source venv/bin/activate
}

install_manim() {
    echo ""
    echo "[3/3] Manim 설치 중..."

    pip install --upgrade pip
    pip install manim

    # 설치 확인
    echo ""
    echo "설치 확인..."
    manim --version
}

print_usage() {
    echo ""
    echo "=========================================="
    echo " 설치 완료!"
    echo "=========================================="
    echo ""
    echo "사용 방법:"
    echo ""
    echo "1. 가상환경 활성화:"
    echo "   source venv/bin/activate"
    echo ""
    echo "2. 애니메이션 렌더링:"
    echo "   manim -pql scenes.py BasicShapes          # 기본 도형"
    echo "   manim -pql scenes.py PythagoreanTheorem   # 피타고라스 정리"
    echo "   manim -pql scenes.py DerivativeVisualization  # 미분"
    echo "   manim -pql scenes.py FourierSeries        # 푸리에 급수"
    echo "   manim -pql scenes.py Surface3D            # 3D 표면"
    echo "   manim -pql scenes.py NeuralNetwork        # 뉴럴 네트워크"
    echo "   manim -pql scenes.py BubbleSort           # 버블 정렬"
    echo "   manim -pql scenes.py EulerFormula         # 오일러 공식"
    echo ""
    echo "품질 옵션:"
    echo "   -ql  저화질 (빠른 미리보기)"
    echo "   -qm  중간 화질"
    echo "   -qh  고화질 (1080p)"
    echo "   -qk  4K 화질"
    echo ""
    echo "출력 파일 위치: media/videos/"
    echo ""
}

# 메인 실행
main() {
    install_dependencies
    create_venv
    install_manim
    print_usage
}

# 빠른 설치 (의존성 제외)
quick_install() {
    echo "빠른 설치 모드 (시스템 의존성은 이미 설치되어 있다고 가정)"
    create_venv
    install_manim
    print_usage
}

# 인자 확인
if [ "$1" == "--quick" ]; then
    quick_install
else
    main
fi
