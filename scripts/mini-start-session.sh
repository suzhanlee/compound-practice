#!/bin/bash
# mini-start-session.sh — UserPromptSubmit hook for ralph loop recovery
# Detects interrupted mini-execute and restarts the loop

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
STATE_FILE="$CWD/.claude/state/state.json"
SPEC_FILE="$CWD/.dev/task/spec.json"

if [[ -f "$STATE_FILE" && -f "$SPEC_FILE" ]]; then
  SKILL_NAME=$(jq -r '.skill_name' "$STATE_FILE")
  if [[ "$SKILL_NAME" == "mini-execute" ]]; then
    REMAINING=$(jq '[.tasks[] | select(.status != "end")] | length' "$SPEC_FILE")
    if [[ "$REMAINING" -gt 0 ]]; then
      echo "{\"decision\":\"block\",\"reason\":\"미완료 task $REMAINING개가 있습니다. mini-execute 스킬을 실행하세요.\"}"
      exit 0
    fi
  fi
fi
echo '{"decision":"approve"}'
