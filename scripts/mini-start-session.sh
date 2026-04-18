#!/bin/bash
# mini-start-session.sh — SessionStart hook for state recovery after compact
# Detects if session was resumed after context compression and remaining interrupted work

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
STATE_FILE="$CWD/.claude/state/state.json"
SPEC_FILE="$CWD/.dev/task/spec.json"
LOG_FILE="$CWD/.claude/state/session-recovery.log"

mkdir -p "$CWD/.claude/state"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# SessionStart 감지 (compact 후 포함)
IS_COMPACT=$(echo "$INPUT" | jq -r '.is_compact // false')
echo "[$TIMESTAMP] SessionStart fired. is_compact=$IS_COMPACT" >> "$LOG_FILE"

if [[ -f "$STATE_FILE" && -f "$SPEC_FILE" ]]; then
  SKILL_NAME=$(jq -r '.skill_name' "$STATE_FILE")
  REMAINING=$(jq '[.tasks[] | select(.status != "end")] | length' "$SPEC_FILE")
  echo "[$TIMESTAMP] Found state.json: skill=$SKILL_NAME, remaining_tasks=$REMAINING" >> "$LOG_FILE"

  if [[ "$REMAINING" -gt 0 ]]; then
    echo "[$TIMESTAMP] ⚠️ 미완료 작업 감지. 복구 필요." >> "$LOG_FILE"
    MSG="⚠️ 미완료 task $REMAINING개가 남아있습니다. ${SKILL_NAME} 스킬을 재개하려면 다시 실행하세요."
    if [[ "$IS_COMPACT" == "true" ]]; then
      MSG="$MSG (context compact 후 재개됨)"
    fi
    printf '{"decision":"block","reason":"%s"}' "$MSG"
    exit 0
  fi
fi

printf '{"decision":"approve"}'
