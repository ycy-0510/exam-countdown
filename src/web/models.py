from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, Boolean, Column
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Config(Base):
    __tablename__ = "configs"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class RunLog(Base):
    __tablename__ = "run_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    days_left: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    ig_status: Mapped[str] = mapped_column(
        String(255), nullable=False, default="skipped"
    )
    fb_status: Mapped[str] = mapped_column(
        String(255), nullable=False, default="skipped"
    )
    discord_status: Mapped[str] = mapped_column(
        String(255), nullable=False, default="skipped"
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
