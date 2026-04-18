from kiosk.domain.models.value_objects import CouponCode
from kiosk.domain.repositories.discount_repository import DiscountRepository
from dataclasses import dataclass


@dataclass
class ValidateDiscountDTO:
    coupon_code: str
    is_valid: bool
    discount_type: str = None
    discount_value: str = None
    applicable_target: str = None


class ValidateDiscountUseCase:
    def __init__(self, discount_repo: DiscountRepository):
        self.discount_repo = discount_repo

    def execute(self, coupon_code: str) -> ValidateDiscountDTO:
        discount = self.discount_repo.find_by_code(CouponCode(coupon_code))

        if not discount or not discount.validate_coupon():
            return ValidateDiscountDTO(
                coupon_code=coupon_code,
                is_valid=False
            )

        return ValidateDiscountDTO(
            coupon_code=coupon_code,
            is_valid=True,
            discount_type=discount.rule.discount_type,
            discount_value=str(discount.rule.value),
            applicable_target=discount.rule.applicable_target
        )
