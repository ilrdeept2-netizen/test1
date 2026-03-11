#!/bin/bash
# ============================================================
# Claude Desktop Guardian - macOS 영구적 크래시 방지 시스템
# ============================================================
#
# Claude Desktop 앱이 반복적으로 크래시되는 문제를 근본적으로 해결합니다.
# launchd를 통해 시스템 시작 시 자동으로 안정성을 보장하고,
# 크래시 발생 시 자동으로 안전 모드로 재시작합니다.
#
# 사용법:
#   chmod +x claude_desktop_guardian.sh
#   ./claude_desktop_guardian.sh install    # Guardian 설치 (launchd 등록)
#   ./claude_desktop_guardian.sh protect    # 설정 보호 1회 실행
#   ./claude_desktop_guardian.sh watch      # 수동 감시 시작
#   ./claude_desktop_guardian.sh uninstall  # Guardian 제거
#   ./claude_desktop_guardian.sh status     # 상태 확인
#
# ============================================================

set -euo pipefail

GUARDIAN_VERSION="2.0.0"
GUARDIAN_NAME="com.claude.desktop.guardian"

# 경로 설정
CLAUDE_APP="/Applications/Claude.app"
CLAUDE_SUPPORT_DIR="$HOME/Library/Application Support/Claude"
CLAUDE_LOGS_DIR="$HOME/Library/Logs/Claude"
GUARDIAN_LOG_DIR="$CLAUDE_SUPPORT_DIR/guardian_logs"
GUARDIAN_CONFIG="$CLAUDE_SUPPORT_DIR/guardian_config.json"
CRASH_HISTORY="$CLAUDE_SUPPORT_DIR/guardian_crash_history.json"
PLIST_PATH="$HOME/Library/LaunchAgents/${GUARDIAN_NAME}.plist"
PLIST_WATCH_PATH="$HOME/Library/LaunchAgents/${GUARDIAN_NAME}.watch.plist"

# 캐시 디렉토리
CACHE_DIRS=(
    "$CLAUDE_SUPPORT_DIR/Cache"
    "$CLAUDE_SUPPORT_DIR/GPUCache"
    "$CLAUDE_SUPPORT_DIR/Code Cache"
    "$CLAUDE_SUPPORT_DIR/DawnCache"
    "$CLAUDE_SUPPORT_DIR/DawnGraphiteCache"
    "$CLAUDE_SUPPORT_DIR/blob_storage"
    "$CLAUDE_SUPPORT_DIR/Service Worker"
)

# GPU 안정화 Electron 플래그
GPU_FLAGS=(
    "--disable-gpu"
    "--disable-gpu-compositing"
    "--disable-gpu-sandbox"
    "--disable-software-rasterizer"
    "--in-process-gpu"
)

# 색상 (터미널 출력용)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ── 유틸리티 함수 ──

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    # 로그 디렉토리 생성
    mkdir -p "$GUARDIAN_LOG_DIR"

    local log_file="$GUARDIAN_LOG_DIR/guardian_$(date +%Y%m%d).log"
    echo "[$timestamp] [$level] $message" >> "$log_file"

    # 터미널 출력 (SILENT 모드가 아닌 경우)
    if [ "${SILENT:-0}" != "1" ]; then
        case "$level" in
            INFO)  echo -e "  ${GRAY}[$level] $message${NC}" ;;
            OK)    echo -e "  ${GREEN}[$level] $message${NC}" ;;
            WARN)  echo -e "  ${YELLOW}[$level] $message${NC}" ;;
            ERROR) echo -e "  ${RED}[$level] $message${NC}" ;;
            FIX)   echo -e "  ${MAGENTA}[$level] $message${NC}" ;;
        esac
    fi
}

banner() {
    if [ "${SILENT:-0}" = "1" ]; then return; fi
    echo ""
    echo -e "  ${CYAN}========================================================${NC}"
    echo -e "   ${NC}Claude Desktop Guardian v${GUARDIAN_VERSION} (macOS)${NC}"
    echo -e "   ${GRAY}영구적 크래시 방지 및 자동 복구 시스템${NC}"
    echo -e "  ${CYAN}========================================================${NC}"
    echo ""
}

