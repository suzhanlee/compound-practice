---
date: 2026-04-18
tags: [decimal, testing, ddd, dto, money]
---

## Problem

DTO에서 Decimal을 str()로 변환했을 때 테스트에서 문자열 비교 시 '9000'과 '9000.0'처럼 포맷이 달라지는 현상 발생

## Cause

Python Decimal 객체를 str()로 변환할 때 백분율 계산의 결과가 부동소수점으로 표현되면서 '.0'이 추가됨

## Rule

DTO에서 금액 문자열을 반환할 때는 Decimal(str_value)로 비교하거나, 테스트에서 Decimal 끼리 비교하는 방식으로 통일하여 포맷 차이를 피한다.
