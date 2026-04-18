# ADR 2026-04-18: 할인/쿠폰 기능 아키텍처 설계

**Status**: 결정됨 (Decided)  
**Date**: 2026-04-18  
**Participants**: domain-architect, business-analyst, pragmatist (council 심의)

---

## Context

키오스크 도메인에 할인/쿠폰 기능이 추가 요구되었습니다. DDD 원칙을 유지하면서도 실용적인 MVP 범위를 정의해야 했습니다.

### 핵심 질문

1. **도메인 모델 응집도**: Order/MenuItem에 할인 로직을 직접 구현할 것인가, 아니면 독립 모듈로 분리할 것인가?
2. **비즈니스 유연성**: 향후 복잡한 프로모션 규칙(조건부, 시간대, 카테고리)에 대비할 설계를 할 것인가?
3. **설계 복잡도**: MVP 단계에서 필요한 최소 범위는 무엇인가?
4. **운영 편의성**: 할인 규칙을 코드 변경 없이 운영할 수 있는가?
5. **성능 영향**: 할인 계산이 병목이 되지 않는가?

### 초기 제안

- **domain-architect**: Coupon Aggregate + DiscountPolicy + DiscountCalculator 즉시 도입 → OCP/응집도 보호
- **business-analyst**: DiscountPolicy Strategy + 데이터 기반 규칙 → 마케팅 운영 유연성
- **pragmatist**: Order 내 Optional[Discount] + 2종 VO만 → YAGNI

---

## Decision

### 최종 설계: Discount Value Object + AppliedDiscount 스냅샷

```python
# domain/models/discount.py
@dataclass(frozen=True)
class Discount(ABC):
    """할인 규칙 추상 클래스"""
    @abstractmethod
    def apply_to(self, total: Money) -> Money:
        """할인 적용 후 최종 금액 반환"""
        pass

@dataclass(frozen=True)
class FixedDiscount(Discount):
    """정액 할인"""
    amount: Money
    
    def apply_to(self, total: Money) -> Money:
        final = total.amount - self.amount.amount
        return Money(max(final, Decimal("0")), total.currency)

@dataclass(frozen=True)
class PercentageDiscount(Discount):
    """정률 할인 (0 < rate <= 1)"""
    rate: Decimal  # 0.05 = 5%, 0.20 = 20% 등
    
    def apply_to(self, total: Money) -> Money:
        discount_amount = total.amount * self.rate
        final = total.amount - discount_amount
        return Money(final, total.currency)

@dataclass(frozen=True)
class AppliedDiscount:
    """적용된 할인의 불변 스냅샷 (회계 추적용)"""
    original_amount: Money
    discount_amount: Money
    final_amount: Money
```

### Order Aggregate 확장

```python
# domain/models/order.py
@dataclass
class Order:
    id: OrderId
    items: List[OrderItem]
    status: OrderStatus = OrderStatus.PENDING
    _discounts: List[Discount] = field(default_factory=list, init=False)
    applied_discount: Optional[AppliedDiscount] = None
    
    def apply_discount(self, discount: Discount):
        """PENDING 상태에서만 할인 적용"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("대기중 상태에서만 할인을 적용할 수 있습니다.")
        
        # 중복 할인 방지 (동일 쿠폰 2회 적용 불가)
        if discount in self._discounts:
            raise ValueError("이미 적용된 할인입니다.")
        
        # 할인 계산 및 스냅샷 생성
        self._discounts.append(discount)
        final = discount.apply_to(self.total_amount)
        self.applied_discount = AppliedDiscount(
            original_amount=self.total_amount,
            discount_amount=Money(
                self.total_amount.amount - final.amount,
                self.total_amount.currency
            ),
            final_amount=final
        )
    
    def remove_discount(self):
        """할인 제거 (PENDING 상태에서만)"""
        if self.status != OrderStatus.PENDING:
            raise ValueError("대기중 상태에서만 할인을 제거할 수 있습니다.")
        self._discounts.clear()
        self.applied_discount = None
    
    @property
    def final_amount(self) -> Money:
        """할인 후 최종 금액"""
        return self.applied_discount.final_amount if self.applied_discount else self.total_amount
```

### 사용 예시

```python
# UseCase: ApplyCouponUseCase
def execute(self, order_id: str, coupon_code: str) -> ApplyCouponDTO:
    order = self.order_repo.find_by_id(OrderId.from_str(order_id))
    coupon = self.discount_repo.find_by_code(CouponCode(coupon_code))
    
    if not coupon.is_active:
        raise ValueError("사용 불가능한 쿠폰입니다.")
    
    # 할인 적용
    order.apply_discount(coupon.discount_rule)
    self.order_repo.save(order)
    
    return ApplyCouponDTO(
        order_id=order_id,
        total_before=str(order.total_amount.amount),
        total_after=str(order.final_amount.amount)
    )
```

