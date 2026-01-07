from datetime import datetime, date

from sqlalchemy import String, Integer, DateTime, func, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src import conf


class GoalModel(conf.Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("auth.id", ondelete="CASCADE"), index=True)

    parent_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # books, travel, health, etc.

    target_value: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = качественная цель
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "книг", "стран", "км"

    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)  # дата завершения, выбирает пользователь

    current_value: Mapped[int] = mapped_column(Integer, default=0)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(),
                                                 onupdate=func.now())

    # Связи
    parent: Mapped["GoalModel | None"] = relationship("GoalModel", remote_side=[id], back_populates="children")
    children: Mapped[list["GoalModel"]] = relationship("GoalModel", back_populates="parent",
                                                       cascade="all, delete-orphan")
    events: Mapped[list["ProgressEventModel"]] = relationship("ProgressEventModel", back_populates="goal")
    images: Mapped[list["ImageModel"]] = relationship("ImageModel", back_populates="goal")


class ProgressEventModel(conf.Base):
    __tablename__ = "progress_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Количественный вклад в цель (обычно +1, но может быть +10 км, +500 руб и т.д.)
    value: Mapped[int] = mapped_column(Integer, default=1)

    # Описание события — то, что пользователь хочет запомнить
    description: Mapped[str] = mapped_column(Text, nullable=False)  # "Прочитал '1984' Орвелла"

    # Настроение в момент достижения
    mood: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "proud", "happy", "tired", "motivated"

    # Дата события
    event_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связи
    goal: Mapped["GoalModel"] = relationship("GoalModel", back_populates="events")
    images: Mapped[list["ImageModel"]] = relationship(
        "ImageModel", back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ProgressEvent {self.value} — {self.description[:30]}... ({self.event_date})>"


class ImageModel(conf.Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Может быть прикреплено к чему-то одному
    goal_id: Mapped[int | None] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=True, index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("progress_events.id", ondelete="CASCADE"), nullable=True, index=True
    )

    img_url: Mapped[str] = mapped_column(String(500), nullable=False)  # /static/images/...

    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Связи
    goal: Mapped["GoalModel | None"] = relationship("GoalModel", back_populates="images")
    event: Mapped["ProgressEventModel | None"] = relationship("ProgressEventModel", back_populates="images")
