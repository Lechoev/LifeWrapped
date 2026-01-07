from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.profiles.models import ProfileModel


class ProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_profile(self, user_id: int):
        result = await self.session.execute(select(1).where(ProfileModel.user_id == user_id))
        return result.scalar_one_or_none()

    async def create_profile(self, data: dict):
        self.session.add(ProfileModel(**data))

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
        return row[0]

    async def get_profile(self, user_id: int):
        result = await self.session.execute(select(ProfileModel).where(ProfileModel.user_id == user_id))
        return result.scalar_one_or_none()
