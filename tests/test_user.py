import pytest
from kiosk.domain.models.user import User
from kiosk.domain.models.value_objects import UserId
from kiosk.infrastructure.repositories.in_memory_user_repository import InMemoryUserRepository


class TestUser:
    def test_user_creation(self):
        user = User.create(email="test@example.com", name="Test User")
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.id is not None

    def test_user_update_profile(self):
        user = User.create(email="test@example.com", name="Old Name")
        original_created_at = user.created_at
        user.update_profile("New Name")
        assert user.name == "New Name"
        assert user.created_at == original_created_at
        assert user.updated_at >= original_created_at


class TestUserId:
    def test_user_id_generation(self):
        id1 = UserId.generate()
        id2 = UserId.generate()
        assert id1.value != id2.value
        assert isinstance(id1, UserId)

    def test_user_id_from_str(self):
        id1 = UserId.generate()
        id_str = str(id1.value)
        id2 = UserId.from_str(id_str)
        assert id1.value == id2.value

    def test_user_id_immutability(self):
        user_id = UserId.generate()
        with pytest.raises(AttributeError):
            user_id.value = None


class TestInMemoryUserRepository:
    @pytest.fixture
    def repo(self):
        return InMemoryUserRepository()

    def test_save_and_find_by_id(self, repo):
        user = User.create(email="test@example.com", name="Test User")
        repo.save(user)
        found = repo.find_by_id(user.id)
        assert found is not None
        assert found.email == user.email

    def test_find_by_email(self, repo):
        user = User.create(email="test@example.com", name="Test User")
        repo.save(user)
        found = repo.find_by_email("test@example.com")
        assert found is not None
        assert found.name == "Test User"

    def test_find_by_email_not_found(self, repo):
        found = repo.find_by_email("nonexistent@example.com")
        assert found is None

    def test_find_by_id_not_found(self, repo):
        fake_id = UserId.generate()
        found = repo.find_by_id(fake_id)
        assert found is None
