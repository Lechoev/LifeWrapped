from functools import lru_cache

from src.conf.session_manager import create_uow


@lru_cache()
def get_uow_factory():
    """Кэшируемая фабрика UoW"""

    def factory():
        return create_uow()

    return factory
