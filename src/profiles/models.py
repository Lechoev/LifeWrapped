from datetime import datetime, date

from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Text, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import conf


class ProfileModel(conf.Base):
    __tablename__ = "profile"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("auth.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["AuthModel"] = relationship("AuthModel", back_populates="profile")

    def __str__(self) -> str:
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip() or "No name"
        return f"Profile(user_id={self.user_id}, name={full_name}, has_bio={bool(self.bio)})"
