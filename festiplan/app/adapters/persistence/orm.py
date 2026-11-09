"""Modèles ORM SQLAlchemy : détail de persistance, invisibles du domaine. Schéma inchangé."""
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.adapters.persistence.database import Base


class FestivalRow(Base):
    __tablename__ = "festivals"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    location: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="preparation", nullable=False)
    stages = relationship("StageRow", back_populates="festival")
    concerts = relationship("ConcertRow", back_populates="festival")


class ArtistRow(Base):
    __tablename__ = "artists"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    genre: Mapped[str] = mapped_column(String(80), nullable=False)
    required_equipment: Mapped[str] = mapped_column(Text, default="", nullable=False)


class StageRow(Base):
    __tablename__ = "stages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    festival_id: Mapped[int] = mapped_column(ForeignKey("festivals.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    available_equipment: Mapped[str] = mapped_column(Text, default="", nullable=False)
    festival = relationship("FestivalRow", back_populates="stages")


class ConcertRow(Base):
    __tablename__ = "concerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    festival_id: Mapped[int] = mapped_column(ForeignKey("festivals.id"), nullable=False)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), nullable=False)
    stage_id: Mapped[int] = mapped_column(ForeignKey("stages.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False)
    festival = relationship("FestivalRow", back_populates="concerts")


class IncidentRow(Base):
    __tablename__ = "incidents"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concert_id: Mapped[int] = mapped_column(ForeignKey("concerts.id"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
