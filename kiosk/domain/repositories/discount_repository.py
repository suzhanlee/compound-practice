from abc import ABC, abstractmethod
from typing import List, Optional
from kiosk.domain.models.discount import Discount
from kiosk.domain.models.value_objects import DiscountId, CouponCode


class DiscountRepository(ABC):
    @abstractmethod
    def save(self, discount: Discount) -> None:
        pass

    @abstractmethod
    def find_by_id(self, discount_id: DiscountId) -> Optional[Discount]:
        pass

    @abstractmethod
    def find_by_code(self, code: CouponCode) -> Optional[Discount]:
        pass

    @abstractmethod
    def list_active(self) -> List[Discount]:
        pass
