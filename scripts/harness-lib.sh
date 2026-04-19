#!/bin/bash
# harness-lib.sh — 공통 헬퍼 함수 (mini-harness hook 스크립트에서 source)

# resolve_run_state CWD SESSION_ID
# → 해당 세션의 STATE_FILE 절대 경로를 stdout에 출력
# → 포인터가 없으면 빈 문자열 출력
resolve_run_state() {
  local cwd="$1"
  local session_id="$2"
  local runs_dir="$cwd/.dev/harness/runs"

  for run_dir in "$runs_dir"/run-*/; do
    [[ -f "$run_dir/sessions/$session_id" ]] || continue
    local state_file="$run_dir/state/state.json"
    [[ -f "$state_file" ]] && echo "$state_file" && return 0
  done
  echo ""
}

# generate_run_id
# → yyyymmdd-HHMMSS-{4hex} 형식의 run_id를 stdout에 출력 (Windows 호환)
generate_run_id() {
  local ts
  ts=$(date -u +"%Y%m%d-%H%M%S")
  local rand
  rand=$(printf '%04x' $((RANDOM * RANDOM % 65536)))
  echo "${ts}-${rand}"
}
