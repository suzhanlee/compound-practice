from kiosk.domain.models.value_objects import CouponCode, OrderId
from kiosk.domain.repositories.discount_repository import DiscountRepository
from kiosk.domain.repositories.order_repository import OrderRepository
from dataclasses import dataclass


@dataclass
class ApplyCouponDTO:
    order_id: str
    coupon_code: str
    total_before: str
    total_after: str
    discount_amount: str


class ApplyCouponUseCase:
    def __init__(self, order_repo: OrderRepository, discount_repo: DiscountRepository):
        self.order_repo = order_repo
        self.discount_repo = discount_repo

    def execute(self, order_id: str, coupon_code: str) -> ApplyCouponDTO:
        order = self.order_repo.find_by_id(OrderId.from_str(order_id))
        if not order:
            raise ValueError(f"주문을 찾을 수 없습니다: {order_id}")

        discount = self.discount_repo.find_by_code(CouponCode(coupon_code))
        if not discount:
            raise ValueError(f"유효한 쿠폰이 아닙니다: {coupon_code}")

        if not discount.validate_coupon():
            raise ValueError(f"사용 불가능한 쿠폰입니다: {coupon_code}")

        total_before = order.total_amount.amount
        order.apply_discount(discount)
        self.order_repo.save(order)
        total_after = order.get_total_after_discounts().amount
        discount_amount = total_before - total_after

        return ApplyCouponDTO(
            order_id=order_id,
            coupon_code=coupon_code,
            total_before=str(total_before),
            total_after=str(total_after),
            discount_amount=str(discount_amount)
        )
