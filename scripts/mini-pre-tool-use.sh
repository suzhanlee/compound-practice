#!/bin/bash
# mini-pre-tool-use.sh — PreToolUse hook for mini-harness orchestration
# Before any Skill tool call, update run state with current skill and processing status

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty')
ARGS=$(echo "$INPUT" | jq -r '.tool_input.args // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')

RUNS_DIR="$CWD/.claude/state/runs"
SESSIONS_DIR="$CWD/.claude/state/sessions"

source "$CWD/scripts/harness-lib.sh"

if [[ "$TOOL_NAME" == "Skill" && -n "$SKILL_NAME" ]]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  if [[ "$SKILL_NAME" == "mini-harness" ]]; then
    # 최초 진입: run_id 생성, run state 파일 신규 생성, 세션 포인터 등록
    RUN_ID=$(generate_run_id)
    mkdir -p "$RUNS_DIR" "$SESSIONS_DIR"

    STATE_FILE="$RUNS_DIR/run-${RUN_ID}.json"
    REQ_PATH=".dev/requirements/run-${RUN_ID}/requirements.json"
    SPEC_PATH=".dev/task/run-${RUN_ID}/spec.json"

    jq -n \
      --arg run_id "$RUN_ID" \
      --arg name "mini-harness" \
      --arg goal "$ARGS" \
      --arg ts "$TIMESTAMP" \
      --arg req_path "$REQ_PATH" \
      --arg spec_path "$SPEC_PATH" \
      '{
        "run_id": $run_id,
        "skill_name": $name,
        "status": "processing",
        "goal": $goal,
        "timestamp": $ts,
        "paths": {
          "requirements": $req_path,
          "spec": $spec_path
        }
      }' > "$STATE_FILE"

    # 세션 포인터 등록
    if [[ -n "$SESSION_ID" ]]; then
      echo "$RUN_ID" > "$SESSIONS_DIR/${SESSION_ID}.run_id"
    fi

  else
    # 체인 중 다음 스킬: 세션 포인터로 STATE_FILE resolve
    STATE_FILE=$(resolve_run_state "$CWD" "$SESSION_ID")

    if [[ -n "$STATE_FILE" && -f "$STATE_FILE" ]]; then
      # 세션 포인터 갱신 (compact 후 새 session_id로 들어왔을 경우 대비)
      if [[ -n "$SESSION_ID" ]]; then
        RUN_ID=$(jq -r '.run_id' "$STATE_FILE")
        echo "$RUN_ID" > "$SESSIONS_DIR/${SESSION_ID}.run_id"
      fi

      if [[ "$SKILL_NAME" == "mini-execute" ]]; then
        jq \
          --arg name "$SKILL_NAME" \
          --arg ts "$TIMESTAMP" \
          '.skill_name = $name | .status = "processing" | .last_action = "execute" | .timestamp = $ts' \
          "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
      else
        jq \
          --arg name "$SKILL_NAME" \
          --arg ts "$TIMESTAMP" \
          '.skill_name = $name | .status = "processing" | .timestamp = $ts' \
          "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
      fi
    fi
    # STATE_FILE이 없으면 (수동 호출) hook은 아무것도 하지 않음
  fi
fi

echo '{"decision":"approve"}'
