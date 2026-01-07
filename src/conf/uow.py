from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.auth_user.repositories import AuthRepository
from src.goals.repositories import GoalRepository
from src.profiles.repositories import ProfileRepository


class UnitOfWork:
    def __init__(self, session_factory: async_sessionmaker):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        self.transaction = None
        self._repositories_cache = {}

    async def __aenter__(self):
        self.session = self._session_factory()
        self.transaction = await self.session.begin()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type:
                await self.transaction.rollback()
            else:
                try:
                    await self.transaction.commit()
                except Exception:
                    if self.transaction.is_active:
                        await self.transaction.rollback()
                    raise
        finally:
            await self.session.close()
            self.session = None
            self.transaction = None
            self._repositories_cache.clear()

    @property
    def goals(self) -> GoalRepository:
        """Ленивая загрузка репозитория целей"""
        if 'goals' not in self._repositories_cache:
            if not self.session:
                raise RuntimeError("Session not initialized. Use UoW in context manager")
            self._repositories_cache['goals'] = GoalRepository(self.session)
        return self._repositories_cache['goals']

    @property
    def profiles(self) -> ProfileRepository:
        if 'profiles' not in self._repositories_cache:
            if not self.session:
                raise RuntimeError("Session not initialized. Use UoW in context manager")
            self._repositories_cache['profiles'] = ProfileRepository(self.session)
        return self._repositories_cache['profiles']

    @property
    def auth(self) -> AuthRepository:
        if 'auth' not in self._repositories_cache:
            if not self.session:
                raise RuntimeError("Session not initialized. Use UoW in context manager")
            self._repositories_cache['auth'] = AuthRepository(self.session)
        return self._repositories_cache['auth']
