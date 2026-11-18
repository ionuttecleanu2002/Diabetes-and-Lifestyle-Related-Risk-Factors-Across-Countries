from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Source(Base):
    __tablename__ = "source"

    source_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    indicators: Mapped[list["Indicator"]] = relationship(back_populates="source")


class Country(Base):
    __tablename__ = "country"

    country_iso3: Mapped[str] = mapped_column(String(3), primary_key=True)
    country_name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(100))

    observations: Mapped[list["Observation"]] = relationship(
        back_populates="country"
    )


class Indicator(Base):
    __tablename__ = "indicator"

    indicator_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    indicator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("source.source_id"), nullable=False
    )

    source: Mapped["Source"] = relationship(back_populates="indicators")
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="indicator"
    )


class Observation(Base):
    __tablename__ = "observation"

    observation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    country_iso3: Mapped[str] = mapped_column(
        String(3), ForeignKey("country.country_iso3"), nullable=False
    )
    indicator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("indicator.indicator_id"), nullable=False
    )
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    sex: Mapped[str] = mapped_column(String(10), nullable=False, default="BTSX")
    age_group: Mapped[str] = mapped_column(
        String(50), nullable=False, default="All ages"
    )
    value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    is_outlier: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    country: Mapped["Country"] = relationship(back_populates="observations")
    indicator: Mapped["Indicator"] = relationship(back_populates="observations")

    __table_args__ = (
        UniqueConstraint(
            "country_iso3",
            "indicator_id",
            "year",
            "sex",
            "age_group",
            name="uq_observation_country_indicator_year_sex_age",
        ),
        Index("ix_observation_indicator_year", "indicator_id", "year"),
    )


class ImportLog(Base):
    __tablename__ = "import_log"

    import_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("source.source_id"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    records_imported: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0
    )
    error_message: Mapped[str | None] = mapped_column(Text)