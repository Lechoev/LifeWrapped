from sqlalchemy import select, update

from src.conf.logger import get_logger
from src.profiles.models import ProfileModel

logger = get_logger(__name__)


class ProfileRepository:
    def __init__(self, session):
        self.session = session

    async def check_profile(self, user_id: int):
        result = await self.session.execute(select(1).where(ProfileModel.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_profile(self, data: dict):
        self.session.add(ProfileModel(**data))
        logger.info("Profile added to session", extra={"user_id": data.get("user_id")})

    async def update_profile(self, user_id: int, update_data: dict):
        stmt = (
            update(ProfileModel)
            .where(ProfileModel.user_id == user_id)
            .values(**update_data)
            .returning(ProfileModel)
        )

        result = await self.session.execute(stmt)
        row = result.fetchone()
        if not row:
            return None
        logger.info("Profile updated successfully", extra={"user_id": user_id})
        return row[0]

    async def get_profile(self, user_id: int):
        result = await self.session.execute(select(ProfileModel).where(ProfileModel.user_id == user_id))
        return result.scalar_one_or_none()
