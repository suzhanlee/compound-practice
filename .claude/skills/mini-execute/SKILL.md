---
name: mini-execute
description: |
  Use when the user says "/mini-execute [task]".
  Implements the task, then records friction to session/learnings.json
  only when a clear, reusable rule can be derived.
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
  - Glob
---

# mini-execute — Implement and Record Friction

## Purpose

태스크를 구현하고, 마찰이 발생한 경우 재사용 가능한 rule을 session에 기록한다.
**rule이 없으면 기록하지 않는다** — 이것이 가장 중요한 필터.

## Workflow

### Step 1: Implement

태스크를 구현한다. 일반적인 개발 작업과 동일하게 수행한다.

### Step 2: Friction Self-Assessment

구현 완료 후 아래 세 가지를 자가 평가한다:

| 트리거 | 판단 기준 |
|--------|----------|
| 예상과 다른 동작 | 가정했던 동작과 실제 동작이 달랐는가? |
| 접근 방법 변경 | 처음 시도한 방식을 두 번 이상 바꿨는가? |
| 우회법 사용 | 표준 방식 대신 workaround를 적용했는가? |

셋 중 하나라도 해당하면 → Step 3으로 이동.
해당 없으면 → 기록 없이 종료.

### Step 3: Rule Derivation

마찰 경험에서 **다음에 바로 적용 가능한 rule**을 도출한다.

rule 예시 (좋음):
- "CSS 변수로 다크모드 구현 시 :root 외에 iframe 내부에도 별도 적용 필요"
- "jq가 없는 환경에서 JSON 파싱은 python -c 로 대체"

rule 예시 (나쁨 — 기록하지 않음):
- "잘 모르겠다"
- "조심해야 한다"
- 동작 설명만 있고 행동 지침 없음

**rule을 명확히 서술할 수 없으면 기록하지 않는다.**

### Step 4: Append to Session

`.mini-harness/session/` 디렉토리가 없으면 먼저 생성:
```bash
mkdir -p .mini-harness/session
```

`.mini-harness/session/learnings.json` 에 entry를 추가한다:

```json
{
  "problem": "무엇이 문제였나 (1~2문장)",
  "cause": "왜 발생했나 (1~2문장)",
  "rule": "다음에 어떻게 해야 하나 (행동 지침, 1문장)",
  "tags": ["keyword1", "keyword2", "keyword3"]
}
```

파일이 이미 존재하면 기존 배열에 append:
```bash
# 기존 내용 읽기 → 새 entry 추가 → 덮어쓰기
```

파일이 없으면 새 배열 `[{...}]` 로 생성한다.

### Step 5: Completion Report

```
✓ Task 완료: {task description}
  Friction recorded: {rule 첫 문장} (해당 시)
  Friction recorded: 없음 (해당 없을 시)
```

## Rules

- 구현 중 막히더라도 rule 없이 기록하지 않는다. 기록의 가치는 재사용 가능한 rule에 있다.
- tags는 mini-specify가 grep할 수 있도록 검색 가능한 키워드로 작성한다.
- session/learnings.json 조작 시 유효한 JSON을 유지한다 (append 전후 검증).
