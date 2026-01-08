from datetime import date

import pytest
from sqlalchemy import select

from src.auth_user.models import AuthModel, VerificationCodeModel
from src.goals.models import GoalModel


def get_unique_email(base_name: str) -> str:
    import time

    timestamp = int(time.time())
    return f"{base_name}_{timestamp}@example.com"


GOALS_PREFIX = "/goals_router"
CREATE_GOAL = f"{GOALS_PREFIX}/v1/create-goals"
GET_ALL_GOALS = f"{GOALS_PREFIX}/v1/get-all-goals"
GET_GOAL = f"{GOALS_PREFIX}/v1/get-goal/{{goal_id}}"
UPDATE_GOAL = f"{GOALS_PREFIX}/v1/update-goal/{{goal_id}}"


@pytest.mark.asyncio
async def test_create_goal_integration(async_client, async_session):
    email = get_unique_email("create_goal_test")

    user = AuthModel(email=email)
    async_session.add(user)
    await async_session.flush()

    test_code = "888888"
    verification_code = VerificationCodeModel(email=email, code=test_code)
    async_session.add(verification_code)
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate", json={"email": email, "code": test_code}
    )

    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    access_token = auth_data["access_token"]

    goal_data = {
        "title": "Read 10 books",
        "category": "books",
        "target_value": 10,
        "unit": "книг",
        "end_date": "2024-12-31",
        "description": "Read 10 books this year",
    }

    response = await async_client.post(
        CREATE_GOAL, headers={"Authorization": f"Bearer {access_token}"}, json=goal_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data

    goal_response = data["data"]
    assert goal_response["title"] == "Read 10 books"
    assert goal_response["category"] == "books"
    assert goal_response["target_value"] == 10
    assert goal_response["unit"] == "книг"
    assert goal_response["end_date"] == "2024-12-31"
    assert goal_response["user_id"] == user.id

    result = await async_session.execute(
        select(GoalModel).where(GoalModel.user_id == user.id)
    )
    goal_in_db = result.scalar_one_or_none()

    assert goal_in_db is not None
    assert goal_in_db.title == "Read 10 books"
    assert goal_in_db.category == "books"
    assert goal_in_db.target_value == 10
    assert goal_in_db.unit == "книг"
    assert goal_in_db.end_date == date(2024, 12, 31)
    assert goal_in_db.current_value == 0
    assert goal_in_db.is_completed is False


@pytest.mark.asyncio
async def test_get_all_goals_integration(async_client, async_session):
    email = get_unique_email("get_all_goals_test")

    user = AuthModel(email=email)
    async_session.add(user)
    await async_session.flush()

    goals = [
        GoalModel(user_id=user.id, title="Goal 1", category="books"),
        GoalModel(user_id=user.id, title="Goal 2", category="health"),
        GoalModel(user_id=user.id, title="Goal 3", category="travel"),
    ]

    for goal in goals:
        async_session.add(goal)

    await async_session.commit()

    test_code = "555555"
    verification_code = VerificationCodeModel(email=email, code=test_code)
    async_session.add(verification_code)
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate", json={"email": email, "code": test_code}
    )

    access_token = auth_response.json()["access_token"]

    response = await async_client.get(
        GET_ALL_GOALS, headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data

    goals_data = data["data"]
    assert len(goals_data) == 3

    titles = {goal["title"] for goal in goals_data}
    assert "Goal 1" in titles
    assert "Goal 2" in titles
    assert "Goal 3" in titles

    for goal in goals_data:
        assert goal["user_id"] == user.id


@pytest.mark.asyncio
async def test_get_goal_by_id_integration(async_client, async_session):
    email = get_unique_email("get_goal_by_id_test")

    user = AuthModel(email=email)
    async_session.add(user)
    await async_session.flush()

    goal = GoalModel(
        user_id=user.id,
        title="Specific Goal",
        category="books",
        target_value=5,
        unit="книг",
        description="Read specific books",
    )
    async_session.add(goal)
    await async_session.commit()

    test_code = "333333"
    verification_code = VerificationCodeModel(email=email, code=test_code)
    async_session.add(verification_code)
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate", json={"email": email, "code": test_code}
    )

    access_token = auth_response.json()["access_token"]

    response = await async_client.get(
        GET_GOAL.format(goal_id=goal.id),
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    goal_data = data["data"]
    assert goal_data["id"] == goal.id
    assert goal_data["title"] == "Specific Goal"
    assert goal_data["category"] == "books"
    assert goal_data["target_value"] == 5
    assert goal_data["unit"] == "книг"
    assert goal_data["description"] == "Read specific books"
    assert goal_data["user_id"] == user.id


@pytest.mark.asyncio
async def test_update_goal_integration(async_client, async_session):
    email = get_unique_email("update_goal_test")

    user = AuthModel(email=email)
    async_session.add(user)
    await async_session.flush()

    goal = GoalModel(
        user_id=user.id,
        title="Old Title",
        category="books",
        target_value=10,
        current_value=0,
    )
    async_session.add(goal)
    await async_session.flush()
    goal_id = goal.id

    test_code = "999999"
    verification_code = VerificationCodeModel(email=email, code=test_code)
    async_session.add(verification_code)
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate", json={"email": email, "code": test_code}
    )

    access_token = auth_response.json()["access_token"]

    update_data = {"title": "New Title", "description": "Updated description"}

    response = await async_client.patch(
        UPDATE_GOAL.format(goal_id=goal_id),
        headers={"Authorization": f"Bearer {access_token}"},
        json=update_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    updated_goal = data["data"]
    assert updated_goal["title"] == "New Title"
    assert updated_goal["description"] == "Updated description"
    assert updated_goal["current_value"] == 0
    assert updated_goal["category"] == "books"
    assert updated_goal["target_value"] == 10

    result = await async_session.execute(
        select(GoalModel).where(GoalModel.id == goal_id)
    )
    goal_in_db = result.scalar_one()

    assert goal_in_db.title == "New Title"
    assert goal_in_db.description == "Updated description"
    assert goal_in_db.current_value == 0


@pytest.mark.asyncio
async def test_create_goal_with_parent_integration(async_client, async_session):
    email = get_unique_email("goal_with_parent_test")

    user = AuthModel(email=email)
    async_session.add(user)
    await async_session.flush()

    test_code = "777777"
    verification_code = VerificationCodeModel(email=email, code=test_code)
    async_session.add(verification_code)
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate", json={"email": email, "code": test_code}
    )

    access_token = auth_response.json()["access_token"]

    parent_goal_data = {
        "title": "Improve Health",
        "category": "health",
        "description": "Overall health improvement",
    }

    parent_response = await async_client.post(
        CREATE_GOAL,
        headers={"Authorization": f"Bearer {access_token}"},
        json=parent_goal_data,
    )

    assert parent_response.status_code == 200
    parent_data = parent_response.json()["data"]
    parent_id = parent_data["id"]

    child_goal_data = {
        "title": "Run 100 km",
        "category": "health",
        "target_value": 100,
        "unit": "км",
        "parent_id": parent_id,
    }

    response = await async_client.post(
        CREATE_GOAL,
        headers={"Authorization": f"Bearer {access_token}"},
        json=child_goal_data,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    child_goal = data["data"]
    assert child_goal["title"] == "Run 100 km"
    assert child_goal["parent_id"] == parent_id
    assert child_goal["user_id"] == user.id


@pytest.mark.asyncio
async def test_goal_comprehensive_flow_integration(async_client, async_session):
    email = get_unique_email("comprehensive_flow_test")

    user = AuthModel(email=email)
    async_session.add(user)

    test_code = "222222"
    verification_code = VerificationCodeModel(email=email, code=test_code)
    async_session.add(verification_code)
    await async_session.commit()

    auth_response = await async_client.post(
        "/auth_router/v1/auth/authenticate", json={"email": email, "code": test_code}
    )

    assert auth_response.status_code == 200
    auth_data = auth_response.json()
    access_token = auth_data["access_token"]

    goals_to_create = [
        {"title": "Goal 1", "category": "books", "target_value": 10, "unit": "книг"},
        {"title": "Goal 2", "category": "health", "target_value": 100, "unit": "км"},
        {"title": "Goal 3", "category": "travel", "description": "Travel goal"},
    ]

    created_goals = []
    for goal_data in goals_to_create:
        response = await async_client.post(
            CREATE_GOAL,
            headers={"Authorization": f"Bearer {access_token}"},
            json=goal_data,
        )
        assert response.status_code == 200
        created_goal = response.json()["data"]
        created_goals.append(created_goal)

    response = await async_client.get(
        GET_ALL_GOALS, headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    all_goals = response.json()["data"]
    assert len(all_goals) == 3

    for goal in created_goals:
        response = await async_client.get(
            GET_GOAL.format(goal_id=goal["id"]),
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        fetched_goal = response.json()["data"]
        assert fetched_goal["title"] == goal["title"]
        assert fetched_goal["user_id"] == user.id

    goal_to_update = created_goals[0]
    update_data = {"title": "Updated Goal 1", "description": "Halfway there!"}

    response = await async_client.patch(
        UPDATE_GOAL.format(goal_id=goal_to_update["id"]),
        headers={"Authorization": f"Bearer {access_token}"},
        json=update_data,
    )

    assert response.status_code == 200
    updated_goal = response.json()["data"]
    assert updated_goal["title"] == "Updated Goal 1"
    assert updated_goal["description"] == "Halfway there!"
