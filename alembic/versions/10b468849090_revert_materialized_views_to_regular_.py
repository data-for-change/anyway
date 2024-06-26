"""revert_materialized_views_to_regular_views

Revision ID: 10b468849090
Revises: 5860a2ed5ffc
Create Date: 2020-06-16 17:52:04.000072

"""

# revision identifiers, used by Alembic.
revision = '10b468849090'
down_revision = '5860a2ed5ffc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

MARKERS_HEBREW_VIEW = """SELECT markers.id,
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

INVOLVED_HEBREW_VIEW = """SELECT
    involved.accident_id,
    involved.provider_and_id,
    involved.provider_code,
    involved.file_type_police,
    involved.involved_type,
    involved_type.involved_type_hebrew,
    involved.license_acquiring_date,
    involved.age_group,
    age_group.age_group_hebrew,
    involved.sex,
    sex.sex_hebrew,
    involved.vehicle_type,
    vehicle_type.vehicle_type_hebrew,
    involved.safety_measures,
    safety_measures.safety_measures_hebrew,
    involved.involve_yishuv_symbol,
    involved.involve_yishuv_name,
    involved.injury_severity,
    injury_severity.injury_severity_hebrew,
    involved.injured_type,
    injured_type.injured_type_hebrew,
    involved.injured_position,
    injured_position.injured_position_hebrew,
    involved.population_type,
    population_type.population_type_hebrew,
    involved.home_region,
    region.region_hebrew as home_region_hebrew,
    involved.home_district,
    district.district_hebrew AS home_district_hebrew,
    involved.home_natural_area,
    natural_area.natural_area_hebrew AS home_natural_area_hebrew,
    involved.home_municipal_status,
    municipal_status.municipal_status_hebrew as home_municipal_status_hebrew,
    involved.home_yishuv_shape,
    yishuv_shape.yishuv_shape_hebrew AS home_yishuv_shape_hebrew,
    involved.hospital_time,
    hospital_time.hospital_time_hebrew,
    involved.medical_type,
    medical_type.medical_type_hebrew,
    involved.release_dest,
    release_dest.release_dest_hebrew,
    involved.safety_measures_use,
    safety_measures_use.safety_measures_use_hebrew,
    involved.late_deceased,
    late_deceased.late_deceased_hebrew,
    involved.car_id,
    involved.involve_id,
    involved.accident_year,
    involved.accident_month
   FROM involved
     LEFT JOIN involved_type ON involved.involved_type = involved_type.id AND involved.accident_year = involved_type.year AND involved.provider_code = involved_type.provider_code
     LEFT JOIN age_group ON involved.age_group = age_group.id  AND involved.accident_year = age_group.year AND involved.provider_code = age_group.provider_code
     LEFT JOIN sex ON involved.sex = sex.id AND involved.accident_year = sex.year AND involved.provider_code = sex.provider_code
     LEFT JOIN vehicle_type ON involved.vehicle_type = vehicle_type.id AND involved.accident_year = vehicle_type.year AND involved.provider_code = vehicle_type.provider_code
     LEFT JOIN safety_measures ON involved.safety_measures = safety_measures.id AND involved.accident_year = safety_measures.year AND involved.provider_code = safety_measures.provider_code
     LEFT JOIN injury_severity ON involved.injury_severity = injury_severity.id AND involved.accident_year = injury_severity.year AND involved.provider_code = injury_severity.provider_code
     LEFT JOIN injured_type ON involved.injured_type = injured_type.id AND involved.accident_year = injured_type.year AND involved.provider_code = injured_type.provider_code
     LEFT JOIN injured_position ON involved.injured_position = injured_position.id AND involved.accident_year = injured_position.year AND involved.provider_code = injured_position.provider_code
     LEFT JOIN population_type ON involved.population_type = population_type.id AND involved.accident_year = population_type.year AND involved.provider_code = population_type.provider_code
     LEFT JOIN region ON involved.home_region = region.id AND involved.accident_year = region.year AND involved.provider_code = region.provider_code
     LEFT JOIN district ON involved.home_district = district.id AND involved.accident_year = district.year AND involved.provider_code = district.provider_code
     LEFT JOIN natural_area ON involved.home_natural_area = natural_area.id AND involved.accident_year = natural_area.year AND involved.provider_code = natural_area.provider_code
     LEFT JOIN municipal_status ON involved.home_municipal_status = municipal_status.id AND involved.accident_year = municipal_status.year AND involved.provider_code = municipal_status.provider_code
     LEFT JOIN yishuv_shape ON involved.home_yishuv_shape = yishuv_shape.id AND involved.accident_year = yishuv_shape.year AND involved.provider_code = yishuv_shape.provider_code
     LEFT JOIN hospital_time ON involved.hospital_time = hospital_time.id AND involved.accident_year = hospital_time.year AND involved.provider_code = hospital_time.provider_code
     LEFT JOIN medical_type ON involved.medical_type = medical_type.id AND involved.accident_year = medical_type.year AND involved.provider_code = medical_type.provider_code
     LEFT JOIN release_dest ON involved.release_dest = release_dest.id AND involved.accident_year = release_dest.year AND involved.provider_code = release_dest.provider_code
     LEFT JOIN safety_measures_use ON involved.safety_measures_use = safety_measures_use.id AND involved.accident_year = safety_measures_use.year AND involved.provider_code = safety_measures_use.provider_code
     LEFT JOIN late_deceased ON involved.late_deceased = late_deceased.id AND involved.accident_year = late_deceased.year AND involved.provider_code = late_deceased.provider_code;"""

VEHICLES_HEBREW_VIEW = """ SELECT
    vehicles.id,
    vehicles.accident_id,
    vehicles.provider_and_id,
    vehicles.provider_code,
    vehicles.file_type_police,
    vehicles.car_id,
    vehicles.engine_volume,
    engine_volume.engine_volume_hebrew,
    vehicles.manufacturing_year,
    vehicles.driving_directions,
    driving_directions.driving_directions_hebrew,
    vehicles.vehicle_status,
    vehicle_status.vehicle_status_hebrew,
    vehicles.vehicle_attribution,
    vehicle_attribution.vehicle_attribution_hebrew,
    vehicles.seats,
    vehicles.total_weight,
    total_weight.total_weight_hebrew,
    vehicles.vehicle_type,
    vehicle_type.vehicle_type_hebrew,
    vehicles.vehicle_damage,
    vehicle_damage.vehicle_damage_hebrew,
    vehicles.accident_year,
    vehicles.accident_month
   FROM vehicles
     LEFT JOIN engine_volume ON vehicles.engine_volume = engine_volume.id AND vehicles.accident_year = engine_volume.year AND vehicles.provider_code = engine_volume.provider_code
     LEFT JOIN driving_directions ON vehicles.driving_directions = driving_directions.id AND vehicles.accident_year = driving_directions.year AND vehicles.provider_code = driving_directions.provider_code
     LEFT JOIN vehicle_status ON vehicles.vehicle_status = vehicle_status.id AND vehicles.accident_year = vehicle_status.year AND vehicles.provider_code = vehicle_status.provider_code
     LEFT JOIN vehicle_attribution ON vehicles.vehicle_attribution = vehicle_attribution.id AND vehicles.accident_year = vehicle_attribution.year AND vehicles.provider_code = vehicle_attribution.provider_code
     LEFT JOIN total_weight ON vehicles.total_weight = total_weight.id AND vehicles.accident_year = total_weight.year AND vehicles.provider_code = total_weight.provider_code
     LEFT JOIN vehicle_type ON vehicles.vehicle_type = vehicle_type.id AND vehicles.accident_year = vehicle_type.year AND vehicles.provider_code = vehicle_type.provider_code
     LEFT JOIN vehicle_damage ON vehicles.vehicle_damage = vehicle_damage.id AND vehicles.accident_year = vehicle_damage.year AND vehicles.provider_code = vehicle_damage.provider_code;"""

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
    op.execute("DROP MATERIALIZED VIEW IF EXISTS involved_markers_hebrew")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vehicles_markers_hebrew")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS markers_hebrew")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS involved_hebrew")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vehicles_hebrew")
    op.execute(f"CREATE OR REPLACE VIEW vehicles_hebrew AS {VEHICLES_HEBREW_VIEW}")
    op.execute(f"CREATE OR REPLACE VIEW involved_hebrew AS {INVOLVED_HEBREW_VIEW}")
    op.execute(f"CREATE OR REPLACE VIEW markers_hebrew AS {MARKERS_HEBREW_VIEW}")
    op.execute(f"CREATE OR REPLACE VIEW vehicles_markers_hebrew AS {VEHICLES_MARKERS_HEBREW_VIEW}")
    op.execute(f"CREATE OR REPLACE VIEW involved_markers_hebrew AS {INVOLVED_HEBREW_MARKERS_HEBREW_VIEW}")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP VIEW IF EXISTS involved_markers_hebrew")
    op.execute("DROP VIEW IF EXISTS vehicles_markers_hebrew")
    op.execute("DROP VIEW IF EXISTS markers_hebrew")
    op.execute("DROP VIEW IF EXISTS involved_hebrew")
    op.execute("DROP VIEW IF EXISTS vehicles_hebrew")
    op.execute(f"CREATE MATERIALIZED VIEW IF NOT EXISTS vehicles_hebrew AS {VEHICLES_HEBREW_VIEW}")
    op.execute(f"CREATE MATERIALIZED VIEW IF NOT EXISTS involved_hebrew AS {INVOLVED_HEBREW_VIEW}")
    op.execute(f"CREATE MATERIALIZED VIEW IF NOT EXISTS markers_hebrew AS {MARKERS_HEBREW_VIEW}")
    op.execute(f"CREATE MATERIALIZED VIEW IF NOT EXISTS vehicles_markers_hebrew"
               f" AS {VEHICLES_MARKERS_HEBREW_VIEW}")
    op.execute(f"CREATE MATERIALIZED VIEW IF NOT EXISTS involved_marker"
               f"s_hebrew AS {INVOLVED_HEBREW_MARKERS_HEBREW_VIEW}")
    # ### end Alembic commands ###
