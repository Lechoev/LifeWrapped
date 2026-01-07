import pytest
from datetime import date
from unittest.mock import AsyncMock, Mock
from src.profiles.services import ProfileService
from src.profiles import exceptions


class MockUoW:
    def __init__(self):
        self.profiles = Mock()
        self.session = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        pass


@pytest.mark.asyncio
async def test_create_profile_success():
    mock_uow = MockUoW()
    mock_profile = Mock()
    mock_profile.user_id = 1
    mock_profile.first_name = "John"
    mock_profile.last_name = "Doe"
    mock_profile.bio = "Developer"
    mock_profile.birth_date = date(1990, 1, 1)
    mock_profile.avatar_url = "avatar.jpg"

    mock_uow.profiles.get_profile = AsyncMock(return_value=None)
    mock_uow.profiles.create_profile = AsyncMock(return_value=mock_profile)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    profile_data = {
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Developer",
        "birth_date": date(1990, 1, 1),
        "avatar_url": "avatar.jpg"
    }

    result = await service.create_profile(user_id=1, profile_data=profile_data)

    assert result["user_id"] == 1
    assert result["first_name"] == "John"
    assert result["last_name"] == "Doe"
    assert result["bio"] == "Developer"
    assert result["birth_date"] == mock_profile.birth_date.isoformat()

    mock_uow.profiles.get_profile.assert_called_once_with(1)
    mock_uow.profiles.create_profile.assert_called_once_with(
        data={"user_id": 1, **profile_data}
    )


@pytest.mark.asyncio
async def test_create_profile_already_exists():
    mock_uow = MockUoW()
    mock_existing_profile = Mock()

    mock_uow.profiles.get_profile = AsyncMock(return_value=mock_existing_profile)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    with pytest.raises(exceptions.ProfileAlreadyExistsError) as exc_info:
        await service.create_profile(user_id=1, profile_data={})

    assert "Профиль для пользователя 1 уже существует" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_profile_success():
    mock_uow = MockUoW()
    mock_profile = Mock()
    mock_profile.user_id = 1
    mock_profile.first_name = "Updated"
    mock_profile.last_name = "Name"
    mock_profile.bio = "Updated bio"
    mock_profile.birth_date = date(1995, 5, 15)
    mock_profile.avatar_url = "new_avatar.jpg"

    mock_uow.profiles.update_profile = AsyncMock(return_value=mock_profile)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    update_data = {
        "first_name": "Updated",
        "last_name": "Name",
        "bio": "Updated bio",
        "birth_date": date(1995, 5, 15),
        "avatar_url": "new_avatar.jpg"
    }

    result = await service.update_profile(user_id=1, update_data=update_data)

    assert result["user_id"] == 1
    assert result["first_name"] == "Updated"
    assert result["last_name"] == "Name"
    assert result["bio"] == "Updated bio"
    assert result["birth_date"] == mock_profile.birth_date.isoformat()

    mock_uow.profiles.update_profile.assert_called_once_with(
        user_id=1,
        update_data=update_data
    )


@pytest.mark.asyncio
async def test_update_profile_not_found():
    mock_uow = MockUoW()
    mock_uow.profiles.update_profile = AsyncMock(return_value=None)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    with pytest.raises(exceptions.ProfileNotFoundError) as exc_info:
        await service.update_profile(user_id=999, update_data={})

    assert "Профиль для пользователя 999 не найден" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_profile_success():
    mock_uow = MockUoW()
    mock_profile = Mock()
    mock_profile.user_id = 1
    mock_profile.first_name = "John"
    mock_profile.last_name = "Doe"

    mock_uow.profiles.get_profile = AsyncMock(return_value=mock_profile)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    result = await service.get_profile(user_id=1)

    assert result is mock_profile
    mock_uow.profiles.get_profile.assert_called_once_with(user_id=1)


@pytest.mark.asyncio
async def test_get_profile_not_found():
    mock_uow = MockUoW()
    mock_uow.profiles.get_profile = AsyncMock(return_value=None)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    with pytest.raises(exceptions.ProfileNotFoundError) as exc_info:
        await service.get_profile(user_id=999)

    assert "Профиль для пользователя 999 не найден" in str(exc_info.value)


@pytest.mark.asyncio
async def test_check_profile_exists():
    mock_uow = MockUoW()
    mock_profile = Mock()

    mock_uow.profiles.check_profile = AsyncMock(return_value=mock_profile)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    result = await service.check_profile(user_id=1)

    assert result is mock_profile
    mock_uow.profiles.check_profile.assert_called_once_with(user_id=1)


@pytest.mark.asyncio
async def test_check_profile_not_exists():
    mock_uow = MockUoW()
    mock_uow.profiles.check_profile = AsyncMock(return_value=None)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    result = await service.check_profile(user_id=999)

    assert result is None
    mock_uow.profiles.check_profile.assert_called_once_with(user_id=999)


@pytest.mark.asyncio
async def test_create_profile_with_none_values():
    mock_uow = MockUoW()
    mock_profile = Mock()
    mock_profile.user_id = 1
    mock_profile.first_name = None
    mock_profile.last_name = None
    mock_profile.bio = None
    mock_profile.birth_date = None
    mock_profile.avatar_url = None

    mock_uow.profiles.get_profile = AsyncMock(return_value=None)
    mock_uow.profiles.create_profile = AsyncMock(return_value=mock_profile)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    profile_data = {
        "first_name": None,
        "last_name": None,
        "bio": None,
        "birth_date": None,
        "avatar_url": None
    }

    result = await service.create_profile(user_id=1, profile_data=profile_data)

    assert result["user_id"] == 1
    assert result["first_name"] is None
    assert result["last_name"] is None
    assert result["bio"] is None
    assert result["birth_date"] is None
    assert result["avatar_url"] is None


@pytest.mark.asyncio
async def test_update_profile_partial_data():
    mock_uow = MockUoW()
    mock_profile = Mock()
    mock_profile.user_id = 1
    mock_profile.first_name = "Partial"
    mock_profile.last_name = "Update"
    mock_profile.bio = "New bio"
    mock_profile.birth_date = None
    mock_profile.avatar_url = None

    mock_uow.profiles.update_profile = AsyncMock(return_value=mock_profile)

    def mock_uow_factory():
        return mock_uow

    service = ProfileService(uow_factory=mock_uow_factory)

    update_data = {
        "first_name": "Partial",
        "bio": "New bio"
    }

    result = await service.update_profile(user_id=1, update_data=update_data)

    assert result["first_name"] == "Partial"
    assert result["bio"] == "New bio"
    mock_uow.profiles.update_profile.assert_called_once_with(
        user_id=1,
        update_data=update_data
    )
