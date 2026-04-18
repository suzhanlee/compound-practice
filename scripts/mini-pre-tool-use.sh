#!/bin/bash
# mini-pre-tool-use.sh — PreToolUse hook for mini-harness orchestration
# Before any Skill tool call, update state.json with current skill and processing status

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
SKILL_NAME=$(echo "$INPUT" | jq -r '.tool_input.skill // empty')
ARGS=$(echo "$INPUT" | jq -r '.tool_input.args // empty')
CWD=$(echo "$INPUT" | jq -r '.cwd')
STATE_FILE="$CWD/.claude/state/state.json"

if [[ "$TOOL_NAME" == "Skill" && -n "$SKILL_NAME" ]]; then
  mkdir -p "$CWD/.claude/state"
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  if [[ "$SKILL_NAME" == "mini-harness" ]]; then
    # 최초 진입: state.json 신규 생성, goal 저장
    jq -n \
      --arg name "mini-harness" \
      --arg goal "$ARGS" \
      --arg ts "$TIMESTAMP" \
      '{"skill_name": $name, "status": "processing", "goal": $goal, "timestamp": $ts}' \
      > "$STATE_FILE"
  elif [[ -f "$STATE_FILE" ]]; then
    # 체인 중 다음 스킬: skill_name 갱신, goal 유지
    GOAL=$(jq -r '.goal // empty' "$STATE_FILE")
    if [[ "$SKILL_NAME" == "mini-execute" ]]; then
      # mini-execute: last_action 초기화
      jq \
        --arg name "$SKILL_NAME" \
        --arg ts "$TIMESTAMP" \
        '.skill_name = $name | .status = "processing" | .last_action = "execute" | .timestamp = $ts' \
        "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    else
      # 다른 스킬
      jq \
        --arg name "$SKILL_NAME" \
        --arg ts "$TIMESTAMP" \
        '.skill_name = $name | .status = "processing" | .timestamp = $ts' \
        "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
    fi
  fi
fi

echo '{"decision":"approve"}'