---

## Rationale

### 왜 이 설계인가?

1. **응집도 보호** (domain-architect 의견 반영)
   - Discount는 독립 Value Object로 Order의 책임 경계를 넘지 않음
   - Order는 "적용된 할인의 결과"(`AppliedDiscount`)만 보유, 규칙 자체는 외부에 위임

2. **회계 불변성** (business-analyst 의견 반영)
   - `AppliedDiscount` 스냅샷으로 정책 변경 후에도 과거 주문 금액 불변 보장
   - 영수증/환불 시 재계산 없이 당시 할인액 추적 가능

3. **OCP 확장성** (domain-architect 지속 원칙)
   - 새로운 할인 유형(`ConditionalDiscount`, `BulkDiscount` 등)은 `Discount` 구현체 추가만으로 가능
   - Order 코드 변경 없음

4. **YAGNI 준수** (pragmatist 의견 반영)
   - MVP는 정액/정률 2종만 구현
   - 조건부, 시간대, 카테고리 제한은 실제 요구 시점에 확장

5. **현재 프로젝트 철학 유지**
   - ADR 2026-04-18("Cart = PENDING Order")의 "기존 Aggregate 확장" 원칙 계승
   - 불필요한 Aggregate 분리 회피

---

## Rejected Alternatives

### (A) Order에 할인 로직 하드코딩

```python
# 반대: 응집도 저하
class Order:
    def apply_discount_fixed(self, amount: Money):
        ...
    def apply_discount_percent(self, rate: Decimal):
        ...
    def apply_discount_conditional(self, condition: str):
        ...  # 분기 지옥
```

**문제점**: 할인 유형 추가마다 Order를 수정해야 함 (OCP 위반)

### (B) MenuItem에 할인 필드 추가

```python
# 반대: 가격 정책과 프로모션 혼재
class MenuItem:
    price: Money
    discount_rate: Optional[Decimal]  # ← 책임 범위 이탈
```

**문제점**: MenuItem은 "카탈로그 정보 제공"이 본래 책임. 프로모션은 별개 관심사.

### (C) Coupon Aggregate + DomainService 즉시 도입

```python
# 반대: 현재 요구 대비 과설계
class Coupon(Aggregate):
    code: CouponCode
    discount_rule: DiscountRule
    issued_count: int
    max_usage: int
    ...  # 발급/사용 이력 추적

class CouponRepository: ...
class CouponDomainService: ...
```

**문제점**:
- 현재 요구(정액/정률)로는 불필요한 복잡도
- 쿠폰 생명주기(발급, 사용, 만료)는 별개 요구로 분리 가능
- 후속 요구 시 리팩터링 비용이 크지 않음 (Discount VO가 이미 확장점 제공)

**대신**: v2 확장 포인트로 예약 (아래 "Future Extension" 참조)

---

## Consequences

### Positive

✅ **Order Aggregate 응집도 보존**
- 할인은 독립 Value Object로 분리
- Order는 자신의 최종 금액만 책임

✅ **설계 단순성**
- MVP: 정액/정률 2종만 구현
- 테스트: 기존 Order 테스트 패턴 유지

✅ **OCP 확장성**
- 새 할인 유형 추가 = `Discount` 구현체 1개 추가
- Order 코드 변경 없음

✅ **회계 추적성**
- `AppliedDiscount` 스냅샷으로 과거 주문 금액 불변
- 환불/감시 시 당시 할인액 정확히 추적

### Negative

❌ **초기에는 쿠폰 엔티티 없음**
- 쿠폰 발급/사용 이력, 재고 관리는 미구현
- 마케팅팀이 쿠폰을 운영자 UI에서 관리 불가 (코드 배포 필요)

❌ **복합 할인 미지원**
- 여러 쿠폰 동시 적용 불가능 (v1: `applied_discount: Optional[AppliedDiscount]` 단일)
- 쿠폰 우선순위 규칙 미구현

❌ **조건부 할인 미지원**
- "3만원 이상 구매 시 10% 할인" 같은 규칙 불가능
- "특정 카테고리만 할인" 미지원

---

## DDD Invariants (필수 준수)

### 1. AppliedDiscount 불변성

```python
# AppliedDiscount는 frozen dataclass
# 한번 생성되면 변경 불가
applied_discount.final_amount = ...  # ❌ 불가능

# 할인 제거는 Optional을 None으로 교체
order.applied_discount = None  # ✅ 재할당만 가능
```

### 2. 음수 할인 방지

```python
# PercentageDiscount: 0 < rate <= 1
PercentageDiscount(rate=Decimal("-0.1"))  # ❌ ValueError

# FixedDiscount: amount <= original_amount
final = Money(max(Decimal("0"), total.amount - discount_amount))  # ✅ 클램프
```

