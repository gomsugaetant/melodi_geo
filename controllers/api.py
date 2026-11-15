"""
base/controllers/api/geo.py
============================
Contrôleur API Quart pour les endpoints de géographie en cascade.

Routes montées dans module.py via api_router :
    GET /api/base/geo/countries
    GET /api/base/geo/countries/<country_id>/regions
    GET /api/base/geo/regions/<region_id>/cities
    GET /api/base/geo/zones

Toutes les routes sont publiques (pas d'auth requise) car les données
géographiques sont des référentiels statiques non-sensibles.
"""
from core.routing import Request, Response
from sqlalchemy import select

from modules.melodi_geo.models.geo_model import (
    CountryModel,
    RegionModel,
    CityModel,
    GeographicZoneModel,
)


class GeoAPIController:

    # ─── Countries ─────────────────────────────────────────────────────────────

    @staticmethod
    async def countries(request: Request, response: Response):
        """
        GET /api/base/geo/countries
        Retourne la liste complète des pays.

        Query params optionnels :
            - search : filtre sur le nom ou le code ISO (insensible à la casse)
        """
        search = (request.query.get("search") or "").strip().lower()

        async with request.module.app.db.get_session() as session:
            stmt = select(CountryModel).order_by(CountryModel.name)
            if search:
                from sqlalchemy import or_, func
                stmt = stmt.where(
                    or_(
                        func.lower(CountryModel.name).contains(search),
                        func.lower(CountryModel.code_iso).contains(search),
                    )
                )
            result = await session.execute(stmt)
            countries = result.scalars().all()

        return response.render_json({
            "count": len(countries),
            "data": [c.to_dict() for c in countries],
        })

    # ─── Regions (filtrées par pays) ────────────────────────────────────────────

    @staticmethod
    async def regions(request: Request, response: Response):
        """
        GET /api/base/geo/countries/<country_id>/regions
        Retourne les régions d'un pays donné, triées par nom.

        Path param :
            country_id : Integer PK du pays
        """
        country_id = request.params.get("country_id")
        if not country_id:
            return response.render_json({"error": "country_id manquant"}, status_code=400)

        country_id = str(country_id).strip().upper()
        if len(country_id) < 2 or len(country_id) > 3:
            return response.render_json({"error": "country_id doit être un code ISO de 2 ou 3 caractères"}, status_code=400)

        async with request.module.app.db.get_session() as session:
            # Vérifier que le pays existe
            country_result = await session.execute(
                select(CountryModel).where(CountryModel.code_iso == country_id)
            )
            country = country_result.scalar_one_or_none()
            if country is None:
                return response.render_json(
                    {"error": f"Pays avec code={country_id} introuvable"},
                    status_code=404,
                )

            stmt = (
                select(RegionModel)
                .where(RegionModel.country_id == country_id)
                .order_by(RegionModel.name)
            )
            result = await session.execute(stmt)
            regions = result.scalars().all()

        return response.render_json({
            "country_id": country_id,
            "count": len(regions),
            "data": [r.to_dict() for r in regions],
        })

    # ─── Cities (filtrées par région) ───────────────────────────────────────────

    @staticmethod
    async def cities(request: Request, response: Response):
        """
        GET /api/base/geo/regions/<region_id>/cities
        Retourne les villes d'une région donnée, triées par nom.

        Path param :
            region_id : Integer PK de la région
        """
        region_id = request.params.get("region_id")
        if not region_id:
            return response.render_json({"error": "region_id manquant"}, status_code=400)

        async with request.module.app.db.get_session() as session:
            # Vérifier que la région existe
            region_result = await session.execute(
                select(RegionModel).where(RegionModel.id == region_id)
            )
            region = region_result.scalar_one_or_none()
            if region is None:
                return response.render_json(
                    {"error": f"Région avec id={region_id} introuvable"},
                    status_code=404,
                )

            stmt = (
                select(CityModel)
                .where(CityModel.region_id == region_id)
                .order_by(CityModel.name)
            )
            result = await session.execute(stmt)
            cities = result.scalars().all()

        return response.render_json({
            "region_id": region_id,
            "count": len(cities),
            "data": [c.to_dict() for c in cities],
        })

    # ─── Geographic Zones ──────────────────────────────────────────────────────

    @staticmethod
    async def zones(request: Request, response: Response):
        """
        GET /api/base/geo/zones
        Retourne toutes les zones commerciales avec leurs pays associés.
        """
        async with request.module.app.db.get_session() as session:
            result = await session.execute(
                select(GeographicZoneModel).order_by(GeographicZoneModel.name)
            )
            zones = result.scalars().all()

        return response.render_json({
            "count": len(zones),
            "data": [z.to_dict() for z in zones],
        })

    # ─── CRUD Géographie ───────────────────────────────────────────────────────

    @staticmethod
    async def save_country(request: Request, response: Response):
        """POST /api/base/geo/countries"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            body = request.json or {}
            code_iso = (body.get("code_iso") or body.get("country_id") or "").strip().upper()
            if not code_iso:
                return response.send_json({"success": False, "error": "code_iso requis"}, status=400)
            if len(code_iso) < 2 or len(code_iso) > 3:
                return response.send_json({"success": False, "error": "code_iso doit comporter 2 ou 3 caractères"}, status=400)

            name = (body.get("name") or "").strip()
            if not name:
                return response.send_json({"success": False, "error": "name requis"}, status=400)

            data = {
                "name": name,
                "default_currency_code": body.get("default_currency_code") or "XAF",
            }
            existing = await repo.get_country_by_id(code_iso)
            if existing:
                await repo.update_country(code_iso, data)
            else:
                data["code_iso"] = code_iso
                await repo.create_country(data)

            return response.send_json({"success": True, "message": "Pays enregistré avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

    @staticmethod
    async def delete_country(request: Request, response: Response):
        """DELETE /api/base/geo/countries"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            code_iso = (request.params.get("country_id") or request.query.get("country_id") or (request.json or {}).get("country_id") or "").strip().upper()
            if not code_iso:
                return response.send_json({"success": False, "error": "country_id requis"}, status=400)

            await repo.delete_country(code_iso)
            return response.send_json({"success": True, "message": "Pays supprimé avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

    @staticmethod
    async def save_region(request: Request, response: Response):
        """POST /api/base/geo/regions"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            body = request.json or {}
            region_id = (body.get("region_id") or body.get("id") or "").strip()
            code = (body.get("code") or "").strip()
            name = (body.get("name") or "").strip()
            country_id = (body.get("country_id") or "").strip().upper()

            if not name or not country_id:
                return response.send_json({"success": False, "error": "name et country_id requis"}, status=400)

            if not region_id:
                target_id = code.lower() if code else f"{country_id.lower()}_{name.lower().replace(' ', '_')}"
                existing = await repo.get_region_by_id(target_id)
                if existing:
                    await repo.update_region(target_id, {"name": name, "country_id": country_id})
                else:
                    await repo.create_region({"id": target_id, "country_id": country_id, "name": name})
            else:
                await repo.update_region(region_id, {"name": name, "country_id": country_id})

            return response.send_json({"success": True, "message": "Région enregistrée avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

    @staticmethod
    async def delete_region(request: Request, response: Response):
        """DELETE /api/base/geo/regions"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            region_id = request.params.get("region_id") or request.query.get("region_id") or (request.json or {}).get("region_id")
            if not region_id:
                return response.send_json({"success": False, "error": "region_id requis"}, status=400)

            await repo.delete_region(str(region_id))
            return response.send_json({"success": True, "message": "Région supprimée avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

    @staticmethod
    async def save_city(request: Request, response: Response):
        """POST /api/base/geo/cities"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            body = request.json or {}
            city_id = (body.get("city_id") or body.get("id") or "").strip()
            code = (body.get("code") or "").strip()
            name = (body.get("name") or "").strip()
            region_id = (body.get("region_id") or "").strip()
            postal_code = body.get("postal_code")

            if not name or not region_id:
                return response.send_json({"success": False, "error": "name et region_id requis"}, status=400)

            if not city_id:
                target_id = code.lower() if code else f"{region_id}_{name.lower().replace(' ', '_')}"
                existing = await repo.get_city_by_id(target_id)
                if existing:
                    await repo.update_city(target_id, {"name": name, "region_id": region_id, "postal_code": postal_code})
                else:
                    await repo.create_city({"id": target_id, "region_id": region_id, "name": name, "postal_code": postal_code})
            else:
                await repo.update_city(city_id, {"name": name, "region_id": region_id, "postal_code": postal_code})

            return response.send_json({"success": True, "message": "Ville enregistrée avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

    @staticmethod
    async def delete_city(request: Request, response: Response):
        """DELETE /api/base/geo/cities"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            city_id = request.params.get("city_id") or request.query.get("city_id") or (request.json or {}).get("city_id")
            if not city_id:
                return response.send_json({"success": False, "error": "city_id requis"}, status=400)

            await repo.delete_city(str(city_id))
            return response.send_json({"success": True, "message": "Ville supprimée avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

    @staticmethod
    async def save_zone(request: Request, response: Response):
        """POST /api/base/geo/zones"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            body = request.json or {}
            zone_id = body.get("zone_id") or body.get("id")
            name = (body.get("name") or "").strip()
            description = body.get("description")
            country_ids = body.get("country_ids") or []

            if not name:
                return response.send_json({"success": False, "error": "name requis"}, status=400)

            data = {
                "name": name,
                "description": description,
            }

            if zone_id:
                await repo.update_zone(int(zone_id), data)
                if country_ids is not None:
                    await repo.set_zone_countries(int(zone_id), country_ids)
            else:
                created = await repo.create_zone(data)
                if country_ids:
                    await repo.set_zone_countries(created.id, country_ids)

            return response.send_json({"success": True, "message": "Zone enregistrée avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

    @staticmethod
    async def delete_zone(request: Request, response: Response):
        """DELETE /api/base/geo/zones"""
        try:
            from modules.melodi_geo.repositories.geo_repository import GeoRepository
            repo = GeoRepository(request.module)
            zone_id = request.params.get("zone_id") or request.query.get("zone_id") or (request.json or {}).get("zone_id")
            if not zone_id:
                return response.send_json({"success": False, "error": "zone_id requis"}, status=400)

            await repo.delete_zone(int(zone_id))
            return response.send_json({"success": True, "message": "Zone supprimée avec succès"})
        except Exception as e:
            return response.send_json({"success": False, "error": str(e)}, status=500)

