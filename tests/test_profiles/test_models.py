import pytest
from datetime import date
from src.goals.models import GoalModel, ProgressEventModel, ImageModel


def test_goal_model_creation():
    goal = GoalModel(
        user_id=1,
        title="Read 10 books",
        category="books",
        target_value=10,
        unit="книг",
        end_date=date(2024, 12, 31),
    )

    assert goal.user_id == 1
    assert goal.title == "Read 10 books"
    assert goal.category == "books"
    assert goal.target_value == 10
    assert goal.unit == "книг"
    assert goal.end_date == date(2024, 12, 31)
    assert goal.current_value is None
    assert goal.is_completed is None


def test_goal_model_with_qualitative_goal():
    goal = GoalModel(
        user_id=1,
        title="Learn to play guitar",
        category="hobby",
        target_value=None,
        unit=None,
        end_date=date(2024, 12, 31),
    )

    assert goal.target_value is None
    assert goal.unit is None
    assert goal.current_value is None
    assert goal.is_completed is None


def test_goal_model_without_end_date():
    goal = GoalModel(
        user_id=1,
        title="Learn Spanish",
        category="education",
        end_date=None,
    )

    assert goal.end_date is None
    assert goal.current_value is None
    assert goal.is_completed is None


def test_goal_model_completed_manual_values():
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

    assert goal.current_value == 10
    assert goal.is_completed is True
    assert goal.completed_at == completion_date


def test_progress_event_model_creation():
    event_date = date(2024, 3, 15)

    event = ProgressEventModel(
        goal_id=1,
        value=1,
        description="Read book",
        mood="proud",
        event_date=event_date,
    )

    assert event.goal_id == 1
    assert event.value == 1
    assert event.description == "Read book"
    assert event.mood == "proud"
    assert event.event_date == event_date


def test_progress_event_model_repr():
    event = ProgressEventModel(
        id=1,
        goal_id=1,
        value=5,
        description="Ran 5 km test",
        event_date=date(2024, 3, 15),
    )

    repr_str = repr(event)

    assert "<ProgressEvent" in repr_str
    assert "5" in repr_str
    assert "Ran" in repr_str


def test_progress_event_without_explicit_defaults():
    event = ProgressEventModel(
        goal_id=1,
        description="Test event",
    )

    assert event.value is None
    assert event.event_date is None


def test_image_model_for_goal():
    image = ImageModel(
        goal_id=1,
        img_url="/static/images/book_cover.jpg",
    )

    assert image.goal_id == 1
    assert image.event_id is None
    assert image.img_url == "/static/images/book_cover.jpg"


def test_image_model_for_event():
    image = ImageModel(
        event_id=1,
        img_url="/static/images/running.jpg",
    )

    assert image.event_id == 1
    assert image.goal_id is None
    assert image.img_url == "/static/images/running.jpg"


def test_goal_with_events_and_images():
    goal = GoalModel(
        id=1,
        user_id=1,
        title="Travel to 5 countries",
        category="travel",
        target_value=5,
        unit="countries",
    )

    event1 = ProgressEventModel(
        id=1,
        goal_id=1,
        value=1,
        description="Visited Italy",
        event_date=date(2024, 1, 15),
    )

    event2 = ProgressEventModel(
        id=2,
        goal_id=1,
        value=1,
        description="Visited France",
        event_date=date(2024, 2, 20),
    )

    image1 = ImageModel(
        id=1,
        event_id=1,
        img_url="/static/images/italy.jpg",
    )

    image2 = ImageModel(
        id=2,
        event_id=2,
        img_url="/static/images/france.jpg",
    )

    goal_image = ImageModel(
        id=3,
        goal_id=1,
        img_url="/static/images/travel_goal.jpg",
    )

    goal.events = [event1, event2]
    goal.images = [goal_image]

    event1.goal = goal
    event2.goal = goal
    event1.images = [image1]
    event2.images = [image2]

    image1.event = event1
    image2.event = event2
    goal_image.goal = goal

    assert len(goal.events) == 2
    assert len(goal.images) == 1

    assert goal.events[0].description == "Visited Italy"
    assert goal.events[1].description == "Visited France"

    assert event1.images[0].img_url == "/static/images/italy.jpg"
    assert event2.images[0].img_url == "/static/images/france.jpg"
    assert goal.images[0].img_url == "/static/images/travel_goal.jpg"

    assert goal.current_value is None
    assert goal.is_completed is None


def test_goal_parent_child_relationship():
    parent = GoalModel(
        id=1,
        user_id=1,
        title="Parent",
        category="health",
    )

    child = GoalModel(
        id=2,
        user_id=1,
        title="Child",
        category="health",
        parent_id=1,
    )

    parent.children = [child]
    child.parent = parent

    assert parent.parent is None
    assert len(parent.children) == 1
    assert child.parent is parent
