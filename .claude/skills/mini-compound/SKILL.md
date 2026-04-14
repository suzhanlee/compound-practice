---
name: mini-compound
description: |
  Use when the user says "/mini-compound".
  Promotes session/learnings.json entries to permanent .mini-harness/learnings/*.md files,
  then deletes the session file so the Stop hook allows exit.
allowed-tools:
  - Read
  - Write
  - Bash
  - Glob
---

# mini-compound — Promote Session Learnings

## Purpose

`.mini-harness/session/learnings.json` 의 임시 기록을 검색 가능한 영구 마크다운 파일로 변환한다.
완료 후 session 파일을 삭제하여 Stop hook이 정상 종료를 허용하게 한다.

## Workflow

### Step 1: Check Session File

```
.mini-harness/session/learnings.json 존재 여부 확인
```

파일이 없으면:
```
기록된 learning이 없습니다. 종료.
```
출력 후 중단한다.

### Step 2: Parse and Convert

JSON 배열의 각 entry를 마크다운 파일로 변환한다.

**파일명 규칙:**
- 형식: `YYYY-MM-DD-{slug}.md`
- slug: rule의 첫 어절 기반, 영문 소문자 + 하이픈, 최대 30자
  - rule이 한국어면 영어 키워드(tags 첫 번째 항목) 사용
- 같은 날짜에 여러 파일이면 `-2`, `-3` 접미사 추가

**마크다운 형식:**
```markdown
---
date: YYYY-MM-DD
tags: [tag1, tag2, tag3]
---

## Problem
{problem}

## Cause
{cause}

## Rule
{rule}
```

### Step 3: Save to Learnings Directory

`.mini-harness/learnings/` 디렉토리가 없으면 먼저 생성:
```bash
mkdir -p .mini-harness/learnings
```

각 entry를 해당 파일에 저장한다.

### Step 4: Delete Session File

```bash
rm .mini-harness/session/learnings.json
```

이 시점부터 Stop hook이 `decision: "allow"` 를 반환한다.

### Step 5: Report

```
✓ mini-compound 완료

생성된 파일:
  - .mini-harness/learnings/2026-04-13-css-iframe.md
  - .mini-harness/learnings/2026-04-13-jq-fallback.md

session/learnings.json 삭제됨.
다음 /mini-specify 가 이 learning을 검색합니다.
```

## Rules

- entry가 여러 개여도 **모두** 처리한 후 session 파일을 삭제한다. 중간에 실패해도 삭제하지 않는다.
- slug가 겹치면 덮어쓰지 않고 접미사를 추가한다.
- 저장 완료 전에 session 파일을 삭제하지 않는다.
