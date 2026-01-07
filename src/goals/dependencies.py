from src.common.dependencies import get_uow_factory
from src.goals.services import GoalService


def get_goal_service() -> GoalService:
    return GoalService(uow_factory=get_uow_factory())
