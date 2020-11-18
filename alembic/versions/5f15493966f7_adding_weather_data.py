"""Adding weather data

Revision ID: 5f15493966f7
Revises: 9687ef04f99d
Create Date: 2020-10-20 21:30:51.699025

"""

# revision identifiers, used by Alembic.
revision = '5f15493966f7'
down_revision = '9687ef04f99d'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


MARKERS_HEBREW_VIEW_WITH_WEATHER = """SELECT markers.id,
                                    markers.provider_and_id,
                                    markers.provider_code,
                                    provider_code.provider_code_hebrew,
                                    markers.file_type_police,
                                    markers.accident_type,
                                    accident_type.accident_type_hebrew,
                                    markers.accident_severity,
                                    accident_severity.accident_severity_hebrew,
                                    markers.created as accident_timestamp,
                                    markers.location_accuracy,
                                    location_accuracy.location_accuracy_hebrew,
                                    markers.road_type,
                                    road_type.road_type_hebrew,
                                    markers.road_shape,
                                    road_shape.road_shape_hebrew,
                                    markers.day_type,
                                    day_type.day_type_hebrew,
                                    markers.police_unit,
                                    police_unit.police_unit_hebrew,
                                    markers.one_lane,
                                    one_lane.one_lane_hebrew,
                                    markers.multi_lane,
                                    multi_lane.multi_lane_hebrew,
                                    markers.speed_limit,
                                    speed_limit.speed_limit_hebrew,
                                    markers.road_intactness,
                                    road_intactness.road_intactness_hebrew,
                                    markers.road_width,
                                    road_width.road_width_hebrew,
                                    markers.road_sign,
                                    road_sign.road_sign_hebrew,
                                    markers.road_light,
                                    road_light.road_light_hebrew,
                                    markers.road_control,
                                    road_control.road_control_hebrew,
                                    markers.weather,
                                    weather.weather_hebrew,
                                    markers.road_surface,
                                    road_surface.road_surface_hebrew,
                                    markers.road_object,
                                    road_object.road_object_hebrew,
                                    markers.object_distance,
                                    object_distance.object_distance_hebrew,
                                    markers.didnt_cross,
                                    didnt_cross.didnt_cross_hebrew,
                                    markers.cross_mode,
                                    cross_mode.cross_mode_hebrew,
                                    markers.cross_location,
                                    cross_location.cross_location_hebrew,
                                    markers.cross_direction,
                                    cross_direction.cross_direction_hebrew,
                                    markers.road1,
                                    markers.road2,
                                    markers.km,
                                    markers.km_raw,
                                    markers.km_accurate,
                                    accident_weathers.rain_rate as accident_rain_rate,
                                    road_segments.segment_id as road_segment_id,
                                    road_segments.segment as road_segment_number,
                                    road_segments.from_name || ' - ' || road_segments.to_name as road_segment_name,
                                    road_segments.from_km as road_segment_from_km,
                                    road_segments.to_km as road_segment_to_km,
                                    road_segments.to_km - road_segments.from_km as road_segment_length_km,
                                    markers.yishuv_symbol,
                                    markers.yishuv_name,
                                    markers.geo_area,
                                    geo_area.geo_area_hebrew,
                                    markers.day_night,
                                    day_night.day_night_hebrew,
                                    markers.day_in_week,
                                    day_in_week.day_in_week_hebrew,
                                    markers.traffic_light,
                                    traffic_light.traffic_light_hebrew,
                                    markers.region,
                                    region.region_hebrew,
                                    markers.district,
                                    district.district_hebrew,
                                    markers.natural_area,
                                    natural_area.natural_area_hebrew,
                                    markers.municipal_status,
                                    municipal_status.municipal_status_hebrew,
                                    markers.yishuv_shape,
                                    yishuv_shape.yishuv_shape_hebrew,
                                    markers.street1,
                                    markers.street1_hebrew,
                                    markers.street2,
                                    markers.street2_hebrew,
                                    markers.house_number,
                                    markers.non_urban_intersection,
                                    markers.non_urban_intersection_hebrew,
                                    markers.non_urban_intersection_by_junction_number,
                                    markers.urban_intersection,
                                    markers.accident_year,
                                    markers.accident_month,
                                    markers.accident_day,
                                    markers.accident_hour_raw,
                                    accident_hour_raw.accident_hour_raw_hebrew,
                                    markers.accident_hour,
                                    markers.accident_minute,
                                    markers.geom,
                                    markers.longitude,
                                    markers.latitude,
                                    markers.x,
                                    markers.y
                                   FROM markers
                                     LEFT JOIN road_segments on (markers.road1 = road_segments.road) AND (road_segments.from_km <= markers.km / 10) AND (markers.km / 10 < road_segments.to_km)
                                     LEFT JOIN accident_type ON markers.accident_type = accident_type.id AND markers.accident_year = accident_type.year AND markers.provider_code = accident_type.provider_code
                                     LEFT JOIN accident_severity ON markers.accident_severity = accident_severity.id AND markers.accident_year = accident_severity.year AND markers.provider_code = accident_severity.provider_code
                                     LEFT JOIN location_accuracy ON markers.location_accuracy = location_accuracy.id AND markers.accident_year = location_accuracy.year AND markers.provider_code = location_accuracy.provider_code
                                     LEFT JOIN road_type ON markers.road_type = road_type.id AND markers.accident_year = road_type.year AND markers.provider_code = road_type.provider_code
                                     LEFT JOIN road_shape ON markers.road_shape = road_shape.id AND markers.accident_year = road_shape.year AND markers.provider_code = road_shape.provider_code
                                     LEFT JOIN day_type ON markers.day_type = day_type.id AND markers.accident_year = day_type.year AND markers.provider_code = day_type.provider_code
                                     LEFT JOIN police_unit ON markers.police_unit = police_unit.id AND markers.accident_year = police_unit.year AND markers.provider_code = police_unit.provider_code
                                     LEFT JOIN one_lane ON markers.one_lane = one_lane.id  AND markers.accident_year = one_lane.year AND markers.provider_code = one_lane.provider_code
                                     LEFT JOIN multi_lane ON markers.multi_lane = multi_lane.id AND markers.accident_year = multi_lane.year AND markers.provider_code = multi_lane.provider_code
                                     LEFT JOIN speed_limit ON markers.speed_limit = speed_limit.id AND markers.accident_year = speed_limit.year AND markers.provider_code = speed_limit.provider_code
                                     LEFT JOIN road_intactness ON markers.road_intactness = road_intactness.id AND markers.accident_year = road_intactness.year AND markers.provider_code = road_intactness.provider_code
                                     LEFT JOIN road_width ON markers.road_width = road_width.id AND markers.accident_year = road_width.year AND markers.provider_code = road_width.provider_code
                                     LEFT JOIN road_sign ON markers.road_sign = road_sign.id AND markers.accident_year = road_sign.year AND markers.provider_code = road_sign.provider_code
                                     LEFT JOIN road_light ON markers.road_light = road_light.id AND markers.accident_year = road_light.year AND markers.provider_code = road_light.provider_code
                                     LEFT JOIN road_control ON markers.road_control = road_control.id AND markers.accident_year = road_control.year AND markers.provider_code = road_control.provider_code
                                     LEFT JOIN weather ON markers.weather = weather.id AND markers.accident_year = weather.year AND markers.provider_code = weather.provider_code
                                     LEFT JOIN accident_weathers ON accident_weathers.provider_code = markers.provider_code AND accident_weathers.accident_id = markers.id AND accident_weathers.accident_year = markers.accident_year
                                     LEFT JOIN road_surface ON markers.road_surface = road_surface.id AND markers.accident_year = road_surface.year AND markers.provider_code = road_surface.provider_code
                                     LEFT JOIN road_object ON markers.road_object = road_object.id AND markers.accident_year = road_object.year AND markers.provider_code = road_object.provider_code
                                     LEFT JOIN object_distance ON markers.object_distance = object_distance.id AND markers.accident_year = object_distance.year AND markers.provider_code = object_distance.provider_code
                                     LEFT JOIN didnt_cross ON markers.didnt_cross = didnt_cross.id AND markers.accident_year = didnt_cross.year AND markers.provider_code = didnt_cross.provider_code
                                     LEFT JOIN cross_mode ON markers.cross_mode = cross_mode.id AND markers.accident_year = cross_mode.year AND markers.provider_code = cross_mode.provider_code
                                     LEFT JOIN cross_location ON markers.cross_location = cross_location.id AND markers.accident_year = cross_location.year AND markers.provider_code = cross_location.provider_code
                                     LEFT JOIN cross_direction ON markers.cross_direction = cross_direction.id AND markers.accident_year = cross_direction.year AND markers.provider_code = cross_direction.provider_code
                                     LEFT JOIN geo_area ON markers.geo_area = geo_area.id AND markers.accident_year = geo_area.year AND markers.provider_code = geo_area.provider_code
                                     LEFT JOIN day_night ON markers.day_night = day_night.id AND markers.accident_year = day_night.year AND markers.provider_code = day_night.provider_code
                                     LEFT JOIN day_in_week ON markers.day_in_week = day_in_week.id AND markers.accident_year = day_in_week.year AND markers.provider_code = day_in_week.provider_code
                                     LEFT JOIN traffic_light ON markers.traffic_light = traffic_light.id AND markers.accident_year = traffic_light.year AND markers.provider_code = traffic_light.provider_code
                                     LEFT JOIN region ON markers.region = region.id AND markers.accident_year = region.year AND markers.provider_code = region.provider_code
                                     LEFT JOIN district ON markers.district = district.id AND markers.accident_year = district.year AND markers.provider_code = district.provider_code
                                     LEFT JOIN natural_area ON markers.natural_area = natural_area.id AND markers.accident_year = natural_area.year AND markers.provider_code = natural_area.provider_code
                                     LEFT JOIN municipal_status ON markers.municipal_status = municipal_status.id AND markers.accident_year = municipal_status.year AND markers.provider_code = municipal_status.provider_code
                                     LEFT JOIN yishuv_shape ON markers.yishuv_shape = yishuv_shape.id AND markers.accident_year = yishuv_shape.year AND markers.provider_code = yishuv_shape.provider_code
                                     LEFT JOIN accident_hour_raw ON markers.accident_hour_raw = accident_hour_raw.id AND markers.accident_year = accident_hour_raw.year AND markers.provider_code = accident_hour_raw.provider_code
                                     LEFT JOIN provider_code ON markers.provider_code = provider_code.id;"""


