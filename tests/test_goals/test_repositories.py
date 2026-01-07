import pytest
from datetime import date
from src.goals.repositories import GoalRepository
from src.goals.models import GoalModel, ProgressEventModel
from src.goals.exceptions import IdNotFoundError
from src.auth_user.models import AuthModel


@pytest.mark.asyncio
async def test_create_goal_success(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="goal_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    goal_data = {
        "user_id": user.id,
        "title": "Read 10 books",
        "category": "books",
        "target_value": 10,
        "unit": "книг",
        "end_date": date(2024, 12, 31)
    }

    created_goal = await repo.create_goal(goal_data)
    await async_session.commit()

    assert created_goal.id is not None
    assert created_goal.user_id == user.id
    assert created_goal.title == "Read 10 books"
    assert created_goal.category == "books"
    assert created_goal.target_value == 10
    assert created_goal.unit == "книг"
    assert created_goal.end_date == date(2024, 12, 31)
    assert created_goal.current_value == 0
    assert created_goal.is_completed is False
    assert created_goal.parent_id is None


@pytest.mark.asyncio
async def test_create_goal_with_parent(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="goal_parent_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    parent_goal = GoalModel(
        user_id=user.id,
        title="Improve Health",
        category="health"
    )
    async_session.add(parent_goal)
    await async_session.flush()

    child_goal_data = {
        "user_id": user.id,
        "parent_id": parent_goal.id,
        "title": "Run 100 km",
        "category": "health",
        "target_value": 100,
        "unit": "км"
    }

    child_goal = await repo.create_goal(child_goal_data)
    await async_session.commit()

    assert child_goal.id is not None
    assert child_goal.parent_id == parent_goal.id
    assert child_goal.title == "Run 100 km"
    assert child_goal.user_id == user.id


@pytest.mark.asyncio
async def test_get_by_id_success(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="get_by_id_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    goal = GoalModel(
        user_id=user.id,
        title="Test Goal",
        category="test"
    )
    async_session.add(goal)
    await async_session.commit()

    found_goal = await repo.get_by_id(goal.id, user.id)

    assert found_goal is not None
    assert found_goal.id == goal.id
    assert found_goal.user_id == user.id
    assert found_goal.title == "Test Goal"


