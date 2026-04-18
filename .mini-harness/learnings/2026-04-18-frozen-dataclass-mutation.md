---
date: 2026-04-18
tags: [ddd, frozen-dataclass, value-object, cart, quantity]
---

## Problem

DDD 값 객체는 frozen dataclass로 불변성을 강제하지만, 카트 기능은 OrderItem의 수량을 동적으로 증가시켜야 한다.

## Cause

OrderItem을 값 객체(immutable)로 설계했으나, 카트 add_item 구현 시 같은 상품 추가 시 수량 누적이 필요해져 설계와 구현 요구사항이 충돌했다.

## Rule

DDD 값 객체가 mutable한 상태 변경이 필요한 경우, `increase_quantity()`/`set_quantity()` 메서드를 제공하고 `object.__setattr__()`로 내부 상태를 업데이트하되, 불변식은 메서드 내부에서 검증한다.