MARKERS_HEBREW_VIEW_WITHOUT_WEATHER = """SELECT markers.id,
                                    markers.provider_and_id,
                                    markers.provider_code,
                                    provider_code.provider_code_hebrew,
                                    markers.file_type_police,
                                    markers.accident_type,
                                    accident_type.accident_type_hebrew,
                                    markers.accident_severity,
                                    accident_severity.accident_severity_hebrew,
                                    markers.created as accident_timestamp,
                                    markers.location_accuracy,
                                    location_accuracy.location_accuracy_hebrew,
                                    markers.road_type,
                                    road_type.road_type_hebrew,
                                    markers.road_shape,
                                    road_shape.road_shape_hebrew,
                                    markers.day_type,
                                    day_type.day_type_hebrew,
                                    markers.police_unit,
                                    police_unit.police_unit_hebrew,
                                    markers.one_lane,
                                    one_lane.one_lane_hebrew,
                                    markers.multi_lane,
                                    multi_lane.multi_lane_hebrew,
                                    markers.speed_limit,
                                    speed_limit.speed_limit_hebrew,
                                    markers.road_intactness,
                                    road_intactness.road_intactness_hebrew,
                                    markers.road_width,
                                    road_width.road_width_hebrew,
                                    markers.road_sign,
                                    road_sign.road_sign_hebrew,
                                    markers.road_light,
                                    road_light.road_light_hebrew,
                                    markers.road_control,
                                    road_control.road_control_hebrew,
                                    markers.weather,
                                    weather.weather_hebrew,
                                    markers.road_surface,
                                    road_surface.road_surface_hebrew,
                                    markers.road_object,
                                    road_object.road_object_hebrew,
                                    markers.object_distance,
                                    object_distance.object_distance_hebrew,
                                    markers.didnt_cross,
                                    didnt_cross.didnt_cross_hebrew,
                                    markers.cross_mode,
                                    cross_mode.cross_mode_hebrew,
                                    markers.cross_location,
                                    cross_location.cross_location_hebrew,
                                    markers.cross_direction,
                                    cross_direction.cross_direction_hebrew,
                                    markers.road1,
                                    markers.road2,
                                    markers.km,
                                    markers.km_raw,
                                    markers.km_accurate,
                                    road_segments.segment_id as road_segment_id,
                                    road_segments.segment as road_segment_number,
                                    road_segments.from_name || ' - ' || road_segments.to_name as road_segment_name,
                                    road_segments.from_km as road_segment_from_km,
                                    road_segments.to_km as road_segment_to_km,
                                    road_segments.to_km - road_segments.from_km as road_segment_length_km,
                                    markers.yishuv_symbol,
                                    markers.yishuv_name,
                                    markers.geo_area,
                                    geo_area.geo_area_hebrew,
                                    markers.day_night,
                                    day_night.day_night_hebrew,
                                    markers.day_in_week,
                                    day_in_week.day_in_week_hebrew,
                                    markers.traffic_light,
                                    traffic_light.traffic_light_hebrew,
                                    markers.region,
                                    region.region_hebrew,
                                    markers.district,
                                    district.district_hebrew,
                                    markers.natural_area,
                                    natural_area.natural_area_hebrew,
                                    markers.municipal_status,
                                    municipal_status.municipal_status_hebrew,
                                    markers.yishuv_shape,
                                    yishuv_shape.yishuv_shape_hebrew,
                                    markers.street1,
                                    markers.street1_hebrew,
                                    markers.street2,
                                    markers.street2_hebrew,
                                    markers.house_number,
                                    markers.non_urban_intersection,
                                    markers.non_urban_intersection_hebrew,
                                    markers.non_urban_intersection_by_junction_number,
                                    markers.urban_intersection,
                                    markers.accident_year,
                                    markers.accident_month,
                                    markers.accident_day,
                                    markers.accident_hour_raw,
                                    accident_hour_raw.accident_hour_raw_hebrew,
                                    markers.accident_hour,
                                    markers.accident_minute,
                                    markers.geom,
                                    markers.longitude,
                                    markers.latitude,
                                    markers.x,
                                    markers.y
                                   FROM markers
                                     LEFT JOIN road_segments on (markers.road1 = road_segments.road) AND (road_segments.from_km <= markers.km / 10) AND (markers.km / 10 < road_segments.to_km)
                                     LEFT JOIN accident_type ON markers.accident_type = accident_type.id AND markers.accident_year = accident_type.year AND markers.provider_code = accident_type.provider_code
                                     LEFT JOIN accident_severity ON markers.accident_severity = accident_severity.id AND markers.accident_year = accident_severity.year AND markers.provider_code = accident_severity.provider_code
                                     LEFT JOIN location_accuracy ON markers.location_accuracy = location_accuracy.id AND markers.accident_year = location_accuracy.year AND markers.provider_code = location_accuracy.provider_code
                                     LEFT JOIN road_type ON markers.road_type = road_type.id AND markers.accident_year = road_type.year AND markers.provider_code = road_type.provider_code
                                     LEFT JOIN road_shape ON markers.road_shape = road_shape.id AND markers.accident_year = road_shape.year AND markers.provider_code = road_shape.provider_code
                                     LEFT JOIN day_type ON markers.day_type = day_type.id AND markers.accident_year = day_type.year AND markers.provider_code = day_type.provider_code
                                     LEFT JOIN police_unit ON markers.police_unit = police_unit.id AND markers.accident_year = police_unit.year AND markers.provider_code = police_unit.provider_code
                                     LEFT JOIN one_lane ON markers.one_lane = one_lane.id  AND markers.accident_year = one_lane.year AND markers.provider_code = one_lane.provider_code
                                     LEFT JOIN multi_lane ON markers.multi_lane = multi_lane.id AND markers.accident_year = multi_lane.year AND markers.provider_code = multi_lane.provider_code
                                     LEFT JOIN speed_limit ON markers.speed_limit = speed_limit.id AND markers.accident_year = speed_limit.year AND markers.provider_code = speed_limit.provider_code
                                     LEFT JOIN road_intactness ON markers.road_intactness = road_intactness.id AND markers.accident_year = road_intactness.year AND markers.provider_code = road_intactness.provider_code
                                     LEFT JOIN road_width ON markers.road_width = road_width.id AND markers.accident_year = road_width.year AND markers.provider_code = road_width.provider_code
                                     LEFT JOIN road_sign ON markers.road_sign = road_sign.id AND markers.accident_year = road_sign.year AND markers.provider_code = road_sign.provider_code
                                     LEFT JOIN road_light ON markers.road_light = road_light.id AND markers.accident_year = road_light.year AND markers.provider_code = road_light.provider_code
                                     LEFT JOIN road_control ON markers.road_control = road_control.id AND markers.accident_year = road_control.year AND markers.provider_code = road_control.provider_code
                                     LEFT JOIN weather ON markers.weather = weather.id AND markers.accident_year = weather.year AND markers.provider_code = weather.provider_code
                                     LEFT JOIN road_surface ON markers.road_surface = road_surface.id AND markers.accident_year = road_surface.year AND markers.provider_code = road_surface.provider_code
                                     LEFT JOIN road_object ON markers.road_object = road_object.id AND markers.accident_year = road_object.year AND markers.provider_code = road_object.provider_code
                                     LEFT JOIN object_distance ON markers.object_distance = object_distance.id AND markers.accident_year = object_distance.year AND markers.provider_code = object_distance.provider_code
                                     LEFT JOIN didnt_cross ON markers.didnt_cross = didnt_cross.id AND markers.accident_year = didnt_cross.year AND markers.provider_code = didnt_cross.provider_code
                                     LEFT JOIN cross_mode ON markers.cross_mode = cross_mode.id AND markers.accident_year = cross_mode.year AND markers.provider_code = cross_mode.provider_code
                                     LEFT JOIN cross_location ON markers.cross_location = cross_location.id AND markers.accident_year = cross_location.year AND markers.provider_code = cross_location.provider_code
                                     LEFT JOIN cross_direction ON markers.cross_direction = cross_direction.id AND markers.accident_year = cross_direction.year AND markers.provider_code = cross_direction.provider_code
                                     LEFT JOIN geo_area ON markers.geo_area = geo_area.id AND markers.accident_year = geo_area.year AND markers.provider_code = geo_area.provider_code
                                     LEFT JOIN day_night ON markers.day_night = day_night.id AND markers.accident_year = day_night.year AND markers.provider_code = day_night.provider_code
                                     LEFT JOIN day_in_week ON markers.day_in_week = day_in_week.id AND markers.accident_year = day_in_week.year AND markers.provider_code = day_in_week.provider_code
                                     LEFT JOIN traffic_light ON markers.traffic_light = traffic_light.id AND markers.accident_year = traffic_light.year AND markers.provider_code = traffic_light.provider_code
                                     LEFT JOIN region ON markers.region = region.id AND markers.accident_year = region.year AND markers.provider_code = region.provider_code
                                     LEFT JOIN district ON markers.district = district.id AND markers.accident_year = district.year AND markers.provider_code = district.provider_code
                                     LEFT JOIN natural_area ON markers.natural_area = natural_area.id AND markers.accident_year = natural_area.year AND markers.provider_code = natural_area.provider_code
                                     LEFT JOIN municipal_status ON markers.municipal_status = municipal_status.id AND markers.accident_year = municipal_status.year AND markers.provider_code = municipal_status.provider_code
                                     LEFT JOIN yishuv_shape ON markers.yishuv_shape = yishuv_shape.id AND markers.accident_year = yishuv_shape.year AND markers.provider_code = yishuv_shape.provider_code
                                     LEFT JOIN accident_hour_raw ON markers.accident_hour_raw = accident_hour_raw.id AND markers.accident_year = accident_hour_raw.year AND markers.provider_code = accident_hour_raw.provider_code
                                     LEFT JOIN provider_code ON markers.provider_code = provider_code.id;"""