@pytest.mark.asyncio
async def test_get_by_id_not_found(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="not_found_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    found_goal = await repo.get_by_id(99999, user.id)

    assert found_goal is None


@pytest.mark.asyncio
async def test_get_by_id_wrong_user(async_session):
    repo = GoalRepository(async_session)

    user1 = AuthModel(email="user1_test@example.com", is_verified=True)
    user2 = AuthModel(email="user2_test@example.com", is_verified=True)
    async_session.add_all([user1, user2])
    await async_session.flush()

    goal = GoalModel(
        user_id=user1.id,
        title="User1 Goal",
        category="test"
    )
    async_session.add(goal)
    await async_session.commit()

    found_goal = await repo.get_by_id(goal.id, user2.id)

    assert found_goal is None


@pytest.mark.asyncio
async def test_get_all_by_user(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="all_goals_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    goals_data = [
        {"user_id": user.id, "title": "Goal 1", "category": "books"},
        {"user_id": user.id, "title": "Goal 2", "category": "health"},
        {"user_id": user.id, "title": "Goal 3", "category": "travel"}
    ]

    for data in goals_data:
        goal = GoalModel(**data)
        async_session.add(goal)

    await async_session.commit()

    user_goals = await repo.get_all_by_user(user.id)

    assert len(user_goals) == 3
    assert all(goal.user_id == user.id for goal in user_goals)


@pytest.mark.asyncio
async def test_get_all_by_user_empty(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="no_goals_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    goals = await repo.get_all_by_user(user.id)

    assert len(goals) == 0
    assert goals == []


@pytest.mark.asyncio
async def test_get_all_by_user_only_own_goals(async_session):
    repo = GoalRepository(async_session)

    user1 = AuthModel(email="owner_test@example.com", is_verified=True)
    user2 = AuthModel(email="other_test@example.com", is_verified=True)
    async_session.add_all([user1, user2])
    await async_session.flush()

    goal1 = GoalModel(user_id=user1.id, title="User1 Goal", category="test")
    goal2 = GoalModel(user_id=user2.id, title="User2 Goal", category="test")
    async_session.add_all([goal1, goal2])
    await async_session.commit()

    user1_goals = await repo.get_all_by_user(user1.id)

    assert len(user1_goals) == 1
    assert user1_goals[0].title == "User1 Goal"
    assert user1_goals[0].user_id == user1.id


@pytest.mark.asyncio
async def test_check_parent_exists_true(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="parent_exists_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    parent_goal = GoalModel(
        user_id=user.id,
        title="Parent Goal",
        category="test"
    )
    async_session.add(parent_goal)
    await async_session.commit()

    exists = await repo.check_parent_exists(parent_goal.id, user.id)

    assert exists is True


@pytest.mark.asyncio
async def test_check_parent_exists_false(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="parent_not_exists_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    exists = await repo.check_parent_exists(99999, user.id)

    assert exists is False


@pytest.mark.asyncio
async def test_check_parent_exists_wrong_user(async_session):
    repo = GoalRepository(async_session)

    user1 = AuthModel(email="owner_parent_test@example.com", is_verified=True)
    user2 = AuthModel(email="other_parent_test@example.com", is_verified=True)
    async_session.add_all([user1, user2])
    await async_session.flush()

    parent_goal = GoalModel(
        user_id=user1.id,
        title="Parent Goal",
        category="test"
    )
    async_session.add(parent_goal)
    await async_session.commit()

    exists = await repo.check_parent_exists(parent_goal.id, user2.id)

    assert exists is False


@pytest.mark.asyncio
async def test_update_goal_success(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="update_goal_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    goal = GoalModel(
        user_id=user.id,
        title="Old Title",
        category="books",
        target_value=10,
        current_value=0
    )
    async_session.add(goal)
    await async_session.commit()

    update_data = {
        "title": "New Title",
        "category": "health",
        "target_value": 20,
        "current_value": 5,
        "is_completed": True
    }

    updated_goal = await repo.update_goal(goal.id, user.id, update_data)
    await async_session.commit()

    assert updated_goal.title == "New Title"
    assert updated_goal.category == "health"
    assert updated_goal.target_value == 20
    assert updated_goal.current_value == 5
    assert updated_goal.is_completed is True
    assert updated_goal.user_id == user.id
    assert updated_goal.id == goal.id


@pytest.mark.asyncio
async def test_update_goal_partial(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="partial_update_goal_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    goal = GoalModel(
        user_id=user.id,
        title="Original Title",
        category="books",
        description="Original description",
        target_value=10
    )
    async_session.add(goal)
    await async_session.commit()

    update_data = {"title": "Updated Title"}

    updated_goal = await repo.update_goal(goal.id, user.id, update_data)
    await async_session.commit()

    assert updated_goal.title == "Updated Title"
    assert updated_goal.category == "books"
    assert updated_goal.description == "Original description"
    assert updated_goal.target_value == 10


@pytest.mark.asyncio
async def test_update_goal_not_found(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="update_not_found_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.commit()

    with pytest.raises(IdNotFoundError, match="Цель 99999 не найдена или не принадлежит вам"):
        await repo.update_goal(99999, user.id, {"title": "New Title"})


@pytest.mark.asyncio
async def test_update_goal_wrong_user(async_session):
    repo = GoalRepository(async_session)

    user1 = AuthModel(email="goal_owner_test@example.com", is_verified=True)
    user2 = AuthModel(email="goal_updater_test@example.com", is_verified=True)
    async_session.add_all([user1, user2])
    await async_session.flush()

    goal = GoalModel(
        user_id=user1.id,
        title="User1 Goal",
        category="test"
    )
    async_session.add(goal)
    await async_session.commit()

    with pytest.raises(IdNotFoundError, match=f"Цель {goal.id} не найдена или не принадлежит вам"):
        await repo.update_goal(goal.id, user2.id, {"title": "Hacked Title"})


@pytest.mark.asyncio
async def test_update_goal_completion_logic(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="completion_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    goal = GoalModel(
        user_id=user.id,
        title="Read 10 books",
        category="books",
        target_value=10,
        current_value=8,
        is_completed=False
    )
    async_session.add(goal)
    await async_session.commit()

    update_data = {
        "current_value": 10,
        "is_completed": True
    }

    updated_goal = await repo.update_goal(goal.id, user.id, update_data)
    await async_session.commit()

    assert updated_goal.current_value == 10
    assert updated_goal.is_completed is True


@pytest.mark.asyncio
async def test_update_goal_with_invalid_data(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="invalid_update_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    goal = GoalModel(
        user_id=user.id,
        title="Test Goal",
        category="test"
    )
    async_session.add(goal)
    await async_session.commit()

    update_data = {"target_value": -10}

    updated_goal = await repo.update_goal(goal.id, user.id, update_data)

    assert updated_goal.target_value == -10


@pytest.mark.asyncio
async def test_repository_integration(async_session):
    repo = GoalRepository(async_session)

    user = AuthModel(email="integration_test@example.com", is_verified=True)
    async_session.add(user)
    await async_session.flush()

    parent_data = {
        "user_id": user.id,
        "title": "Parent Goal",
        "category": "health",
        "target_value": None
    }
    parent_goal = await repo.create_goal(parent_data)

    parent_exists = await repo.check_parent_exists(parent_goal.id, user.id)
    assert parent_exists is True

    child_data = {
        "user_id": user.id,
        "parent_id": parent_goal.id,
        "title": "Child Goal",
        "category": "health",
        "target_value": 100,
        "unit": "km"
    }
    child_goal = await repo.create_goal(child_data)

    all_goals = await repo.get_all_by_user(user.id)
    assert len(all_goals) == 2

    retrieved_child = await repo.get_by_id(child_goal.id, user.id)
    assert retrieved_child.title == "Child Goal"
    assert retrieved_child.parent_id == parent_goal.id

    update_data = {
        "current_value": 50,
        "title": "Updated Child Goal"
    }
    updated_child = await repo.update_goal(child_goal.id, user.id, update_data)
    assert updated_child.current_value == 50
    assert updated_child.title == "Updated Child Goal"

    await async_session.commit()
