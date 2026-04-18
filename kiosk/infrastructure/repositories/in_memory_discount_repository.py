from typing import Dict, List, Optional
from kiosk.domain.models.discount import Discount
from kiosk.domain.models.value_objects import DiscountId, CouponCode
from kiosk.domain.repositories.discount_repository import DiscountRepository


class InMemoryDiscountRepository(DiscountRepository):
    def __init__(self):
        self._discounts: Dict[DiscountId, Discount] = {}

    def save(self, discount: Discount) -> None:
        self._discounts[discount.id] = discount

    def find_by_id(self, discount_id: DiscountId) -> Optional[Discount]:
        return self._discounts.get(discount_id)

    def find_by_code(self, code: CouponCode) -> Optional[Discount]:
        for discount in self._discounts.values():
            if discount.code == code:
                return discount
        return None

    def list_active(self) -> List[Discount]:
        return [d for d in self._discounts.values() if d.is_active]