INVOLVED_HEBREW_MARKERS_HEBREW_VIEW = """SELECT
    involved_hebrew.accident_id,
    involved_hebrew.provider_and_id,
    involved_hebrew.provider_code,
    involved_hebrew.file_type_police,
    involved_hebrew.involved_type,
    involved_hebrew.involved_type_hebrew,
    involved_hebrew.license_acquiring_date,
    involved_hebrew.age_group,
    involved_hebrew.age_group_hebrew,
    involved_hebrew.sex,
    involved_hebrew.sex_hebrew,
    involved_hebrew.vehicle_type as involve_vehicle_type,
    involved_hebrew.vehicle_type_hebrew as involve_vehicle_type_hebrew,
    involved_hebrew.safety_measures,
    involved_hebrew.safety_measures_hebrew,
    involved_hebrew.involve_yishuv_symbol,
    involved_hebrew.involve_yishuv_name,
    involved_hebrew.injury_severity,
    involved_hebrew.injury_severity_hebrew,
    involved_hebrew.injured_type,
    involved_hebrew.injured_type_hebrew,
    involved_hebrew.injured_position,
    involved_hebrew.injured_position_hebrew,
    involved_hebrew.population_type,
    involved_hebrew.population_type_hebrew,
    involved_hebrew.home_region as involve_home_region,
    involved_hebrew.home_region_hebrew as involve_home_region_hebrew,
    involved_hebrew.home_district as involve_home_district,
    involved_hebrew.home_district_hebrew as involve_home_district_hebrew,
    involved_hebrew.home_natural_area as involve_home_natural_area,
    involved_hebrew.home_natural_area_hebrew as involve_home_natural_area_hebrew,
    involved_hebrew.home_municipal_status as involve_home_municipal_status,
    involved_hebrew.home_municipal_status_hebrew as involve_home_municipal_status_hebrew,
    involved_hebrew.home_yishuv_shape as involve_home_yishuv_shape,
    involved_hebrew.home_yishuv_shape_hebrew as involve_home_yishuv_shape_hebrew,
    involved_hebrew.hospital_time,
    involved_hebrew.hospital_time_hebrew,
    involved_hebrew.medical_type,
    involved_hebrew.medical_type_hebrew,
    involved_hebrew.release_dest,
    involved_hebrew.release_dest_hebrew,
    involved_hebrew.safety_measures_use,
    involved_hebrew.safety_measures_use_hebrew,
    involved_hebrew.late_deceased,
    involved_hebrew.late_deceased_hebrew,
    involved_hebrew.car_id,
    involved_hebrew.involve_id,
    involved_hebrew.accident_year,
    involved_hebrew.accident_month,
    markers_hebrew.provider_code_hebrew,
    markers_hebrew.accident_timestamp,
    markers_hebrew.accident_type,
    markers_hebrew.accident_type_hebrew,
    markers_hebrew.accident_severity,
    markers_hebrew.accident_severity_hebrew,
    markers_hebrew.location_accuracy,
    markers_hebrew.location_accuracy_hebrew,
    markers_hebrew.road_type,
    markers_hebrew.road_type_hebrew,
    markers_hebrew.road_shape,
    markers_hebrew.road_shape_hebrew,
    markers_hebrew.day_type,
    markers_hebrew.day_type_hebrew,
    markers_hebrew.police_unit,
    markers_hebrew.police_unit_hebrew,
    markers_hebrew.one_lane,
    markers_hebrew.one_lane_hebrew,
    markers_hebrew.multi_lane,
    markers_hebrew.multi_lane_hebrew,
    markers_hebrew.speed_limit,
    markers_hebrew.speed_limit_hebrew,
    markers_hebrew.road_intactness,
    markers_hebrew.road_intactness_hebrew,
    markers_hebrew.road_width,
    markers_hebrew.road_width_hebrew,
    markers_hebrew.road_sign,
    markers_hebrew.road_sign_hebrew,
    markers_hebrew.road_light,
    markers_hebrew.road_light_hebrew,
    markers_hebrew.road_control,
    markers_hebrew.road_control_hebrew,
    markers_hebrew.weather,
    markers_hebrew.weather_hebrew,
    markers_hebrew.road_surface,
    markers_hebrew.road_surface_hebrew,
    markers_hebrew.road_object,
    markers_hebrew.road_object_hebrew,
    markers_hebrew.object_distance,
    markers_hebrew.object_distance_hebrew,
    markers_hebrew.didnt_cross,
    markers_hebrew.didnt_cross_hebrew,
    markers_hebrew.cross_mode,
    markers_hebrew.cross_mode_hebrew,
    markers_hebrew.cross_location,
    markers_hebrew.cross_location_hebrew,
    markers_hebrew.cross_direction,
    markers_hebrew.cross_direction_hebrew,
    markers_hebrew.road1,
    markers_hebrew.road2,
    markers_hebrew.km,
    markers_hebrew.km_raw,
    markers_hebrew.km_accurate,
    markers_hebrew.road_segment_id,
    markers_hebrew.road_segment_number,
    markers_hebrew.road_segment_name,
    markers_hebrew.road_segment_from_km,
    markers_hebrew.road_segment_to_km,
    markers_hebrew.road_segment_length_km,
    markers_hebrew.yishuv_symbol as accident_yishuv_symbol,
    markers_hebrew.yishuv_name as accident_yishuv_name,
    markers_hebrew.geo_area,
    markers_hebrew.geo_area_hebrew,
    markers_hebrew.day_night,
    markers_hebrew.day_night_hebrew,
    markers_hebrew.day_in_week,
    markers_hebrew.day_in_week_hebrew,
    markers_hebrew.traffic_light,
    markers_hebrew.traffic_light_hebrew,
    markers_hebrew.region as accident_region,
    markers_hebrew.region_hebrew as accident_region_hebrew,
    markers_hebrew.district as accident_district,
    markers_hebrew.district_hebrew as accident_district_hebrew,
    markers_hebrew.natural_area as accident_natural_area,
    markers_hebrew.natural_area_hebrew as accident_natural_area_hebrew,
    markers_hebrew.municipal_status as accident_municipal_status,
    markers_hebrew.municipal_status_hebrew as accident_municipal_status_hebrew,
    markers_hebrew.yishuv_shape as accident_yishuv_shape,
    markers_hebrew.yishuv_shape_hebrew as accident_yishuv_shape_hebrew,
    markers_hebrew.street1,
    markers_hebrew.street1_hebrew,
    markers_hebrew.street2,
    markers_hebrew.street2_hebrew,
    markers_hebrew.non_urban_intersection,
    markers_hebrew.non_urban_intersection_hebrew,
    markers_hebrew.non_urban_intersection_by_junction_number,
    markers_hebrew.accident_day,
    markers_hebrew.accident_hour_raw,
    markers_hebrew.accident_hour_raw_hebrew,
    markers_hebrew.accident_hour,
    markers_hebrew.accident_minute,
    markers_hebrew.geom,
    markers_hebrew.longitude,
    markers_hebrew.latitude,
    markers_hebrew.x,
    markers_hebrew.y,
    vehicles_hebrew.engine_volume,
    vehicles_hebrew.engine_volume_hebrew,
    vehicles_hebrew.manufacturing_year,
    vehicles_hebrew.driving_directions,
    vehicles_hebrew.driving_directions_hebrew,
    vehicles_hebrew.vehicle_status,
    vehicles_hebrew.vehicle_status_hebrew,
    vehicles_hebrew.vehicle_attribution,
    vehicles_hebrew.vehicle_attribution_hebrew,
    vehicles_hebrew.seats,
    vehicles_hebrew.total_weight,
    vehicles_hebrew.total_weight_hebrew,
    vehicles_hebrew.vehicle_type as vehicle_vehicle_type,
    vehicles_hebrew.vehicle_type_hebrew as vehicle_vehicle_type_hebrew,
    vehicles_hebrew.vehicle_damage,
    vehicles_hebrew.vehicle_damage_hebrew
     FROM involved_hebrew
     LEFT JOIN markers_hebrew ON involved_hebrew.provider_code = markers_hebrew.provider_code
                              AND involved_hebrew.accident_id = markers_hebrew.id
                              AND involved_hebrew.accident_year = markers_hebrew.accident_year
     LEFT JOIN vehicles_hebrew ON involved_hebrew.provider_code = vehicles_hebrew.provider_code
                              AND involved_hebrew.accident_id = vehicles_hebrew.accident_id
                              AND involved_hebrew.accident_year = vehicles_hebrew.accident_year
                              AND involved_hebrew.car_id = vehicles_hebrew.car_id ;"""


