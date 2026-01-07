from sqlalchemy import select, exists, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.goals.models import GoalModel
from src.goals.exceptions import IdNotFoundError


class GoalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_goal(self, data: dict):
        """Создать цель"""
        try:
            goal = GoalModel(**data)
            self.session.add(goal)
            await self.session.flush()
            return goal
        except IntegrityError:
            raise IdNotFoundError("Передан неверный внешний ключ")

    async def get_by_id(self, goal_id: int, user_id: int):
        """Получить цель по ID с проверкой владельца"""
        result = await self.session.execute(
            select(GoalModel).where(
                GoalModel.id == goal_id,
                GoalModel.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int):
        """Все цели пользователя"""
        result = await self.session.execute(
            select(GoalModel)
            .where(GoalModel.user_id == user_id)
            .order_by(GoalModel.created_at.desc())
        )
        return result.scalars().all()

    async def check_parent_exists(self, parent_id: int, user_id: int) -> bool:
        """Проверить существование родительской цели"""
        result = await self.session.execute(
            select(exists().where(
                GoalModel.id == parent_id,
                GoalModel.user_id == user_id
            ))
        )
        return result.scalar()

    async def update_goal(self, goal_id: int, user_id: int, update_data: dict):
        stmt = (
            update(GoalModel)
            .where(
                GoalModel.id == goal_id,
                GoalModel.user_id == user_id
            )
            .values(**update_data)
            .returning(GoalModel)
        )

        result = await self.session.execute(stmt)
        updated_goal = result.scalar_one_or_none()

        if not updated_goal:
            raise IdNotFoundError(f"Цель {goal_id} не найдена или не принадлежит вам")

        return updated_goal
