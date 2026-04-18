from dataclasses import dataclass
from kiosk.domain.models.value_objects import DiscountId, CouponCode, DiscountRule


@dataclass(frozen=True)
class Discount:
    id: DiscountId
    code: CouponCode
    rule: DiscountRule
    is_active: bool = True

    def validate_coupon(self) -> bool:
        return self.is_active