VEHICLES_MARKERS_HEBREW_VIEW = """ SELECT
    markers_hebrew.accident_timestamp,
    markers_hebrew.accident_type,
    markers_hebrew.accident_type_hebrew,
    markers_hebrew.accident_severity,
    markers_hebrew.accident_severity_hebrew,
    markers_hebrew.location_accuracy,
    markers_hebrew.location_accuracy_hebrew,
    markers_hebrew.road_type,
    markers_hebrew.road_type_hebrew,
    markers_hebrew.road_shape,
    markers_hebrew.road_shape_hebrew,
    markers_hebrew.day_type,
    markers_hebrew.day_type_hebrew,
    markers_hebrew.police_unit,
    markers_hebrew.police_unit_hebrew,
    markers_hebrew.one_lane,
    markers_hebrew.one_lane_hebrew,
    markers_hebrew.multi_lane,
    markers_hebrew.multi_lane_hebrew,
    markers_hebrew.speed_limit,
    markers_hebrew.speed_limit_hebrew,
    markers_hebrew.road_intactness,
    markers_hebrew.road_intactness_hebrew,
    markers_hebrew.road_width,
    markers_hebrew.road_width_hebrew,
    markers_hebrew.road_sign,
    markers_hebrew.road_sign_hebrew,
    markers_hebrew.road_light,
    markers_hebrew.road_light_hebrew,
    markers_hebrew.road_control,
    markers_hebrew.road_control_hebrew,
    markers_hebrew.weather,
    markers_hebrew.weather_hebrew,
    markers_hebrew.road_surface,
    markers_hebrew.road_surface_hebrew,
    markers_hebrew.road_object,
    markers_hebrew.road_object_hebrew,
    markers_hebrew.object_distance,
    markers_hebrew.object_distance_hebrew,
    markers_hebrew.didnt_cross,
    markers_hebrew.didnt_cross_hebrew,
    markers_hebrew.cross_mode,
    markers_hebrew.cross_mode_hebrew,
    markers_hebrew.cross_location,
    markers_hebrew.cross_location_hebrew,
    markers_hebrew.cross_direction,
    markers_hebrew.cross_direction_hebrew,
    markers_hebrew.road1,
    markers_hebrew.road2,
    markers_hebrew.km,
    markers_hebrew.km_raw,
    markers_hebrew.km_accurate,
    markers_hebrew.road_segment_id,
    markers_hebrew.road_segment_number,
    markers_hebrew.road_segment_name,
    markers_hebrew.road_segment_from_km,
    markers_hebrew.road_segment_to_km,
    markers_hebrew.road_segment_length_km,
    markers_hebrew.yishuv_symbol as accident_yishuv_symbol,
    markers_hebrew.yishuv_name as accident_yishuv_name,
    markers_hebrew.geo_area,
    markers_hebrew.geo_area_hebrew,
    markers_hebrew.day_night,
    markers_hebrew.day_night_hebrew,
    markers_hebrew.day_in_week,
    markers_hebrew.day_in_week_hebrew,
    markers_hebrew.traffic_light,
    markers_hebrew.traffic_light_hebrew,
    markers_hebrew.region as accident_region,
    markers_hebrew.region_hebrew as accident_region_hebrew,
    markers_hebrew.district as accident_district,
    markers_hebrew.district_hebrew as accident_district_hebrew,
    markers_hebrew.natural_area as accident_natural_area,
    markers_hebrew.natural_area_hebrew as accident_natural_area_hebrew,
    markers_hebrew.municipal_status as accident_municipal_status,
    markers_hebrew.municipal_status_hebrew as accident_municipal_status_hebrew,
    markers_hebrew.yishuv_shape as accident_yishuv_shape,
    markers_hebrew.yishuv_shape_hebrew as accident_yishuv_shape_hebrew,
    markers_hebrew.street1,
    markers_hebrew.street1_hebrew,
    markers_hebrew.street2,
    markers_hebrew.street2_hebrew,
    markers_hebrew.non_urban_intersection,
    markers_hebrew.non_urban_intersection_hebrew,
    markers_hebrew.non_urban_intersection_by_junction_number,
    markers_hebrew.accident_day,
    markers_hebrew.accident_hour_raw,
    markers_hebrew.accident_hour_raw_hebrew,
    markers_hebrew.accident_hour,
    markers_hebrew.accident_minute,
    markers_hebrew.accident_year,
    markers_hebrew.accident_month,
    markers_hebrew.geom,
    markers_hebrew.longitude,
    markers_hebrew.latitude,
    markers_hebrew.x,
    markers_hebrew.y,
    vehicles_hebrew.id,
    vehicles_hebrew.accident_id,
    vehicles_hebrew.provider_and_id,
    vehicles_hebrew.provider_code,
    vehicles_hebrew.file_type_police,
    vehicles_hebrew.engine_volume,
    vehicles_hebrew.engine_volume_hebrew,
    vehicles_hebrew.manufacturing_year,
    vehicles_hebrew.driving_directions,
    vehicles_hebrew.driving_directions_hebrew,
    vehicles_hebrew.vehicle_status,
    vehicles_hebrew.vehicle_status_hebrew,
    vehicles_hebrew.vehicle_attribution,
    vehicles_hebrew.vehicle_attribution_hebrew,
    vehicles_hebrew.seats,
    vehicles_hebrew.total_weight,
    vehicles_hebrew.total_weight_hebrew,
    vehicles_hebrew.vehicle_type,
    vehicles_hebrew.vehicle_type_hebrew,
    vehicles_hebrew.vehicle_damage,
    vehicles_hebrew.vehicle_damage_hebrew,
    vehicles_hebrew.car_id
   FROM vehicles_hebrew
    INNER JOIN markers_hebrew ON vehicles_hebrew.provider_code = markers_hebrew.provider_code
                             AND vehicles_hebrew.accident_id = markers_hebrew.id
                             AND vehicles_hebrew.accident_year = markers_hebrew.accident_year ;"""


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('accident_weathers',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('provider_and_id', sa.BigInteger(), nullable=True),
    sa.Column('provider_code', sa.Integer(), nullable=True),
    sa.Column('accident_id', sa.BigInteger(), nullable=True),
    sa.Column('accident_year', sa.Integer(), nullable=True),
    sa.Column('rain_rate', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['accident_id', 'provider_code', 'accident_year'], ['markers.id', 'markers.provider_code', 'markers.accident_year'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('accident_id_idx_accident_weather', 'accident_weathers', ['accident_id'], unique=False)
    op.create_index('provider_and_id_idx_accident_weather', 'accident_weathers', ['provider_and_id'], unique=False)

    # Don't see this view anywhere in the code but getting this when trying to delete the involved_markers_hebrew view
    # cannot drop view involved_markers_hebrew because other objects depend on it - view road_25 depends on view involved_markers_hebrew
    # probably some old leftover - removing
    op.execute("DROP VIEW IF EXISTS road_25")

    # we're really changing only the markers_hebrew view but we must remove and re create views dependent on it
    op.execute("DROP VIEW IF EXISTS involved_markers_hebrew")
    op.execute("DROP VIEW IF EXISTS vehicles_markers_hebrew")

    # the real change - remove the old view, create the new one with the weather data
    op.execute("DROP VIEW IF EXISTS markers_hebrew")
    op.execute(f"CREATE OR REPLACE VIEW markers_hebrew AS {MARKERS_HEBREW_VIEW_WITH_WEATHER}")

    # Recreate the dependent views
    op.execute(f"CREATE OR REPLACE VIEW vehicles_markers_hebrew AS {VEHICLES_MARKERS_HEBREW_VIEW}")
    op.execute(f"CREATE OR REPLACE VIEW involved_markers_hebrew AS {INVOLVED_HEBREW_MARKERS_HEBREW_VIEW}")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('accident_weathers')

    # we're really changing only the markers_hebrew view but we must remove and re create views dependent on it
    op.execute("DROP VIEW IF EXISTS involved_markers_hebrew")
    op.execute("DROP VIEW IF EXISTS vehicles_markers_hebrew")

    # the real change - remove the old view, create the new one without the weather data
    op.execute("DROP VIEW IF EXISTS markers_hebrew")
    op.execute(f"CREATE OR REPLACE VIEW markers_hebrew AS {MARKERS_HEBREW_VIEW_WITHOUT_WEATHER}")

    # Recreate the dependent views
    op.execute(f"CREATE OR REPLACE VIEW vehicles_markers_hebrew AS {VEHICLES_MARKERS_HEBREW_VIEW}")
    op.execute(f"CREATE OR REPLACE VIEW involved_markers_hebrew AS {INVOLVED_HEBREW_MARKERS_HEBREW_VIEW}")
    # ### end Alembic commands ###
