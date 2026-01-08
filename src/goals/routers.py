from fastapi import APIRouter, Depends

from src.auth_user.dependencies import get_current_verified_user
from src.conf.logger import get_logger
from src.goals.decorators import goal_exceptions
from src.goals.dependencies import get_goal_service
from src.goals.schemas import CreateGoalSchema, UpdateGoalSchema
from src.goals.services import GoalService

logger = get_logger(__name__)

router = APIRouter(tags=["goals"])


@router.post("/v1/create-goals")
@goal_exceptions
async def create_goals(
    goal_data: CreateGoalSchema,
    service: GoalService = Depends(get_goal_service),
    current_user: int = Depends(get_current_verified_user),
):
    data = goal_data.model_dump()
    data["user_id"] = current_user
    result = await service.create_goal(data)

    logger.info("Goal created", extra={"user_id": current_user, "goal": data})
    return {"status": "success", "data": result}


@router.get("/v1/get-all-goals")
@goal_exceptions
async def get_all_goals(
    service: GoalService = Depends(get_goal_service),
    current_user: int = Depends(get_current_verified_user),
):
    result = await service.get_all_goals(user_id=current_user)

    logger.info(
        "Fetched all goals", extra={"user_id": current_user, "count": len(result)}
    )
    return {"status": "success", "data": result}


@router.get("/v1/get-goal/{goal_id}")
@goal_exceptions
async def get_goal(
    goal_id: int,
    service: GoalService = Depends(get_goal_service),
    current_user: int = Depends(get_current_verified_user),
):
    result = await service.get_goal(goal_id=goal_id, user_id=current_user)

    logger.info("Fetched goal", extra={"user_id": current_user, "goal_id": goal_id})
    return {"status": "success", "data": result}


@router.patch("/v1/update-goal/{goal_id}")
@goal_exceptions
async def update_goal(
    goal_id: int,
    goal_data: UpdateGoalSchema,
    service: GoalService = Depends(get_goal_service),
    current_user: int = Depends(get_current_verified_user),
):
    update_dict = goal_data.model_dump(exclude_unset=True)  # только переданные поля
    result = await service.update_goal(
        goal_id=goal_id, user_id=current_user, goal_data=update_dict
    )

    logger.info("Goal updated", extra={"user_id": current_user, "goal_id": goal_id})
    return {"status": "success", "data": result}
