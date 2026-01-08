from datetime import UTC, date, datetime

import pytest

from src.goals.models import GoalModel, ImageModel, ProgressEventModel


def test_goal_model_with_all_fields():
    goal = GoalModel(
        user_id=1,
        title="Run Marathon",
        description="Complete a full marathon in under 4 hours",
        category="health",
        target_value=42,
        unit="км",
        end_date=date(2024, 6, 30),
        current_value=15,
        is_completed=False,
        parent_id=None,
    )

    assert goal.title == "Run Marathon"
    assert goal.description == "Complete a full marathon in under 4 hours"
    assert goal.category == "health"
    assert goal.target_value == 42
    assert goal.unit == "км"
    assert goal.current_value == 15
    assert goal.is_completed is False


def test_goal_model_completed():
    completion_date = date(2024, 5, 15)
    goal = GoalModel(
        user_id=1,
        title="Read 10 books",
        category="books",
        target_value=10,
        current_value=10,
        is_completed=True,
        completed_at=completion_date,
    )

    assert goal.current_value == goal.target_value
    assert goal.is_completed is True
    assert goal.completed_at == completion_date


def test_goal_model_progress_percentage():
    goal = GoalModel(
        user_id=1,
        title="Read 10 books",
        category="books",
        target_value=10,
        current_value=3,
    )

    if goal.target_value:
        percentage = (goal.current_value / goal.target_value) * 100
        assert percentage == 30.0
    else:
        assert goal.target_value is None


def test_goal_model_parent_child_relationship():
    parent_goal = GoalModel(id=1, user_id=1, title="Improve Health", category="health")

    child1 = GoalModel(user_id=1, title="Run 100 km", category="health", parent_id=1)

    child2 = GoalModel(user_id=1, title="Lose 5 kg", category="health", parent_id=1)

    parent_goal.children = [child1, child2]
    child1.parent = parent_goal
    child2.parent = parent_goal

    assert parent_goal.parent is None
    assert len(parent_goal.children) == 2
    assert child1.parent is parent_goal
    assert child2.parent is parent_goal
    assert child1 in parent_goal.children
    assert child2 in parent_goal.children


def test_goal_model_edge_cases():
    goal1 = GoalModel(
        user_id=1, title="Zero target", category="test", target_value=0, current_value=0
    )
    assert goal1.target_value == 0

    goal2 = GoalModel(
        user_id=1,
        title="Big goal",
        category="finance",
        target_value=1000000,
        current_value=500000,
    )
    assert goal2.target_value == 1000000
    assert goal2.current_value == 500000

    goal3 = GoalModel(user_id=1, title="A", category="test")
    assert goal3.title == "A"


def test_progress_event_model_creation():
    event_date = date(2024, 3, 15)
    event = ProgressEventModel(
        goal_id=1,
        value=1,
        description="Read '1984' by George Orwell",
        mood="proud",
        event_date=event_date,
    )

    assert event.goal_id == 1
    assert event.value == 1
    assert event.description == "Read '1984' by George Orwell"
    assert event.mood == "proud"
    assert event.event_date == event_date
    assert event.id is None


def test_progress_event_model_with_different_values():
    event1 = ProgressEventModel(goal_id=1, value=1, description="Read one chapter")
    assert event1.value == 1

    event2 = ProgressEventModel(goal_id=2, value=10, description="Ran 10 km")
    assert event2.value == 10


def test_progress_event_model_without_mood():
    event = ProgressEventModel(
        goal_id=1,
        value=1,
        description="Completed task",
        mood=None,
        event_date=date.today(),
    )

    assert event.mood is None
    assert event.description == "Completed task"


def test_progress_event_model_relationships():
    goal = GoalModel(id=1, user_id=1, title="Read 10 books", category="books")

    event = ProgressEventModel(goal_id=1, value=1, description="Read a book")

    event.goal = goal
    goal.events = [event]

    assert event.goal is goal
    assert len(goal.events) == 1
    assert goal.events[0] is event


def test_image_model_for_goal():
    image = ImageModel(goal_id=1, img_url="/static/images/goals/book_cover.jpg")

    assert image.goal_id == 1
    assert image.event_id is None
    assert image.img_url == "/static/images/goals/book_cover.jpg"
    assert image.id is None


