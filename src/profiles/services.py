from src.profiles import exceptions
from src.conf.logger import get_logger

logger = get_logger(__name__)


class ProfileService:
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    async def create_profile(self, user_id: int, profile_data: dict) -> dict:
        async with self.uow_factory() as uow:
            existing_profile = await uow.profiles.get_profile(user_id)
            if existing_profile:
                raise exceptions.ProfileAlreadyExistsError(f"Профиль для пользователя {user_id} уже существует")

            await uow.profiles.create_profile(
                data={**profile_data, "user_id": user_id}
            )
            logger.info("Profile created", extra={"user_id": user_id})
            return profile_data

    async def check_profile(self, user_id: int):
        async with self.uow_factory() as uow:
            return await uow.profiles.check_profile(user_id=user_id)

    async def update_profile(self, user_id: int, update_data: dict) -> dict:
        async with self.uow_factory() as uow:
            profile = await uow.profiles.update_profile(
                user_id=user_id,
                update_data=update_data
            )

            if not profile:
                raise exceptions.ProfileNotFoundError(f"Профиль для пользователя {user_id} не найден")

            logger.info("Profile updated", extra={"user_id": user_id, "fields": list(update_data.keys())})
            return {
                "user_id": profile.user_id,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "bio": profile.bio,
                "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
                "avatar_url": profile.avatar_url,
                "updated_at": profile.updated_at.isoformat() if profile.updated_at else None
            }

    async def get_profile(self, user_id: int):
        async with self.uow_factory() as uow:
            profile = await uow.profiles.get_profile(user_id=user_id)
            if not profile:
                raise exceptions.ProfileNotFoundError(f"Профиль для пользователя {user_id} не найден")
            logger.info("Profile fetched", extra={"user_id": user_id})
            return profile
