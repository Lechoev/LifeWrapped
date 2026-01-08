from src.common.dependencies import get_uow_factory
from src.profiles.services import ProfileService


def get_profile_service() -> ProfileService:
    return ProfileService(uow_factory=get_uow_factory())
