from typing import List

from sqlalchemy import func, or_

from anyway.models import SDAccident
from anyway.views.safety_data.geo_parser import Polygon, parse_geo_param


def _polygon_wkt(coordinates: Polygon) -> str:
    # Enforce exact closure: validation only guarantees the first and last points
    # match within COORDINATE_EPS, but ST_GeomFromText rejects non-closed rings.
    ring = list(coordinates)
    ring[-1] = ring[0]
    points = ", ".join(f"{lon} {lat}" for lon, lat in ring)
    return f"POLYGON(({points}))"


def add_geo_filter(query, values: List[str]):
    polygons = parse_geo_param(values)
    query = query.filter(SDAccident.geom.isnot(None))
    covers_exprs = [
        func.ST_Covers(
            func.ST_GeomFromText(_polygon_wkt(coordinates), 4326), SDAccident.geom
        )
        for coordinates in polygons
    ]
    return query.filter(or_(*covers_exprs))