# JSON 간이 파서/생성 (jq 없이도 동작)
get_json_value() {
    local file="$1"
    local key="$2"
    if [ -f "$file" ]; then
        python3 -c "
import json, sys
try:
    with open('$file') as f:
        data = json.load(f)
    print(data.get('$key', ''))
except:
    print('')
" 2>/dev/null
    fi
}

set_json_value() {
    local file="$1"
    local key="$2"
    local value="$3"
    python3 -c "
import json, os
data = {}
if os.path.exists('$file'):
    try:
        with open('$file') as f:
            data = json.load(f)
    except:
        pass
data['$key'] = $value
with open('$file', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null
}

get_crash_count() {
    if [ -f "$CRASH_HISTORY" ]; then
        python3 -c "
import json
try:
    with open('$CRASH_HISTORY') as f:
        data = json.load(f)
    print(data.get('totalCrashes', 0))
except:
    print(0)
" 2>/dev/null
    else
        echo "0"
    fi
}

record_crash() {
    python3 -c "
import json, os
from datetime import datetime

file = '$CRASH_HISTORY'
data = {'crashes': [], 'totalCrashes': 0, 'lastReset': datetime.now().isoformat()}

if os.path.exists(file):
    try:
        with open(file) as f:
            data = json.load(f)
    except:
        pass

crash = {
    'timestamp': datetime.now().isoformat(),
    'consecutiveCount': $1
}

if not isinstance(data.get('crashes'), list):
    data['crashes'] = []

data['crashes'].append(crash)
data['crashes'] = data['crashes'][-100:]  # 최근 100건만
data['totalCrashes'] = data.get('totalCrashes', 0) + 1

with open(file, 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null
}

reset_crash_history() {
    python3 -c "
import json
from datetime import datetime

data = {
    'crashes': [],
    'totalCrashes': 0,
    'lastReset': datetime.now().isoformat(),
    'guardianVersion': '$GUARDIAN_VERSION'
}

with open('$CRASH_HISTORY', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null
}

# ══════════════════════════════════════════════════════════════
# 핵심 기능 1: 안정성 설정 보호
# ══════════════════════════════════════════════════════════════
protect_settings() {
    log "INFO" "안정성 설정 보호 점검 시작"
    local fix_count=0

    # 1. 설정 디렉토리 확인
    mkdir -p "$CLAUDE_SUPPORT_DIR"

    # 2. GPU 플래그 확인
    local need_gpu_flags=0
    local force_gpu
    force_gpu=$(get_json_value "$GUARDIAN_CONFIG" "forceDisableGpu")
    local crash_count
    crash_count=$(get_crash_count)

    if [ "$force_gpu" = "True" ] || [ "$force_gpu" = "true" ]; then
        need_gpu_flags=1
    fi

    if [ "$crash_count" -ge 2 ] 2>/dev/null; then
        need_gpu_flags=1
        log "WARN" "크래시 이력 ${crash_count}회 - GPU 비활성화 강제 적용"
    fi

    if [ "$need_gpu_flags" = "1" ]; then
        local flags_file="$CLAUDE_SUPPORT_DIR/electron-flags.conf"
        local expected_flags
        expected_flags=$(printf '%s\n' "${GPU_FLAGS[@]}")
        local current_flags=""

        if [ -f "$flags_file" ]; then
            current_flags=$(cat "$flags_file" 2>/dev/null || echo "")
        fi

        if [ "$(echo "$current_flags" | tr -d '[:space:]')" != "$(echo "$expected_flags" | tr -d '[:space:]')" ]; then
            printf '%s\n' "${GPU_FLAGS[@]}" > "$flags_file"
            log "FIX" "GPU 안정화 플래그 복구"
            fix_count=$((fix_count + 1))
        else
            log "OK" "GPU 안정화 플래그 정상"
        fi
    fi

    # 3. Session Storage 손상 감지
    local session_dir="$CLAUDE_SUPPORT_DIR/Session Storage"
    if [ -d "$session_dir" ]; then
        local corrupt_count
        corrupt_count=$(find "$session_dir" -type f -empty 2>/dev/null | wc -l | tr -d ' ')
        if [ "$corrupt_count" -gt 0 ]; then
            rm -rf "$session_dir"
            log "FIX" "손상된 Session Storage 삭제 (${corrupt_count}개 빈 파일)"
            fix_count=$((fix_count + 1))
        fi
    fi

    # 4. Local Storage 손상 감지
    local local_dir="$CLAUDE_SUPPORT_DIR/Local Storage"
    if [ -d "$local_dir" ]; then
        local corrupt_ldb
        corrupt_ldb=$(find "$local_dir" -name "*.ldb" -empty 2>/dev/null | wc -l | tr -d ' ')
        if [ "$corrupt_ldb" -gt 0 ]; then
            rm -rf "$local_dir"
            log "FIX" "손상된 Local Storage 삭제 (${corrupt_ldb}개 빈 파일)"
            fix_count=$((fix_count + 1))
        fi
    fi

    # 5. GPUCache 크기 이상 감지
    local gpu_cache="$CLAUDE_SUPPORT_DIR/GPUCache"
    if [ -d "$gpu_cache" ]; then
        local gpu_cache_size
        gpu_cache_size=$(du -sm "$gpu_cache" 2>/dev/null | awk '{print $1}')
        if [ "${gpu_cache_size:-0}" -gt 500 ] 2>/dev/null; then
            rm -rf "$gpu_cache"
            log "FIX" "비정상적으로 큰 GPUCache 삭제 (${gpu_cache_size}MB)"
            fix_count=$((fix_count + 1))
        fi
    fi

    # 6. claude_desktop_config.json 무결성
    local config_file="$CLAUDE_SUPPORT_DIR/claude_desktop_config.json"
    if [ -f "$config_file" ]; then
        if ! python3 -c "import json; json.load(open('$config_file'))" 2>/dev/null; then
            local backup="${config_file}.bak.$(date +%Y%m%d-%H%M%S)"
            cp "$config_file" "$backup" 2>/dev/null || true
            echo '{"allowAutoUpdate": true}' > "$config_file"
            log "FIX" "손상된 설정 파일 백업 후 재생성"
            fix_count=$((fix_count + 1))
        else
            log "OK" "설정 파일 정상"
        fi
    fi

    if [ "$fix_count" -gt 0 ]; then
        log "OK" "총 ${fix_count}건 설정 복구 완료"
    else
        log "OK" "모든 안정성 설정 정상"
    fi

    return "$fix_count"
}

# ══════════════════════════════════════════════════════════════
# 핵심 기능 2: 프로세스 감시 및 자동 복구
# ══════════════════════════════════════════════════════════════
watch_process() {
    log "INFO" "Claude Desktop 프로세스 감시 시작"

    if [ ! -d "$CLAUDE_APP" ]; then
        log "ERROR" "Claude Desktop 앱을 찾을 수 없습니다: $CLAUDE_APP"
        return 1
    fi

    local max_crashes_gpu=2
    local max_crashes_cache=3
    local max_crashes_full=5
    local watch_interval=10
    local consecutive_crashes=0
    local was_running=0
    local last_pid=0

    while true; do
        local claude_pid
        claude_pid=$(pgrep -f "Claude.app/Contents/MacOS/Claude" 2>/dev/null | head -1 || echo "")

        if [ -n "$claude_pid" ]; then
            # Claude 실행 중
            if [ "$was_running" = "0" ]; then
                log "OK" "Claude Desktop 실행 감지 (PID: $claude_pid)"
                consecutive_crashes=0
            fi
            was_running=1
            last_pid="$claude_pid"

            # 메모리 사용량 모니터링
            local mem_mb
            mem_mb=$(ps -o rss= -p "$claude_pid" 2>/dev/null | awk '{print int($1/1024)}' || echo "0")
            if [ "${mem_mb:-0}" -gt 2000 ] 2>/dev/null; then
                log "WARN" "Claude Desktop 메모리 사용량 과다: ${mem_mb}MB"
            fi
        else
            # Claude가 실행되지 않음
            if [ "$was_running" = "1" ]; then
                consecutive_crashes=$((consecutive_crashes + 1))
                log "ERROR" "Claude Desktop 크래시 감지! (연속 ${consecutive_crashes}회, 이전 PID: $last_pid)"

                record_crash "$consecutive_crashes"

                # 적응형 복구
                if [ "$consecutive_crashes" -ge "$max_crashes_full" ]; then
                    log "FIX" "연속 크래시 ${consecutive_crashes}회 - 전체 캐시 초기화 후 재시작"
                    sleep 3
                    clear_all_cache
                    protect_settings
                    sleep 2
                    start_claude_safe

                elif [ "$consecutive_crashes" -ge "$max_crashes_cache" ]; then
                    log "FIX" "연속 크래시 ${consecutive_crashes}회 - 캐시 정리 후 재시작"
                    sleep 3
                    clear_problematic_cache
                    protect_settings
                    sleep 2
                    start_claude_safe

                elif [ "$consecutive_crashes" -ge "$max_crashes_gpu" ]; then
                    log "FIX" "연속 크래시 ${consecutive_crashes}회 - GPU 비활성화 후 재시작"
                    set_json_value "$GUARDIAN_CONFIG" "forceDisableGpu" "True"
                    protect_settings
                    sleep 2
                    start_claude_safe

                else
                    log "FIX" "크래시 후 안전 모드 재시작 시도"
                    sleep 5
                    start_claude_safe
                fi
            fi
            was_running=0
        fi

        sleep "$watch_interval"
    done
}

start_claude_safe() {
    if [ ! -d "$CLAUDE_APP" ]; then
        log "ERROR" "Claude Desktop 앱을 찾을 수 없습니다"
        return 1
    fi

    local args=()
    local force_gpu
    force_gpu=$(get_json_value "$GUARDIAN_CONFIG" "forceDisableGpu")
    local crash_count
    crash_count=$(get_crash_count)

    if [ "$force_gpu" = "True" ] || [ "$force_gpu" = "true" ] || [ "${crash_count:-0}" -ge 2 ] 2>/dev/null; then
        args+=("--disable-gpu" "--disable-gpu-compositing" "--disable-gpu-sandbox" "--in-process-gpu")
    fi

    log "INFO" "Claude Desktop 시작: ${args[*]:-기본 모드}"

    if [ ${#args[@]} -gt 0 ]; then
        open -a "Claude" --args "${args[@]}" 2>/dev/null
    else
        open -a "Claude" 2>/dev/null
    fi

    if [ $? -eq 0 ]; then
        log "OK" "Claude Desktop 시작 성공"
    else
        log "ERROR" "Claude Desktop 시작 실패"
    fi
}

clear_problematic_cache() {
    log "INFO" "문제 가능성 있는 캐시 정리 중..."

    # Claude 프로세스 종료
    pkill -f "Claude.app/Contents/MacOS/Claude" 2>/dev/null || true
    sleep 2

    local problematic=(
        "$CLAUDE_SUPPORT_DIR/GPUCache"
        "$CLAUDE_SUPPORT_DIR/DawnCache"
        "$CLAUDE_SUPPORT_DIR/DawnGraphiteCache"
        "$CLAUDE_SUPPORT_DIR/Code Cache"
    )

    for dir in "${problematic[@]}"; do
        if [ -d "$dir" ]; then
            rm -rf "$dir"
            log "FIX" "삭제: $dir"
        fi
    done
}

clear_all_cache() {
    log "INFO" "전체 캐시 초기화 중..."

    pkill -f "Claude.app/Contents/MacOS/Claude" 2>/dev/null || true
    sleep 3

    for dir in "${CACHE_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            local size_mb
            size_mb=$(du -sm "$dir" 2>/dev/null | awk '{print $1}')
            rm -rf "$dir"
            log "FIX" "삭제: $(basename "$dir") (${size_mb:-0}MB)"
        fi
    done

    # Session/Local Storage
    rm -rf "$CLAUDE_SUPPORT_DIR/Session Storage" 2>/dev/null
    rm -rf "$CLAUDE_SUPPORT_DIR/Local Storage" 2>/dev/null
    log "FIX" "Session/Local Storage 삭제 (재로그인 필요)"
}

# ══════════════════════════════════════════════════════════════
# 핵심 기능 3: launchd 등록 (영구화)
# ══════════════════════════════════════════════════════════════
install_guardian() {
    log "INFO" "Guardian 설치 시작 (macOS)"

    local script_path
    script_path="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"

    # Guardian 설정 생성
    python3 -c "
import json
from datetime import datetime
data = {
    'version': '$GUARDIAN_VERSION',
    'installedAt': datetime.now().isoformat(),
    'scriptPath': '$script_path',
    'forceDisableGpu': False,
    'autoWatch': True
}
with open('$GUARDIAN_CONFIG', 'w') as f:
    json.dump(data, f, indent=2)
"

    # 기존 크래시 이력 확인
    local crash_count
    crash_count=$(get_crash_count)
    if [ "${crash_count:-0}" -ge 2 ] 2>/dev/null; then
        set_json_value "$GUARDIAN_CONFIG" "forceDisableGpu" "True"
        log "WARN" "기존 크래시 이력 존재 - GPU 비활성화 유지"
    fi

    # launchd plist 생성 - 설정 보호 (로그인 시)
    mkdir -p "$HOME/Library/LaunchAgents"

    cat > "$PLIST_PATH" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${GUARDIAN_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${script_path}</string>
        <string>protect</string>
        <string>--silent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${GUARDIAN_LOG_DIR}/launchd_protect.log</string>
    <key>StandardErrorPath</key>
    <string>${GUARDIAN_LOG_DIR}/launchd_protect_error.log</string>
</dict>
</plist>
PLIST_EOF

    log "OK" "launchd 설정 보호 에이전트 생성: $PLIST_PATH"

    # launchd plist 생성 - 프로세스 감시
    cat > "$PLIST_WATCH_PATH" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${GUARDIAN_NAME}.watch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${script_path}</string>
        <string>watch</string>
        <string>--silent</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>ThrottleInterval</key>
    <integer>300</integer>
    <key>StandardOutPath</key>
    <string>${GUARDIAN_LOG_DIR}/launchd_watch.log</string>
    <key>StandardErrorPath</key>
    <string>${GUARDIAN_LOG_DIR}/launchd_watch_error.log</string>
</dict>
</plist>
PLIST_EOF

    log "OK" "launchd 감시 에이전트 생성: $PLIST_WATCH_PATH"

    # launchd에 로드
    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl unload "$PLIST_WATCH_PATH" 2>/dev/null || true
    launchctl load "$PLIST_PATH" 2>/dev/null
    launchctl load "$PLIST_WATCH_PATH" 2>/dev/null

    log "OK" "launchd 에이전트 로드 완료"

    # 최초 설정 보호 실행
    protect_settings

    # 크래시 이력 초기화
    reset_crash_history

    # 안정 실행 앱 생성 (Automator 스크립트)
    create_stable_launcher

    echo ""
    log "OK" "============================================"
    log "OK" "Guardian 설치 완료!"
    log "OK" "============================================"
    log "INFO" "- 로그인 시 자동으로 안정성 설정이 적용됩니다"
    log "INFO" "- Claude 크래시 시 자동으로 안전 모드 재시작됩니다"
    log "INFO" "- 앱 업데이트 후 설정 리셋도 자동 복구됩니다"
    log "INFO" "- 로그: $GUARDIAN_LOG_DIR"
    log "INFO" "- 제거: $0 uninstall"
    log "OK" "============================================"
}

uninstall_guardian() {
    log "INFO" "Guardian 제거 시작"

    launchctl unload "$PLIST_PATH" 2>/dev/null || true
    launchctl unload "$PLIST_WATCH_PATH" 2>/dev/null || true
    rm -f "$PLIST_PATH" "$PLIST_WATCH_PATH"
    log "OK" "launchd 에이전트 제거 완료"

    # 안정 실행 스크립트 제거
    rm -f "$HOME/Desktop/Claude_안정실행.command" 2>/dev/null || true
    log "OK" "안정 실행 스크립트 제거"

    log "OK" "Guardian 제거 완료 (로그 및 기록은 보존됨)"
    log "INFO" "로그/기록도 삭제: rm -rf '$GUARDIAN_LOG_DIR'"
}

create_stable_launcher() {
    local launcher="$HOME/Desktop/Claude_안정실행.command"
    cat > "$launcher" << 'LAUNCHER_EOF'
#!/bin/bash
echo "============================================"
echo " Claude Desktop 안정 실행 모드"
echo " (Guardian Protected)"
echo "============================================"
echo ""

# 기존 프로세스 정리
pkill -f "Claude.app/Contents/MacOS/Claude" 2>/dev/null || true
sleep 2

echo "[1/3] 기존 프로세스 정리 완료"
echo "[2/3] GPU 하드웨어 가속 비활성화 모드"
echo "[3/3] Claude Desktop 시작 중..."
echo ""

open -a "Claude" --args --disable-gpu --disable-gpu-compositing --disable-gpu-sandbox --in-process-gpu

echo "Claude Desktop이 시작되었습니다."
sleep 3
LAUNCHER_EOF

    chmod +x "$launcher"
    log "OK" "안정 실행 스크립트 생성: $launcher"
}

show_status() {
    banner

    echo -e "  ${CYAN}상태 정보:${NC}"
    echo ""

    # Guardian 설치 확인
    if [ -f "$PLIST_PATH" ]; then
        echo -e "  Guardian 설치: ${GREEN}설치됨${NC}"
        if launchctl list | grep -q "$GUARDIAN_NAME" 2>/dev/null; then
            echo -e "  설정 보호 서비스: ${GREEN}실행 중${NC}"
        else
            echo -e "  설정 보호 서비스: ${YELLOW}중지됨${NC}"
        fi
    else
        echo -e "  Guardian 설치: ${RED}미설치${NC}"
    fi

    if [ -f "$PLIST_WATCH_PATH" ]; then
        if launchctl list | grep -q "${GUARDIAN_NAME}.watch" 2>/dev/null; then
            echo -e "  프로세스 감시: ${GREEN}실행 중${NC}"
        else
            echo -e "  프로세스 감시: ${YELLOW}중지됨${NC}"
        fi
    fi

    # 크래시 이력
    local crash_count
    crash_count=$(get_crash_count)
    if [ "${crash_count:-0}" -gt 0 ] 2>/dev/null; then
        echo -e "  크래시 이력: ${YELLOW}${crash_count}회${NC}"
    else
        echo -e "  크래시 이력: ${GREEN}없음${NC}"
    fi

    # GPU 설정
    local force_gpu
    force_gpu=$(get_json_value "$GUARDIAN_CONFIG" "forceDisableGpu")
    if [ "$force_gpu" = "True" ] || [ "$force_gpu" = "true" ]; then
        echo -e "  GPU 가속: ${YELLOW}비활성화 (안정 모드)${NC}"
    else
        echo -e "  GPU 가속: ${GREEN}활성화 (기본)${NC}"
    fi

    # 로그 위치
    echo ""
    echo -e "  ${GRAY}로그: $GUARDIAN_LOG_DIR${NC}"
    echo ""
}

clean_old_logs() {
    if [ -d "$GUARDIAN_LOG_DIR" ]; then
        find "$GUARDIAN_LOG_DIR" -name "guardian_*.log" -mtime +30 -delete 2>/dev/null || true
    fi
}

# ══════════════════════════════════════════════════════════════
# 메인 실행
# ══════════════════════════════════════════════════════════════

# --silent 플래그 처리
if [[ " $* " == *" --silent "* ]]; then
    SILENT=1
fi

banner
clean_old_logs

case "${1:-}" in
    install)
        install_guardian
        ;;
    uninstall)
        uninstall_guardian
        ;;
    protect)
        protect_settings
        ;;
    watch)
        log "INFO" "감시 모드 시작 (Ctrl+C로 종료)"
        protect_settings
        watch_process
        ;;
    status)
        show_status
        ;;
    *)
        echo -e "  사용법:"
        echo ""
        echo -e "    ${GREEN}$0 install${NC}      # Guardian 설치 (권장)"
        echo -e "    ${GRAY}$0 watch${NC}        # 수동 감시 시작"
        echo -e "    ${GRAY}$0 protect${NC}      # 설정 보호 1회 실행"
        echo -e "    ${GRAY}$0 status${NC}       # 상태 확인"
        echo -e "    ${GRAY}$0 uninstall${NC}    # Guardian 제거"
        echo ""
        echo -e "  최초 사용 시 ${GREEN}install${NC}을 실행하면:"
        echo -e "    ${GRAY}- 로그인 시 자동으로 안정성 설정이 적용됩니다${NC}"
        echo -e "    ${GRAY}- Claude 크래시 시 자동으로 안전 모드 재시작됩니다${NC}"
        echo -e "    ${GRAY}- 앱 업데이트 후 설정이 리셋되어도 자동 복구됩니다${NC}"
        echo ""
        ;;
esac
