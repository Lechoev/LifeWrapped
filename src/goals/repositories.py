from abc import ABC, abstractmethod

from sqlalchemy import exists, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.logger import get_logger
from src.goals.exceptions import IdNotFoundError
from src.goals.models import GoalModel

logger = get_logger(__name__)


class GoalInterface(ABC):
    @abstractmethod
    async def create_goal(self, data: dict): ...

    @abstractmethod
    async def get_by_id(self, goal_id: int, user_id: int): ...

    @abstractmethod
    async def get_all_by_user(self, user_id: int): ...

    @abstractmethod
    async def check_parent_exists(self, parent_id: int, user_id: int): ...

    @abstractmethod
    async def update_goal(self, goal_id: int, user_id: int, update_data: dict): ...


class GoalRepository(GoalInterface):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_goal(self, data: dict):
        try:
            goal = GoalModel(**data)
            self.session.add(goal)
            await self.session.flush()
            logger.info(
                "Goal created",
                extra={"user_id": data.get("user_id"), "goal_id": goal.id},
            )
            return goal
        except IntegrityError:
            logger.warning("Invalid foreign key", extra={"data": data})
            raise IdNotFoundError("Передан неверный внешний ключ")

    async def get_by_id(self, goal_id: int, user_id: int):
        result = await self.session.execute(
            select(GoalModel).where(
                GoalModel.id == goal_id, GoalModel.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_user(self, user_id: int):
        result = await self.session.execute(
            select(GoalModel)
            .where(GoalModel.user_id == user_id)
            .order_by(GoalModel.created_at.desc())
        )
        goals = result.scalars().all()
        logger.info(
            "Fetched all goals for user",
            extra={"user_id": user_id, "count": len(goals)},
        )
        return goals

    async def check_parent_exists(self, parent_id: int, user_id: int) -> bool:
        result = await self.session.execute(
            select(
                exists().where(GoalModel.id == parent_id, GoalModel.user_id == user_id)
            )
        )
        exists_flag = result.scalar()
        logger.info(
            "Checked parent goal existence",
            extra={"user_id": user_id, "parent_id": parent_id, "exists": exists_flag},
        )
        return exists_flag

    async def update_goal(self, goal_id: int, user_id: int, update_data: dict):
        stmt = (
            update(GoalModel)
            .where(GoalModel.id == goal_id, GoalModel.user_id == user_id)
            .values(**update_data)
            .returning(GoalModel)
        )

        result = await self.session.execute(stmt)
        updated_goal = result.scalar_one_or_none()

        if not updated_goal:
            logger.warning(
                "Goal not found for update",
                extra={"user_id": user_id, "goal_id": goal_id},
            )
            raise IdNotFoundError(f"Цель {goal_id} не найдена или не принадлежит вам")

        logger.info(
            "Goal updated",
            extra={
                "user_id": user_id,
                "goal_id": goal_id,
                "update_fields": list(update_data.keys()),
            },
        )
        return updated_goal
