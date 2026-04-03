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
  pip install -q -r "$CLAUDE_PROJECT_DIR/requirements.txt" 2>&1 | tail -5 || true
  echo "[1/2] Python 패키지 설치 완료 (일부 선택적 패키지 제외 가능)" >&2
fi

# Node.js / npx 확인 (korean-law-mcp 용)
echo "[2/2] Node.js/npx 확인 중..." >&2
if command -v npx &> /dev/null; then
  echo "[2/2] npx 사용 가능: $(npx --version)" >&2
else
  echo "[2/2] 경고: npx를 찾을 수 없습니다. Node.js를 설치해주세요." >&2
fi

echo "=== 환경 설정 완료 ===" >&2
