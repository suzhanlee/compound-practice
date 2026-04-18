from dataclasses import dataclass
from typing import Optional
from ...domain.models.user import User
from ...domain.models.value_objects import UserId
from ...domain.repositories.user_repository import UserRepository


@dataclass
class UserDTO:
    user_id: str
    email: str
    name: str


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, email: str, name: str) -> UserDTO:
        existing = self.user_repo.find_by_email(email)
        if existing:
            raise ValueError(f"이미 가입된 사용자입니다: {email}")

        user = User.create(email=email, name=name)
        self.user_repo.save(user)

        return UserDTO(
            user_id=str(user.id.value),
            email=user.email,
            name=user.name
        )


class GetUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: str) -> Optional[UserDTO]:
        user = self.user_repo.find_by_id(UserId.from_str(user_id))
        if not user:
            return None

        return UserDTO(
            user_id=str(user.id.value),
            email=user.email,
            name=user.name
        )


class AuthenticateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, email: str) -> Optional[UserDTO]:
        user = self.user_repo.find_by_email(email)
        if not user:
            return None

        return UserDTO(
            user_id=str(user.id.value),
            email=user.email,
            name=user.name
        )
