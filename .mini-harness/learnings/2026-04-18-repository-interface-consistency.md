---
date: 2026-04-18
tags: [repository, use-case, interface, python, ddd]
---

## Problem

use case 구현 시 repository 메서드명을 잘못 사용하여(get() 대신 find_by_id()) 런타임 오류 발생.

## Cause

OrderRepository 인터페이스 정의(find_by_id)와 use case 구현(get 호출) 간 메서드명 불일치. 인터페이스를 먼저 확인하지 않고 구현했음.

## Rule

Repository 사용 use case 구현 시 먼저 OrderRepository 추상 인터페이스의 메서드 시그니처를 확인한 후 구현하여, 인터페이스-구현 불일치로 인한 런타임 오류를 사전 방지한다.
