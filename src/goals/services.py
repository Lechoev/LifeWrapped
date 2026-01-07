from src.goals.exceptions import ParentNotFoundError, GoalNotFound


class GoalService:
    def __init__(self, uow_factory):
        self.uow_factory = uow_factory

    async def create_goal(self, goal_data: dict):
        """Создание цели через UoW с проверкой безопасности"""
        async with self.uow_factory() as uow:
            parent_id = goal_data.get("parent_id")
            user_id = goal_data.get("user_id")
            if parent_id:
                parent_exists = await uow.goals.check_parent_exists(parent_id, user_id)
                if not parent_exists:
                    raise ParentNotFoundError(
                        f"Родительская цель {parent_id} не найдена"
                    )
            return await uow.goals.create_goal(data={**goal_data, "user_id": user_id})

    async def get_all_goals(self, user_id: int):
        """Все цели пользователя"""
        async with self.uow_factory() as uow:
            return await uow.goals.get_all_by_user(user_id)

    async def get_goal(self, goal_id: int, user_id: int):
        """Получение цели по ID с проверкой владельца"""
        async with self.uow_factory() as uow:
            result = await uow.goals.get_by_id(goal_id, user_id)
            if not result:
                raise GoalNotFound("Цель не найдена")
            return result

    async def update_goal(self, goal_id: int, user_id: int, goal_data: dict):
        async with self.uow_factory() as uow:
            new_parent_id = goal_data.get("parent_id")
            if new_parent_id is not None:
                if new_parent_id == goal_id:
                    raise ParentNotFoundError("Цель не может быть родителем самой себя")
                parent_exists = await uow.goals.check_parent_exists(new_parent_id, user_id)
                if not parent_exists:
                    raise ParentNotFoundError(f"Родительская цель {new_parent_id} не найдена")
            return await uow.goals.update_goal(goal_id, user_id, goal_data)
