from __future__ import annotations

from core.module import ApplicationModule
from modules.melodi_geo.controllers.api import GeoAPIController


class GeoModule(ApplicationModule):
    def __init__(self):
        super().__init__(name="melodi_geo", router_name="melodi_geo")

    async def load(self):
        # Endpoints API publics
        self.api_router.add_route("/countries", GeoAPIController.countries, methods=["GET"])
        self.api_router.add_route("/countries/<country_id>/regions", GeoAPIController.regions, methods=["GET"])
        self.api_router.add_route("/regions/<region_id>/cities", GeoAPIController.cities, methods=["GET"])
        self.api_router.add_route("/zones", GeoAPIController.zones, methods=["GET"])
        self.api_router.add_route("/seed", GeoAPIController.seed_defaults, methods=["POST"])

        # Endpoints API admin
        self.api_admin_router.add_route("/countries", GeoAPIController.countries, methods=["GET"])
        self.api_admin_router.add_route("/countries/<country_id>/regions", GeoAPIController.regions, methods=["GET"])
        self.api_admin_router.add_route("/regions/<region_id>/cities", GeoAPIController.cities, methods=["GET"])
        self.api_admin_router.add_route("/zones", GeoAPIController.zones, methods=["GET"])
        self.api_admin_router.add_route("/seed", GeoAPIController.seed_defaults, methods=["POST"])


module = GeoModule()
