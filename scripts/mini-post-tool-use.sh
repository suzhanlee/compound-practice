#!/bin/bash
# mini-post-tool-use.sh — PostToolUse hook for mini-harness orchestration
# After mini-harness Skill completes, ensure state.json status is processing

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')
CWD=$(echo "$INPUT" | jq -r '.cwd')
STATE_FILE="$CWD/.claude/state/state.json"

if [[ "$TOOL_NAME" == "Skill" && -f "$STATE_FILE" ]]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  SKILL_NAME=$(jq -r '.skill_name' "$STATE_FILE")

  if [[ "$SKILL_NAME" == "mini-harness" ]]; then
    jq --arg ts "$TIMESTAMP" '.status = "processing" | .timestamp = $ts' \
      "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
  fi
fi
