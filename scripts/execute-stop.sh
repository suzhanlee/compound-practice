#!/bin/bash
# execute-stop.sh — Stop hook for mini-execute ralph loop orchestration
# Handles validation-execute alternation and prevents infinite loops via last_action field

INPUT=$(cat)
CWD=$(echo "$INPUT" | jq -r '.cwd')
STATE_FILE="$CWD/.claude/state/state.json"
SPEC_FILE="$CWD/.dev/task/spec.json"

# Not in execute context → approve (delegate to mini-stop.sh)
if [[ ! -f "$STATE_FILE" ]]; then
  echo '{"decision":"approve"}'; exit 0
fi
SKILL_NAME=$(jq -r '.skill_name' "$STATE_FILE")
if [[ "$SKILL_NAME" != "mini-execute" ]]; then
  echo '{"decision":"approve"}'; exit 0
fi

# spec.json missing → approve
if [[ ! -f "$SPEC_FILE" ]]; then
  echo '{"decision":"approve"}'; exit 0
fi

REMAINING=$(jq '[.tasks[] | select(.status != "end")] | length' "$SPEC_FILE")
LAST_ACTION=$(jq -r '.last_action // "execute"' "$STATE_FILE")
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

if [[ "$REMAINING" -gt 0 ]]; then
  if [[ "$LAST_ACTION" == "execute" ]]; then
    # Transition to validate: set last_action to prevent re-entry
    jq --arg ts "$TIMESTAMP" '.last_action = "validate" | .timestamp = $ts' \
      "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    INCOMPLETE=$(jq -r '[.tasks[] | select(.status != "end") | .action] | join(", ")' "$SPEC_FILE")
    echo "{\"decision\":\"block\",\"reason\":\"미완료 task가 있습니다. validate-tasks agent를 실행하세요. 미완료: $INCOMPLETE\"}"
  else
    # Transition to re-execute: set last_action to prevent re-entry
    jq --arg ts "$TIMESTAMP" '.last_action = "execute" | .timestamp = $ts' \
      "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    echo "{\"decision\":\"block\",\"reason\":\"검증 후 미완료 task가 남아있습니다. mini-execute 스킬을 실행하세요.\"}"
  fi
else
  # All tasks complete → approve → mini-stop.sh handles compound transition
  echo '{"decision":"approve"}'
fi