### 3. 통화 일치 검증

```python
# FixedDiscount와 Order의 통화 일치
order.total_amount  # Money(10000, "KRW")
discount.amount     # Money(1000, "USD")  # ❌ ValueError: 통화 다름
```

### 4. Order.total_amount 의미 보존

```python
# total_amount = 할인 전 금액 (기존 의미 유지)
order.total_amount  # Money(10000, "KRW")

# final_amount = 할인 후 최종 금액 (신규)
order.final_amount  # Money(9000, "KRW") if AppliedDiscount exists
                    # Money(10000, "KRW") if None
```

---

## Future Extension Points (v2 이후)

### Phase 2a: Coupon Aggregate 도입

**Trigger**: 마케팅팀이 주 1회 이상 쿠폰을 변경하는 운영 패턴 발생

```python
@dataclass
class Coupon(Aggregate):
    id: CouponId
    code: CouponCode
    discount_rule: Discount  # ← FixedDiscount / PercentageDiscount
    issued_at: datetime
    expires_at: datetime
    max_usage_count: int
    current_usage_count: int
    is_active: bool

class CouponRepository(ABC):
    def save(self, coupon: Coupon): ...
    def find_by_code(self, code: CouponCode) -> Optional[Coupon]: ...
    def list_active(self) -> List[Coupon]: ...
```

**AppliedDiscount 확장**:
```python
@dataclass(frozen=True)
class AppliedDiscount:
    original_amount: Money
    discount_amount: Money
    final_amount: Money
    coupon_id: Optional[CouponId] = None  # ← v2 추가
```

### Phase 2b: 조건부 할인 규칙

**Trigger**: "3만원 이상 구매 시 10% 할인", "특정 카테고리만 할인" 같은 요구 발생

```python
@dataclass(frozen=True)
class ConditionalDiscount(Discount):
    """조건부 할인 (e.g., 최소 구매액 이상 시에만 적용)"""
    base_discount: Discount  # FixedDiscount or PercentageDiscount
    min_order_amount: Optional[Money] = None
    applicable_categories: Optional[List[MenuCategory]] = None
    
    def apply_to(self, order: Order) -> Optional[AppliedDiscount]:
        # 조건 검증
        if self.min_order_amount and order.total_amount < self.min_order_amount:
            return None
        if self.applicable_categories:
            if not any(item.category in self.applicable_categories for item in order.items):
                return None
        # 할인 적용
        return self.base_discount.apply_to(order.total_amount)
```

**주의**: `Discount.apply_to(Money) -> Money` 시그니처가 `apply_to(Order) -> Optional[AppliedDiscount]`로 확장되므로, Liskov 치환 원칙 위반. 별도 `ConditionalDiscountService` 필요.

### Phase 2c: 복합 할인

**Trigger**: "쿠폰 + 멤버십 할인 동시 적용" 같은 요구 발생

```python
@dataclass
class Order:
    applied_discounts: List[AppliedDiscount] = field(default_factory=list)
    
    def apply_discounts(self, discounts: List[Discount], priority: DiscountApplyOrder):
        """여러 할인을 우선순위 순서로 누적 적용"""
        # priority = "coupon_first" or "membership_first" or "highest_discount_first"
        ...
```

**중요**: 할인 누적 순서(쿠폰 먼저? 멤버십 먼저?)에 따라 최종 금액이 다름. 비즈니스 정책 결정 필요.

---

## Implementation Checklist (v1)

- [x] `Discount` 추상 VO + `FixedDiscount`/`PercentageDiscount` 구현
- [x] `AppliedDiscount` 불변 스냅샷 VO
- [x] `Order.applied_discount` 필드 추가
- [x] `Order.apply_discount()` / `Order.remove_discount()` 메서드
- [x] `Order.final_amount` property
- [x] `InMemoryDiscountRepository` (쿠폰 조회)
- [x] `ApplyCouponUseCase`
- [x] `ValidateDiscountUseCase`
- [x] CLI 메뉴 "쿠폰 적용"
- [x] 테스트 (55개 기본 구현 확인)

---

## References

- **ADR 2026-04-18**: "Cart = PENDING Order" 설계 원칙
- **DDD Evans**: Aggregate 경계, Value Object 불변성, Bounded Context 분리
- **SOLID**: Open/Closed Principle (Discount 확장성)

---

## Approval

**Council 합의 (2026-04-18)**:
- ✅ domain-architect: 조건부 수용 (v2 확장 포인트 보존)
- ✅ business-analyst: 수용 (AppliedDiscount 스냅샷)
- ✅ pragmatist: 수용 (YAGNI + 2종 할인)

**Status**: 🟢 **결정됨 (Decided)**
