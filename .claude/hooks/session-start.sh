#!/bin/bash
set -euo pipefail

# 웹(리모트) 환경에서만 실행
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "=== 세션 시작 환경 설정 중 ===" >&2

# Python 의존성 설치 (일부 패키지 빌드 실패 시에도 계속 진행)
if [ -f "$CLAUDE_PROJECT_DIR/requirements.txt" ]; then
  echo "[1/2] Python 패키지 설치 중..." >&2
  # sgmllib3k: Debian 패치 setuptools와 충돌하므로 PEP 517 빌드 격리로 먼저 설치
  # (feedparser가 런타임에 sgmllib 모듈을 필요로 함)
  pip install -q --use-pep517 --root-user-action=ignore sgmllib3k 2>&1 | tail -3 || true
  # blinker: Debian 시스템 패키지(RECORD 파일 없음)로 설치되어 있어 uninstall 실패.
  # --ignore-installed로 우회하지 않으면 이후 flask 등 의존성 설치가 전부 실패함.
  pip install -q --ignore-installed --root-user-action=ignore blinker 2>&1 | tail -3 || true
  pip install -q --root-user-action=ignore -r "$CLAUDE_PROJECT_DIR/requirements.txt" 2>&1 | tail -5 || true
  echo "[1/2] Python 패키지 설치 완료" >&2
fi

# Node.js / npx 확인 (korean-law-mcp 용)
echo "[2/2] Node.js/npx 확인 중..." >&2
if command -v npx &> /dev/null; then
  echo "[2/2] npx 사용 가능: $(npx --version)" >&2
else
  echo "[2/2] 경고: npx를 찾을 수 없습니다. Node.js를 설치해주세요." >&2
fi

echo "=== 환경 설정 완료 ===" >&2
