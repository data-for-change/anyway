import json
import math
from typing import List, Tuple

from pydantic import BaseModel, Extra, Field, ValidationError, validator

Coordinate = Tuple[float, float]
Coordinates = List[Coordinate]
Polygon = List[Coordinate]
MINIMUM_POINTS_FOR_POLYGON = 4  # triangle: 3 vertices + first point repeated to close
COORDINATE_EPS = 1e-9


def _coordinates_equal(first: Coordinate, second: Coordinate) -> bool:
    return (
        abs(first[0] - second[0]) <= COORDINATE_EPS
        and abs(first[1] - second[1]) <= COORDINATE_EPS
    )


def _is_closed_polygon(coordinates: Coordinates) -> bool:
    return _coordinates_equal(coordinates[0], coordinates[-1])


class GeoObject(BaseModel):
    coordinates: List[Coordinate] = Field(..., min_items=MINIMUM_POINTS_FOR_POLYGON)

    class Config:
        extra = Extra.ignore

    def as_polygon(self) -> Polygon:
        return list(self.coordinates)

    @validator("coordinates")
    def validate_polygon(cls, coordinates: Coordinates) -> Coordinates:
        for point_index, point in enumerate(coordinates):
            lon, lat = point
            if not math.isfinite(lon) or not math.isfinite(lat):
                raise ValueError(f"coordinates[{point_index}] must contain finite numbers")
            if not -180 <= lon <= 180:
                raise ValueError(f"coordinates[{point_index}][0] must be a valid longitude")
            if not -90 <= lat <= 90:
                raise ValueError(f"coordinates[{point_index}][1] must be a valid latitude")
        if not _is_closed_polygon(coordinates):
            raise ValueError("polygon must be closed")
        return coordinates


class GeoFilter(BaseModel):
    polygons: List[GeoObject] = Field(..., min_items=1)


def _validation_error_message(exc: ValidationError) -> str:
    return exc.errors()[0]["msg"]


def parse_geo_param(values: List[str]) -> List[Polygon]:
    if len(values) != 1:
        raise ValueError("geo must be a single JSON object")
    try:
        data = json.loads(values[0])
    except json.JSONDecodeError as exc:
        raise ValueError("geo must be valid JSON") from exc
    try:
        geo_filter = GeoFilter.parse_obj(data)
    except ValidationError as exc:
        raise ValueError(_validation_error_message(exc)) from exc
    return [geo_object.as_polygon() for geo_object in geo_filter.polygons]
