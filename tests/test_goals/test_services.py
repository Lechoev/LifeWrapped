import pytest
from datetime import date
from unittest.mock import AsyncMock, Mock
from src.goals.services import GoalService
from src.goals.exceptions import ParentNotFoundError, GoalNotFound


class MockUoW:
    def __init__(self):
        self.goals = Mock()
        self.session = AsyncMock()
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()


@pytest.mark.asyncio
async def test_create_goal_success_without_parent():
    mock_uow = MockUoW()

    mock_goal = Mock()
    mock_goal.id = 1
    mock_goal.user_id = 1
    mock_goal.title = "Read 10 books"
    mock_goal.category = "books"
    mock_goal.target_value = 10
    mock_goal.unit = "книг"
    mock_goal.end_date = date(2024, 12, 31)
    mock_goal.current_value = 0
    mock_goal.is_completed = False

    mock_uow.goals.create_goal = AsyncMock(return_value=mock_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    goal_data = {
        "user_id": 1,
        "title": "Read 10 books",
        "category": "books",
        "target_value": 10,
        "unit": "книг",
        "end_date": date(2024, 12, 31)
    }

    result = await service.create_goal(goal_data)

    assert result.id == 1
    assert result.user_id == 1
    assert result.title == "Read 10 books"
    assert result.category == "books"
    assert result.target_value == 10
    assert result.unit == "книг"
    assert result.end_date == date(2024, 12, 31)

    mock_uow.goals.create_goal.assert_called_once_with(
        data={"user_id": 1, **goal_data}
    )


@pytest.mark.asyncio
async def test_create_goal_success_with_parent():
    mock_uow = MockUoW()

    mock_goal = Mock()
    mock_goal.id = 2
    mock_goal.user_id = 1
    mock_goal.title = "Run 100 km"
    mock_goal.parent_id = 1

    mock_uow.goals.check_parent_exists = AsyncMock(return_value=True)
    mock_uow.goals.create_goal = AsyncMock(return_value=mock_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    goal_data = {
        "user_id": 1,
        "parent_id": 1,
        "title": "Run 100 km",
        "category": "health",
        "target_value": 100,
        "unit": "км"
    }

    result = await service.create_goal(goal_data)

    assert result.id == 2
    assert result.user_id == 1
    assert result.title == "Run 100 km"
    assert result.parent_id == 1

    mock_uow.goals.check_parent_exists.assert_called_once_with(1, 1)
    mock_uow.goals.create_goal.assert_called_once_with(
        data={"user_id": 1, **goal_data}
    )


@pytest.mark.asyncio
async def test_create_goal_parent_not_found():
    mock_uow = MockUoW()

    mock_uow.goals.check_parent_exists = AsyncMock(return_value=False)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    goal_data = {
        "user_id": 1,
        "parent_id": 999,
        "title": "Test Goal",
        "category": "test"
    }

    with pytest.raises(ParentNotFoundError) as exc_info:
        await service.create_goal(goal_data)

    assert "Родительская цель 999 не найдена" in str(exc_info.value)
    mock_uow.goals.check_parent_exists.assert_called_once_with(999, 1)
    mock_uow.goals.create_goal.assert_not_called()


@pytest.mark.asyncio
async def test_get_all_goals_success():
    mock_uow = MockUoW()

    mock_goal1 = Mock()
    mock_goal1.id = 1
    mock_goal1.title = "Goal 1"

    mock_goal2 = Mock()
    mock_goal2.id = 2
    mock_goal2.title = "Goal 2"

    mock_uow.goals.get_all_by_user = AsyncMock(return_value=[mock_goal1, mock_goal2])

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    result = await service.get_all_goals(user_id=1)

    assert len(result) == 2
    assert result[0].title == "Goal 1"
    assert result[1].title == "Goal 2"
    mock_uow.goals.get_all_by_user.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_all_goals_empty():
    mock_uow = MockUoW()

    mock_uow.goals.get_all_by_user = AsyncMock(return_value=[])

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    result = await service.get_all_goals(user_id=1)

    assert len(result) == 0
    assert result == []
    mock_uow.goals.get_all_by_user.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_goal_success():
    mock_uow = MockUoW()

    mock_goal = Mock()
    mock_goal.id = 1
    mock_goal.user_id = 1
    mock_goal.title = "Test Goal"

    mock_uow.goals.get_by_id = AsyncMock(return_value=mock_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    result = await service.get_goal(goal_id=1, user_id=1)

    assert result.id == 1
    assert result.user_id == 1
    assert result.title == "Test Goal"
    mock_uow.goals.get_by_id.assert_called_once_with(1, 1)


@pytest.mark.asyncio
async def test_get_goal_not_found():
    mock_uow = MockUoW()

    mock_uow.goals.get_by_id = AsyncMock(return_value=None)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    with pytest.raises(GoalNotFound) as exc_info:
        await service.get_goal(goal_id=999, user_id=1)

    assert "Цель не найдена" in str(exc_info.value)
    mock_uow.goals.get_by_id.assert_called_once_with(999, 1)


@pytest.mark.asyncio
async def test_update_goal_success_without_parent():
    mock_uow = MockUoW()

    mock_updated_goal = Mock()
    mock_updated_goal.id = 1
    mock_updated_goal.user_id = 1
    mock_updated_goal.title = "Updated Title"
    mock_updated_goal.current_value = 5
    mock_updated_goal.is_completed = False

    mock_uow.goals.update_goal = AsyncMock(return_value=mock_updated_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "title": "Updated Title",
        "current_value": 5
    }

    result = await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert result.title == "Updated Title"
    assert result.current_value == 5
    assert result.is_completed is False

    mock_uow.goals.check_parent_exists.assert_not_called()
    mock_uow.goals.update_goal.assert_called_once_with(1, 1, update_data)


@pytest.mark.asyncio
async def test_update_goal_success_with_parent():
    mock_uow = MockUoW()

    mock_updated_goal = Mock()
    mock_updated_goal.id = 2
    mock_updated_goal.user_id = 1
    mock_updated_goal.parent_id = 10

    mock_uow.goals.check_parent_exists = AsyncMock(return_value=True)
    mock_uow.goals.update_goal = AsyncMock(return_value=mock_updated_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "parent_id": 10,
        "title": "Updated with new parent"
    }

    result = await service.update_goal(goal_id=2, user_id=1, goal_data=update_data)

    assert result.parent_id == 10
    assert result.id == 2

    mock_uow.goals.check_parent_exists.assert_called_once_with(10, 1)
    mock_uow.goals.update_goal.assert_called_once_with(2, 1, update_data)


@pytest.mark.asyncio
async def test_update_goal_parent_not_found():
    mock_uow = MockUoW()

    mock_uow.goals.check_parent_exists = AsyncMock(return_value=False)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "parent_id": 999,
        "title": "Updated"
    }

    with pytest.raises(ParentNotFoundError) as exc_info:
        await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert "Родительская цель 999 не найдена" in str(exc_info.value)
    mock_uow.goals.check_parent_exists.assert_called_once_with(999, 1)
    mock_uow.goals.update_goal.assert_not_called()


@pytest.mark.asyncio
async def test_update_goal_self_parent():
    mock_uow = MockUoW()

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "parent_id": 1,
        "title": "Updated"
    }

    with pytest.raises(ParentNotFoundError) as exc_info:
        await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert "Цель не может быть родителем самой себя" in str(exc_info.value)
    mock_uow.goals.check_parent_exists.assert_not_called()
    mock_uow.goals.update_goal.assert_not_called()


@pytest.mark.asyncio
async def test_update_goal_remove_parent():
    mock_uow = MockUoW()

    mock_updated_goal = Mock()
    mock_updated_goal.id = 1
    mock_updated_goal.user_id = 1
    mock_updated_goal.parent_id = None

    mock_uow.goals.update_goal = AsyncMock(return_value=mock_updated_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "parent_id": None,
        "title": "Updated without parent"
    }

    result = await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert result.parent_id is None

    mock_uow.goals.check_parent_exists.assert_not_called()
    mock_uow.goals.update_goal.assert_called_once_with(1, 1, update_data)


@pytest.mark.asyncio
async def test_update_goal_complete():
    mock_uow = MockUoW()

    mock_updated_goal = Mock()
    mock_updated_goal.id = 1
    mock_updated_goal.user_id = 1
    mock_updated_goal.current_value = 100
    mock_updated_goal.target_value = 100
    mock_updated_goal.is_completed = True
    mock_updated_goal.completed_at = date.today()

    mock_uow.goals.update_goal = AsyncMock(return_value=mock_updated_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "current_value": 100,
        "is_completed": True,
        "completed_at": date.today()
    }

    result = await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert result.current_value == 100
    assert result.is_completed is True
    assert result.completed_at == date.today()
    mock_uow.goals.update_goal.assert_called_once_with(1, 1, update_data)


@pytest.mark.asyncio
async def test_create_goal_minimal_data():
    mock_uow = MockUoW()

    mock_goal = Mock()
    mock_goal.id = 1
    mock_goal.user_id = 1
    mock_goal.title = "Minimal Goal"
    mock_goal.category = "test"
    mock_goal.current_value = 0
    mock_goal.is_completed = False

    mock_uow.goals.create_goal = AsyncMock(return_value=mock_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    goal_data = {
        "user_id": 1,
        "title": "Minimal Goal",
        "category": "test"
    }

    result = await service.create_goal(goal_data)

    assert result.title == "Minimal Goal"
    assert result.category == "test"
    assert result.current_value == 0
    assert result.is_completed is False
    mock_uow.goals.create_goal.assert_called_once_with(
        data={"user_id": 1, **goal_data}
    )


@pytest.mark.asyncio
async def test_update_goal_partial_data():
    mock_uow = MockUoW()

    mock_updated_goal = Mock()
    mock_updated_goal.id = 1
    mock_updated_goal.user_id = 1
    mock_updated_goal.title = "Partially Updated"
    mock_updated_goal.description = "Still old description"
    mock_updated_goal.current_value = 50

    mock_uow.goals.update_goal = AsyncMock(return_value=mock_updated_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "title": "Partially Updated",
        "current_value": 50
    }

    result = await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert result.title == "Partially Updated"
    assert result.current_value == 50
    mock_uow.goals.update_goal.assert_called_once_with(1, 1, update_data)


@pytest.mark.asyncio
async def test_create_goal_with_qualitative_data():
    mock_uow = MockUoW()

    mock_goal = Mock()
    mock_goal.id = 1
    mock_goal.user_id = 1
    mock_goal.title = "Learn Guitar"
    mock_goal.category = "hobby"
    mock_goal.target_value = None
    mock_goal.unit = None
    mock_goal.current_value = 0

    mock_uow.goals.create_goal = AsyncMock(return_value=mock_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    goal_data = {
        "user_id": 1,
        "title": "Learn Guitar",
        "category": "hobby",
        "target_value": None,
        "unit": None
    }

    result = await service.create_goal(goal_data)

    assert result.target_value is None
    assert result.unit is None
    assert result.current_value == 0
    mock_uow.goals.create_goal.assert_called_once_with(
        data={"user_id": 1, **goal_data}
    )


@pytest.mark.asyncio
async def test_update_goal_with_empty_data():
    mock_uow = MockUoW()

    mock_updated_goal = Mock()
    mock_updated_goal.id = 1
    mock_updated_goal.user_id = 1

    mock_uow.goals.update_goal = AsyncMock(return_value=mock_updated_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {}

    result = await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert result.id == 1
    assert result.user_id == 1
    mock_uow.goals.update_goal.assert_called_once_with(1, 1, {})


@pytest.mark.asyncio
async def test_create_goal_with_large_values():
    mock_uow = MockUoW()

    mock_goal = Mock()
    mock_goal.id = 1
    mock_goal.user_id = 1
    mock_goal.title = "Big Goal"
    mock_goal.target_value = 1000000
    mock_goal.current_value = 500000

    mock_uow.goals.create_goal = AsyncMock(return_value=mock_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    goal_data = {
        "user_id": 1,
        "title": "Big Goal",
        "category": "finance",
        "target_value": 1000000,
        "current_value": 500000
    }

    result = await service.create_goal(goal_data)

    assert result.target_value == 1000000
    assert result.current_value == 500000
    mock_uow.goals.create_goal.assert_called_once_with(
        data={"user_id": 1, **goal_data}
    )


@pytest.mark.asyncio
async def test_update_goal_with_special_characters():
    mock_uow = MockUoW()

    mock_updated_goal = Mock()
    mock_updated_goal.id = 1
    mock_updated_goal.user_id = 1
    mock_updated_goal.title = "Тест с русскими символами áéíóú 🚀"
    mock_updated_goal.description = "Описание с emoji 😊"

    mock_uow.goals.update_goal = AsyncMock(return_value=mock_updated_goal)

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    update_data = {
        "title": "Тест с русскими символами áéíóú 🚀",
        "description": "Описание с emoji 😊"
    }

    result = await service.update_goal(goal_id=1, user_id=1, goal_data=update_data)

    assert "🚀" in result.title
    assert "😊" in result.description
    mock_uow.goals.update_goal.assert_called_once_with(1, 1, update_data)


@pytest.mark.asyncio
async def test_create_goal_repository_error():
    mock_uow = MockUoW()

    mock_uow.goals.create_goal = AsyncMock(side_effect=Exception("DB error"))

    def mock_uow_factory():
        return mock_uow

    service = GoalService(uow_factory=mock_uow_factory)

    goal_data = {
        "user_id": 1,
        "title": "Test",
        "category": "test"
    }

    with pytest.raises(Exception) as exc_info:
        await service.create_goal(goal_data)

    assert "DB error" in str(exc_info.value)
