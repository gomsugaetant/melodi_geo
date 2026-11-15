from __future__ import annotations

from core.db.base_module_tables import BaseModuleTables

MODULE_NAME = "melodi_geo"
PREFIX_TABLE = "ml_base_"


class GeoTables(BaseModuleTables):
    GEO_COUNTRIES = f"{PREFIX_TABLE}geo_countries"
    GEO_REGIONS = f"{PREFIX_TABLE}geo_regions"
    GEO_CITIES = f"{PREFIX_TABLE}geo_cities"
    GEO_ZONES = f"{PREFIX_TABLE}geo_zones"
    GEO_ZONE_COUNTRY_REL = f"{PREFIX_TABLE}geo_zone_country_rel"
    CURRENCIES = f"{PREFIX_TABLE}currencies"
