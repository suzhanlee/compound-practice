from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from .value_objects import UserId


@dataclass
class User:
    id: UserId
    email: str
    name: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create(cls, email: str, name: str) -> User:
        return cls(
            id=UserId.generate(),
            email=email,
            name=name,
        )

    def update_profile(self, name: str):
        self.name = name
        self.updated_at = datetime.now()
