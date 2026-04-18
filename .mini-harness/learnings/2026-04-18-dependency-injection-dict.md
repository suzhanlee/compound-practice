---
date: 2026-04-18
tags: [cli, dependency-injection, use-case, python]
---

## Problem

CLI에 다수의 use case를 주입할 때 `build_dependencies()` 반환값이 커지면서 호출부에서 구조 분해가 복잡해진다.

## Cause

원래 `get_menu`, `place_order`, `process_payment` 3개만 있을 때 튜플로 충분했으나, 카트 use case 5개가 추가되면서 반환값 개수가 8개로 증가하여 가독성과 유지보수성이 떨어졌다.

## Rule

다수의 use case를 DI할 때는 튜플 대신 딕셔너리 `{키: use_case}`로 반환하여 호출부에서 필요한 것만 구조 분해하고, 추가/제거 시 영향 범위를 최소화한다.
