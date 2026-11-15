"""
base/repositories/geo_repository.py
=====================================
Repository async pour les entités géographiques :
    CountryModel, RegionModel, CityModel, GeographicZoneModel
"""
from core.orm import select
from sqlalchemy import delete as sqla_delete
from modules.melodi_geo.models.geo_model import (
    CountryModel,
    RegionModel,
    CityModel,
    GeographicZoneModel,
    geo_zone_country_rel_table,
)


class GeoRepository:
    def __init__(self, module):
        self.module = module

    # ─── Countries ──────────────────────────────────────────────────────────────

    async def get_all_countries(self) -> list[CountryModel]:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(select(CountryModel).order_by(CountryModel.name))
            return list(res.scalars().all())

    async def get_country_by_id(self, country_id: str) -> CountryModel | None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(CountryModel).where(CountryModel.code_iso == country_id)
            )
            return res.scalar_one_or_none()

    async def create_country(self, data: dict) -> CountryModel:
        async with self.module.app.db.get_session() as session:
            obj = CountryModel(**data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    async def update_country(self, country_id: str, data: dict) -> None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(CountryModel).where(CountryModel.code_iso == country_id)
            )
            obj = res.scalar_one_or_none()
            if obj:
                for k, v in data.items():
                    setattr(obj, k, v)
                await session.commit()

    async def delete_country(self, country_id: str) -> None:
        async with self.module.app.db.get_session() as session:
            await session.execute(
                sqla_delete(CountryModel).where(CountryModel.code_iso == country_id)
            )
            await session.commit()

    # ─── Regions ────────────────────────────────────────────────────────────────

    async def get_all_regions(self, country_id: str | None = None) -> list[RegionModel]:
        async with self.module.app.db.get_session() as session:
            stmt = select(RegionModel).order_by(RegionModel.name)
            if country_id:
                stmt = stmt.where(RegionModel.country_id == country_id)
            res = await session.execute(stmt)
            return list(res.scalars().all())

    async def get_region_by_id(self, region_id: str) -> RegionModel | None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(RegionModel).where(RegionModel.id == region_id)
            )
            return res.scalar_one_or_none()

    async def create_region(self, data: dict) -> RegionModel:
        async with self.module.app.db.get_session() as session:
            obj = RegionModel(**data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    async def update_region(self, region_id: str, data: dict) -> None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(RegionModel).where(RegionModel.id == region_id)
            )
            obj = res.scalar_one_or_none()
            if obj:
                for k, v in data.items():
                    setattr(obj, k, v)
                await session.commit()

    async def delete_region(self, region_id: str) -> None:
        async with self.module.app.db.get_session() as session:
            await session.execute(
                sqla_delete(RegionModel).where(RegionModel.id == region_id)
            )
            await session.commit()

    # ─── Cities ─────────────────────────────────────────────────────────────────

    async def get_all_cities(self, region_id: str | None = None) -> list[CityModel]:
        async with self.module.app.db.get_session() as session:
            stmt = select(CityModel).order_by(CityModel.name)
            if region_id:
                stmt = stmt.where(CityModel.region_id == region_id)
            res = await session.execute(stmt)
            return list(res.scalars().all())

    async def get_city_by_id(self, city_id: str) -> CityModel | None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(CityModel).where(CityModel.id == city_id)
            )
            return res.scalar_one_or_none()

    async def create_city(self, data: dict) -> CityModel:
        async with self.module.app.db.get_session() as session:
            obj = CityModel(**data)
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    async def update_city(self, city_id: str, data: dict) -> None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(CityModel).where(CityModel.id == city_id)
            )
            obj = res.scalar_one_or_none()
            if obj:
                for k, v in data.items():
                    setattr(obj, k, v)
                await session.commit()

    async def delete_city(self, city_id: str) -> None:
        async with self.module.app.db.get_session() as session:
            await session.execute(
                sqla_delete(CityModel).where(CityModel.id == city_id)
            )
            await session.commit()

    # ─── Geographic Zones ───────────────────────────────────────────────────────

    async def get_all_zones(self) -> list[GeographicZoneModel]:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(GeographicZoneModel).order_by(GeographicZoneModel.name)
            )
            return list(res.scalars().all())

    async def get_zone_by_id(self, zone_id: int) -> GeographicZoneModel | None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(GeographicZoneModel).where(GeographicZoneModel.id == zone_id)
            )
            return res.scalar_one_or_none()

    async def create_zone(self, data: dict) -> GeographicZoneModel:
        async with self.module.app.db.get_session() as session:
            obj = GeographicZoneModel(
                name=data["name"],
                description=data.get("description") or None,
            )
            session.add(obj)
            await session.commit()
            await session.refresh(obj)
            return obj

    async def update_zone(self, zone_id: int, data: dict) -> None:
        async with self.module.app.db.get_session() as session:
            res = await session.execute(
                select(GeographicZoneModel).where(GeographicZoneModel.id == zone_id)
            )
            obj = res.scalar_one_or_none()
            if obj:
                obj.name = data.get("name", obj.name)
                obj.description = data.get("description") or None
                await session.commit()

    async def delete_zone(self, zone_id: int) -> None:
        async with self.module.app.db.get_session() as session:
            await session.execute(
                sqla_delete(GeographicZoneModel).where(GeographicZoneModel.id == zone_id)
            )
            await session.commit()

    async def set_zone_countries(self, zone_id: int, country_ids: list[str]) -> None:
        """Remplace entièrement les pays associés à une zone commerciale."""
        async with self.module.app.db.get_session() as session:
            # Supprimer les liens existants
            await session.execute(
                sqla_delete(geo_zone_country_rel_table).where(
                    geo_zone_country_rel_table.c.zone_id == zone_id
                )
            )
            # Ré-insérer
            for cid in country_ids:
                await session.execute(
                    geo_zone_country_rel_table.insert().values(zone_id=zone_id, country_id=cid)
                )
            await session.commit()
