import random
import string
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import conf

if TYPE_CHECKING:
    from src.profiles.models import ProfileModel


class AuthModel(conf.Base):
    __tablename__ = "auth"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    profile: Mapped["ProfileModel"] = relationship(
        "ProfileModel",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan",
    )
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __str__(self) -> str:
        return f"Auth(id={self.id}, email={self.email}, verified={self.is_verified})"


class VerificationCodeModel(conf.Base):
    __tablename__ = "verification_code"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)

    def is_valid(self) -> bool:
        """Код действителен минуту и не использован"""
        if self.is_used:
            return False

        now_utc = datetime.now(timezone.utc)

        if self.created_at.tzinfo is None:
            created_utc = self.created_at.replace(tzinfo=timezone.utc)
        else:
            created_utc = self.created_at

        age = now_utc - created_utc
        return age < timedelta(minutes=1)

    def mark_used(self):
        self.is_used = True

    @classmethod
    def generate_code(cls, email: str) -> "VerificationCodeModel":
        code = "".join(random.choices(string.digits, k=6))
        return cls(email=email, code=code)


class RefreshTokenModel(conf.Base):
    __tablename__ = "refresh_token"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("auth.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped["AuthModel"] = relationship(
        "AuthModel", back_populates="refresh_tokens"
    )