def test_image_model_for_event():
    image = ImageModel(event_id=1, img_url="/static/images/events/running.jpg")

    assert image.event_id == 1
    assert image.goal_id is None
    assert image.img_url == "/static/images/events/running.jpg"


def test_image_model_relationships():
    goal = GoalModel(id=1, user_id=1, title="Test Goal", category="test")
    image1 = ImageModel(goal_id=1, img_url="/test1.jpg")

    image1.goal = goal
    goal.images = [image1]

    assert image1.goal is goal
    assert len(goal.images) == 1
    assert goal.images[0] is image1

    event = ProgressEventModel(id=1, goal_id=1, description="Test event")
    image2 = ImageModel(event_id=1, img_url="/test2.jpg")

    image2.event = event
    event.images = [image2]

    assert image2.event is event
    assert len(event.images) == 1
    assert event.images[0] is image2


def test_image_model_with_both_ids_none():
    image = ImageModel(img_url="/static/images/general.jpg")

    assert image.goal_id is None
    assert image.event_id is None


def test_image_model_with_full_url():
    full_url = "https://example.com/images/profile.jpg"
    image = ImageModel(goal_id=1, img_url=full_url)

    assert image.img_url == full_url
    assert image.img_url.startswith("https://")


def test_image_model_upload_timestamp():
    image = ImageModel(goal_id=1, img_url="/test.jpg")

    assert image.uploaded_at is None

    image.uploaded_at = datetime.now(UTC)
    assert image.uploaded_at is not None


def test_goal_completion_logic():
    goal = GoalModel(
        user_id=1,
        title="Read 3 books",
        category="books",
        target_value=3,
        current_value=0,
    )

    events = []
    for i in range(3):
        event = ProgressEventModel(
            goal_id=goal.id if goal.id else 1, value=1, description=f"Read book {i + 1}"
        )
        events.append(event)

    goal.events = events
    goal.current_value = len(events)

    if goal.target_value and goal.current_value >= goal.target_value:
        goal.is_completed = True
        goal.completed_at = date.today()

    assert goal.current_value == 3
    assert goal.is_completed is True
    assert goal.completed_at == date.today()


def test_goal_model_with_circular_parent_reference():
    goal1 = GoalModel(id=1, user_id=1, title="Parent", category="test")
    goal2 = GoalModel(id=2, user_id=1, title="Child", category="test")
    goal3 = GoalModel(id=3, user_id=1, title="Grandchild", category="test")

    goal3.parent = goal2
    goal2.parent = goal1
    goal1.children = [goal2]
    goal2.children = [goal3]

    assert goal1.parent is None
    assert goal2.parent is goal1
    assert goal3.parent is goal2
    assert goal1 not in goal2.children


def test_progress_event_serialization():
    event = ProgressEventModel(
        goal_id=1,
        value=5,
        description="Test event with special chars: áéíóú 🚀",
        mood="happy",
        event_date=date(2024, 3, 15),
        created_at=datetime(2024, 3, 15, 10, 30, 0),
    )

    assert "🚀" in event.description
    assert "áéíóú" in event.description

    assert isinstance(event.value, int)
    assert isinstance(event.description, str)
    assert isinstance(event.event_date, date)
    assert isinstance(event.created_at, datetime)


@pytest.fixture
def sample_goal():
    return GoalModel(
        user_id=1, title="Test Goal", category="test", target_value=10, unit="units"
    )


@pytest.fixture
def sample_event():
    return ProgressEventModel(
        goal_id=1, value=1, description="Test event", mood="neutral"
    )


@pytest.fixture
def sample_image():
    return ImageModel(goal_id=1, img_url="/static/images/test.jpg")


def test_goal_with_fixture(sample_goal):
    assert sample_goal.user_id == 1
    assert sample_goal.title == "Test Goal"
    assert sample_goal.category == "test"


def test_event_with_fixture(sample_event):
    assert sample_event.goal_id == 1
    assert sample_event.value == 1
    assert sample_event.description == "Test event"


def test_image_with_fixture(sample_image):
    assert sample_image.goal_id == 1
    assert sample_image.img_url == "/static/images/test.jpg"
