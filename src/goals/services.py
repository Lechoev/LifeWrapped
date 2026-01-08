from src.conf.logger import get_logger
from src.goals.exceptions import GoalNotFound, ParentNotFoundError

logger = get_logger(__name__)


class GoalService:
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    async def create_goal(self, goal_data: dict):
        async with self.uow_factory() as uow:
            parent_id = goal_data.get("parent_id")
            user_id = goal_data.get("user_id")
            if parent_id:
                parent_exists = await uow.goals.check_parent_exists(parent_id, user_id)
                if not parent_exists:
                    logger.warning(
                        "Parent goal not found",
                        extra={"user_id": user_id, "parent_id": parent_id},
                    )
                    raise ParentNotFoundError(
                        f"Родительская цель {parent_id} не найдена"
                    )

            result = await uow.goals.create_goal(data={**goal_data, "user_id": user_id})
            logger.info(
                "Goal created", extra={"user_id": user_id, "goal_id": result.id}
            )
            return result

    async def get_all_goals(self, user_id: int):
        async with self.uow_factory() as uow:
            result = await uow.goals.get_all_by_user(user_id)
            logger.info(
                "Fetched all goals", extra={"user_id": user_id, "count": len(result)}
            )
            return result

    async def get_goal(self, goal_id: int, user_id: int):
        async with self.uow_factory() as uow:
            result = await uow.goals.get_by_id(goal_id, user_id)
            if not result:
                logger.warning(
                    "Goal not found", extra={"user_id": user_id, "goal_id": goal_id}
                )
                raise GoalNotFound("Цель не найдена")
            logger.info("Fetched goal", extra={"user_id": user_id, "goal_id": goal_id})
            return result

    async def update_goal(self, goal_id: int, user_id: int, goal_data: dict):
        async with self.uow_factory() as uow:
            new_parent_id = goal_data.get("parent_id")
            if new_parent_id is not None:
                if new_parent_id == goal_id:
                    logger.warning(
                        "Goal cannot be parent of itself",
                        extra={"user_id": user_id, "goal_id": goal_id},
                    )
                    raise ParentNotFoundError("Цель не может быть родителем самой себя")
                parent_exists = await uow.goals.check_parent_exists(
                    new_parent_id, user_id
                )
                if not parent_exists:
                    logger.warning(
                        "Parent goal not found for update",
                        extra={
                            "user_id": user_id,
                            "goal_id": goal_id,
                            "parent_id": new_parent_id,
                        },
                    )
                    raise ParentNotFoundError(
                        f"Родительская цель {new_parent_id} не найдена"
                    )

            result = await uow.goals.update_goal(goal_id, user_id, goal_data)
            logger.info("Goal updated", extra={"user_id": user_id, "goal_id": goal_id})
            return result
