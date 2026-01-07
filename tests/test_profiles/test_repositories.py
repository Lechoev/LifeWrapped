import pytest
from datetime import date
from src.profiles.repositories import ProfileRepository
from src.profiles.models import ProfileModel
from src.auth_user.models import AuthModel


@pytest.mark.asyncio
async def test_create_profile(async_session):
    repo = ProfileRepository(async_session)

    user = AuthModel(email="profile_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    profile_data = {
        "user_id": user.id,
        "first_name": "John",
        "last_name": "Doe",
        "bio": "Software Developer",
        "birth_date": date(1990, 1, 1)
    }

    await repo.create_profile(profile_data)
    await async_session.commit()
    profile = await repo.get_profile(user.id)

    assert profile.id is not None
    assert profile.user_id == user.id
    assert profile.first_name == "John"
    assert profile.last_name == "Doe"
    assert profile.bio == "Software Developer"
    assert profile.birth_date == date(1990, 1, 1)


@pytest.mark.asyncio
async def test_get_profile_by_user_id(async_session):
    repo = ProfileRepository(async_session)

    user = AuthModel(email="get_profile_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    profile = ProfileModel(
        user_id=user.id,
        first_name="Alice",
        last_name="Smith"
    )
    async_session.add(profile)
    await async_session.commit()

    found_profile = await repo.get_profile(user.id)

    assert found_profile is not None
    assert found_profile.user_id == user.id
    assert found_profile.first_name == "Alice"
    assert found_profile.last_name == "Smith"


@pytest.mark.asyncio
async def test_get_profile_by_user_id_not_found(async_session):
    repo = ProfileRepository(async_session)

    user = AuthModel(email="no_profile_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    profile = await repo.get_profile(user.id)

    assert profile is None


@pytest.mark.asyncio
async def test_update_profile(async_session):
    repo = ProfileRepository(async_session)

    user = AuthModel(email="update_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    profile = ProfileModel(
        user_id=user.id,
        first_name="Old",
        last_name="Name",
        bio="Old bio"
    )
    async_session.add(profile)
    await async_session.commit()

    update_data = {
        "first_name": "New",
        "last_name": "Name",
        "bio": "Updated bio",
        "birth_date": date(1995, 5, 15)
    }

    updated_profile = await repo.update_profile(user.id, update_data)
    await async_session.commit()

    assert updated_profile.first_name == "New"
    assert updated_profile.last_name == "Name"
    assert updated_profile.bio == "Updated bio"
    assert updated_profile.birth_date == date(1995, 5, 15)
    assert updated_profile.user_id == user.id
    assert updated_profile.avatar_url is None


@pytest.mark.asyncio
async def test_update_partial_profile(async_session):
    repo = ProfileRepository(async_session)

    user = AuthModel(email="partial_update_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    profile = ProfileModel(
        user_id=user.id,
        first_name="John",
        last_name="Doe",
        bio="Original bio",
        birth_date=date(1990, 1, 1)
    )
    async_session.add(profile)
    await async_session.commit()

    updated_profile = await repo.update_profile(
        user.id,
        {"first_name": "Jonathan"}
    )
    await async_session.commit()

    assert updated_profile.first_name == "Jonathan"
    assert updated_profile.last_name == "Doe"
    assert updated_profile.bio == "Original bio"
    assert updated_profile.birth_date == date(1990, 1, 1)


@pytest.mark.asyncio
async def test_update_profile_not_found(async_session):
    repo = ProfileRepository(async_session)

    user = AuthModel(email="no_profile_update_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    updated_profile = await repo.update_profile(
        user.id,
        {"first_name": "New Name"}
    )

    assert updated_profile is None
