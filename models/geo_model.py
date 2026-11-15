"""
base/models/geo_model.py
========================
Structure géographique administrative normalisée pour MELODI ERP.

Hiérarchie : Country → Region → City
Zone commerciale virtuelle : GeographicZone ←M2M→ Country
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy import UniqueConstraint, Table, Column, Integer as SAInteger, String as SAString, ForeignKey as SAFK
from core.orm.model import (
    BaseModel,
    Mapped,
    mapped_column,
    relationship,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    Boolean,
)
from modules.melodi_geo.config import GeoTables as BaseTables


# ─── Table d'association M2M : Zone ↔ Country ─────────────────────────────────
# On utilise une Table SQLAlchemy déclarative pour éviter un modèle full class
# car cette table n'a que des FKs (pas d'attributs supplémentaires).
geo_zone_country_rel_table = Table(
    BaseTables.GEO_ZONE_COUNTRY_REL,
    BaseModel.metadata,
    Column("zone_id", SAInteger, SAFK(f"{BaseTables.GEO_ZONES}.id", ondelete="CASCADE"), primary_key=True, nullable=False),
    Column("country_id", SAString(3), SAFK(f"{BaseTables.GEO_COUNTRIES}.code_iso", ondelete="CASCADE"), primary_key=True, nullable=False),
)


class CountryModel(BaseModel):
    """
    Pays — entité racine de la hiérarchie géographique.

    Colonnes :
        name             : Nom complet du pays (unique)
        code_iso         : Code ISO 3166-1 alpha-3 (3 lettres, PK)
        default_currency_code : Devise par défaut (FK → base_currencies.code, nullable)
    """
    __tablename__ = BaseTables.GEO_COUNTRIES

    code_iso: Mapped[str] = mapped_column(String(3), primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    default_currency_code: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    regions: Mapped[List["RegionModel"]] = relationship(
        "RegionModel",
        back_populates="country",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    default_currency = relationship(
        "CurrencyModel",
        foreign_keys=[default_currency_code],
        primaryjoin=f"CountryModel.default_currency_code == CurrencyModel.code",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.code_iso,
            "name": self.name,
            "code_iso": self.code_iso,
            "default_currency_code": self.default_currency_code,
        }


class RegionModel(BaseModel):
    """
    Région / Province / État — second niveau de la hiérarchie.

    Contrainte : (country_id, name) unique → pas deux régions de même nom dans un pays.
    """
    __tablename__ = BaseTables.GEO_REGIONS
    __table_args__ = (
        UniqueConstraint("country_id", "name", name=f"uq_{BaseTables.GEO_REGIONS}_country_name"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    country_id: Mapped[str] = mapped_column(
        String(3),
        ForeignKey(f"{BaseTables.GEO_COUNTRIES}.code_iso", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    country: Mapped["CountryModel"] = relationship(
        "CountryModel",
        back_populates="regions",
        lazy="selectin",
    )
    cities: Mapped[List["CityModel"]] = relationship(
        "CityModel",
        back_populates="region",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.id,
            "country_id": self.country_id,
            "name": self.name,
        }


class CityModel(BaseModel):
    """
    Ville — troisième niveau de la hiérarchie.

    Contrainte : (region_id, name) unique → pas deux villes de même nom dans une région.
    """
    __tablename__ = BaseTables.GEO_CITIES
    __table_args__ = (
        UniqueConstraint("region_id", "name", name=f"uq_{BaseTables.GEO_CITIES}_region_name"),
    )

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    region_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey(f"{BaseTables.GEO_REGIONS}.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    region: Mapped["RegionModel"] = relationship(
        "RegionModel",
        back_populates="cities",
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.id,
            "region_id": self.region_id,
            "name": self.name,
            "postal_code": self.postal_code,
        }


class GeographicZoneModel(BaseModel):
    """
    Zone commerciale virtuelle — regroupe des pays à des fins de tarification
    ou de segmentation marketing. Relation M2M avec CountryModel.
    """
    __tablename__ = BaseTables.GEO_ZONES

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ──────────────────────────────────────────────────────────
    countries: Mapped[List["CountryModel"]] = relationship(
        "CountryModel",
        secondary=geo_zone_country_rel_table,
        lazy="selectin",
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "countries": [c.to_dict() for c in (self.countries or [])],
        }
