"""카트 기능 통합 테스트"""
import pytest
from decimal import Decimal
from uuid import UUID
from kiosk.domain.models.order import Order, OrderItem, OrderStatus
from kiosk.domain.models.value_objects import OrderId, MenuItemId, Money
from kiosk.application.use_cases.cart_use_cases import (
    AddToCartUseCase, RemoveFromCartUseCase, UpdateQuantityUseCase,
    ViewCartUseCase, CheckoutUseCase
)
from kiosk.infrastructure.repositories.in_memory_order_repository import InMemoryOrderRepository

# 테스트용 고정 UUID
ITEM_1_ID = "550e8400-e29b-41d4-a716-446655440000"
ITEM_2_ID = "550e8400-e29b-41d4-a716-446655440001"


@pytest.fixture
def order_repo():
    return InMemoryOrderRepository()


@pytest.fixture
def cart_use_cases(order_repo):
    return {
        'add': AddToCartUseCase(order_repo),
        'remove': RemoveFromCartUseCase(order_repo),
        'update': UpdateQuantityUseCase(order_repo),
        'view': ViewCartUseCase(order_repo),
        'checkout': CheckoutUseCase(order_repo),
    }


class TestAddToCart:
    def test_add_single_item_creates_new_cart(self, order_repo, cart_use_cases):
        """첫 상품 추가 시 새로운 카트 생성"""
        result = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )

        assert result.order_id is not None
        assert len(result.items) == 1
        assert result.items[0].name == "아메리카노"
        assert result.items[0].quantity == 1
        assert result.total_amount == "3000"

    def test_add_duplicate_item_increases_quantity(self, cart_use_cases):
        """같은 상품 재추가 시 수량 누적"""
        # 첫 번째 추가
        result1 = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result1.order_id

        # 같은 상품 재추가
        result2 = cart_use_cases['add'].execute(
            order_id=order_id,
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=2
        )

        assert len(result2.items) == 1
        assert result2.items[0].quantity == 3  # 1 + 2
        assert result2.total_amount == "9000"  # 3000 * 3

    def test_add_multiple_different_items(self, cart_use_cases):
        """다양한 상품 추가"""
        result1 = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result1.order_id

        result2 = cart_use_cases['add'].execute(
            order_id=order_id,
            menu_item_id=ITEM_2_ID,
            name="카페라떼",
            unit_price_amount="4500",
            quantity=2
        )

        assert len(result2.items) == 2
        assert result2.total_amount == "12000"  # 3000 + 4500*2

    def test_add_respects_quantity_limit(self, cart_use_cases):
        """수량 제한(최대 10개) 준수"""
        with pytest.raises(ValueError, match="수량은 최대 10개"):
            cart_use_cases['add'].execute(
                order_id="",
                menu_item_id=ITEM_1_ID,
                name="아메리카노",
                unit_price_amount="3000",
                quantity=11
            )


class TestRemoveFromCart:
    def test_remove_item_from_cart(self, cart_use_cases):
        """카트에서 상품 제거"""
        result1 = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result1.order_id

        result2 = cart_use_cases['add'].execute(
            order_id=order_id,
            menu_item_id=ITEM_2_ID,
            name="카페라떼",
            unit_price_amount="4500",
            quantity=1
        )

        result3 = cart_use_cases['remove'].execute(order_id, ITEM_1_ID)

        assert len(result3.items) == 1
        assert result3.items[0].name == "카페라떼"
        assert result3.total_amount == "4500"

    def test_remove_nonexistent_item(self, cart_use_cases):
        """존재하지 않는 상품 제거 시도"""
        result = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result.order_id

        result2 = cart_use_cases['remove'].execute(order_id, "550e8400-e29b-41d4-a716-446655440999")

        # 아무것도 제거되지 않음 (오류 없음)
        assert len(result2.items) == 1


class TestUpdateQuantity:
    def test_update_quantity_of_item(self, cart_use_cases):
        """카트 항목의 수량 변경"""
        result1 = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=2
        )
        order_id = result1.order_id

        result2 = cart_use_cases['update'].execute(order_id, ITEM_1_ID, 5)

        assert result2.items[0].quantity == 5
        assert result2.total_amount == "15000"

    def test_update_respects_quantity_limits(self, cart_use_cases):
        """수량 변경 시 제한 준수"""
        result1 = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result1.order_id

        with pytest.raises(ValueError, match="수량은 1~10 사이"):
            cart_use_cases['update'].execute(order_id, ITEM_1_ID, 11)

    def test_update_nonexistent_item_fails(self, cart_use_cases):
        """존재하지 않는 항목 수량 변경 실패"""
        result = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result.order_id

        with pytest.raises(ValueError, match="항목을 찾을 수 없습니다"):
            cart_use_cases['update'].execute(order_id, "550e8400-e29b-41d4-a716-446655440999", 2)


class TestViewCart:
    def test_view_cart_shows_current_state(self, cart_use_cases):
        """카트 조회 시 현재 상태 반영"""
        result1 = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=2
        )
        order_id = result1.order_id

        result = cart_use_cases['view'].execute(order_id)

        assert result.order_id == order_id
        assert len(result.items) == 1
        assert result.items[0].quantity == 2
        assert result.item_count == 2


class TestCheckout:
    def test_checkout_confirms_order(self, cart_use_cases, order_repo):
        """체크아웃 시 카트 → 주문 상태 변경"""
        result1 = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result1.order_id

        result = cart_use_cases['checkout'].execute(order_id)

        # 주문 상태 확인
        order = order_repo.find_by_id(OrderId.from_str(order_id))
        assert order.status == OrderStatus.CONFIRMED

    def test_cannot_checkout_empty_cart(self, cart_use_cases):
        """빈 카트 체크아웃 실패"""
        result = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result.order_id

        # 상품 제거
        cart_use_cases['remove'].execute(order_id, ITEM_1_ID)

        # 체크아웃 시도
        with pytest.raises(ValueError, match="주문 항목이 없습니다"):
            cart_use_cases['checkout'].execute(order_id)


class TestCartE2EFlow:
    def test_full_cart_to_order_flow(self, cart_use_cases):
        """전체 카트 → 주문 플로우"""
        # 1. 상품 추가
        result = cart_use_cases['add'].execute(
            order_id="",
            menu_item_id=ITEM_1_ID,
            name="아메리카노",
            unit_price_amount="3000",
            quantity=1
        )
        order_id = result.order_id

        # 2. 상품 추가
        result = cart_use_cases['add'].execute(
            order_id=order_id,
            menu_item_id=ITEM_2_ID,
            name="카페라떼",
            unit_price_amount="4500",
            quantity=2
        )

        # 3. 수량 변경
        result = cart_use_cases['update'].execute(order_id, ITEM_1_ID, 2)
        assert result.items[0].quantity == 2

        # 4. 카트 조회
        result = cart_use_cases['view'].execute(order_id)
        assert len(result.items) == 2
        assert result.total_amount == "15000"  # 3000*2 + 4500*2 = 15000

        # 5. 체크아웃
        result = cart_use_cases['checkout'].execute(order_id)
        assert result.order_id == order_id
