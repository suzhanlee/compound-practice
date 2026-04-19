---
date: 2026-04-19
tags: [frozen-dataclass, object-setattr, value-object, test, mutation]
---

## Problem
frozen dataclass에 object.__setattr__()로 값을 변경한 후 테스트에서 변경 전 값을 포함한 누산값을 기대했으나, 변경 후의 현재 값에서 더하는 구조여서 기대값이 달랐다.

## Cause
Stock.decrease()로 stock이 0이 된 후 restock(5) 시 0+5=5인데, 테스트는 원래 set_stock(1) 값인 1을 포함한 6을 기대했다. object.__setattr__() 패턴이 in-place mutation임을 간과했다.

## Rule
frozen dataclass를 object.__setattr__()로 mutate할 때, 연산 후 최종 상태를 기준으로 테스트 기대값을 작성하라 — 이전 상태와의 합산이 아닌 현재 필드 값을 직접 검증한다.
