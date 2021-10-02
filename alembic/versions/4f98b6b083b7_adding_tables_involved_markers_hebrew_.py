"""Adding tables involved_markers_hebrew_small, markers_hebrew_small and vehicles_markers_hebrew_small

Revision ID: 4f98b6b083b7
Revises: 312c9eb92e40
Create Date: 2021-10-02 06:09:03.808108

"""

# revision identifiers, used by Alembic.
revision = '4f98b6b083b7'
down_revision = '312c9eb92e40'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    create_involved_markers_hebrew_small()
    create_markers_hebrew_small()
    create_vehicles_markers_hebrew_small()


def create_vehicles_markers_hebrew_small():
    op.execute("""
-- Table: public.vehicles_markers_hebrew_small

DROP TABLE if exists public.vehicles_markers_hebrew_small;

CREATE TABLE IF NOT EXISTS public.vehicles_markers_hebrew_small
(
    accident_timestamp timestamp without time zone,
    accident_type integer,
--     accident_type_hebrew text COLLATE pg_catalog."default",
    accident_severity integer,
--     accident_severity_hebrew text COLLATE pg_catalog."default",
    location_accuracy integer,
--     location_accuracy_hebrew text COLLATE pg_catalog."default",
    road_type integer,
--     road_type_hebrew text COLLATE pg_catalog."default",
    road_shape integer,
--     road_shape_hebrew text COLLATE pg_catalog."default",
    day_type integer,
--     day_type_hebrew text COLLATE pg_catalog."default",
--     police_unit integer,
--     police_unit_hebrew text COLLATE pg_catalog."default",
    one_lane integer,
--     one_lane_hebrew text COLLATE pg_catalog."default",
    multi_lane integer,
--     multi_lane_hebrew text COLLATE pg_catalog."default",
    speed_limit integer,
--     speed_limit_hebrew text COLLATE pg_catalog."default",
--     road_intactness integer,
--     road_intactness_hebrew text COLLATE pg_catalog."default",
    road_width integer,
--     road_width_hebrew text COLLATE pg_catalog."default",
    road_sign integer,
--     road_sign_hebrew text COLLATE pg_catalog."default",
    road_light integer,
--     road_light_hebrew text COLLATE pg_catalog."default",
--     road_control integer,
--     road_control_hebrew text COLLATE pg_catalog."default",
    weather integer,
--     weather_hebrew text COLLATE pg_catalog."default",
    road_surface integer,
--     road_surface_hebrew text COLLATE pg_catalog."default",
--     road_object integer,
--     road_object_hebrew text COLLATE pg_catalog."default",
    object_distance integer,
--     object_distance_hebrew text COLLATE pg_catalog."default",
--     didnt_cross integer,
--     didnt_cross_hebrew text COLLATE pg_catalog."default",
--     cross_mode integer,
--     cross_mode_hebrew text COLLATE pg_catalog."default",
--     cross_location integer,
--     cross_location_hebrew text COLLATE pg_catalog."default",
--     cross_direction integer,
--     cross_direction_hebrew text COLLATE pg_catalog."default",
    road1 integer,
    road2 integer,
    km double precision,
--     km_raw text COLLATE pg_catalog."default",
    km_accurate boolean,
    road_segment_id integer,
    road_segment_number integer,
--     road_segment_name text COLLATE pg_catalog."default",
--     road_segment_from_km double precision,
--     road_segment_to_km double precision,
    road_segment_length_km double precision,
    accident_yishuv_symbol integer,
--     accident_yishuv_name text COLLATE pg_catalog."default",
    geo_area integer,
--     geo_area_hebrew text COLLATE pg_catalog."default",
    day_night integer,
--     day_night_hebrew text COLLATE pg_catalog."default",
--     day_in_week integer,
--     day_in_week_hebrew text COLLATE pg_catalog."default",
    traffic_light integer,
--     traffic_light_hebrew text COLLATE pg_catalog."default",
    accident_region integer,
--     accident_region_hebrew text COLLATE pg_catalog."default",
    accident_district integer,
--     accident_district_hebrew text COLLATE pg_catalog."default",
    accident_natural_area integer,
--     accident_natural_area_hebrew text COLLATE pg_catalog."default",
    accident_municipal_status integer,
--     accident_municipal_status_hebrew text COLLATE pg_catalog."default",
--     accident_yishuv_shape integer,
--     accident_yishuv_shape_hebrew text COLLATE pg_catalog."default",
    street1 integer,
--     street1_hebrew text COLLATE pg_catalog."default",
    street2 integer,
--     street2_hebrew text COLLATE pg_catalog."default",
    non_urban_intersection integer,
--     non_urban_intersection_hebrew text COLLATE pg_catalog."default",
--     non_urban_intersection_by_junction_number text COLLATE pg_catalog."default",
    accident_day integer,
    accident_hour_raw integer,
--     accident_hour_raw_hebrew text COLLATE pg_catalog."default",
    accident_hour integer,
--     accident_minute integer,
    accident_year integer NOT NULL,
--     accident_month integer,
--     geom geometry(Point),
--     longitude double precision,
--     latitude double precision,
--     x double precision,
--     y double precision,
    id bigint NOT NULL,
    accident_id bigint NOT NULL,
    provider_and_id bigint,
    provider_code integer NOT NULL,
--     file_type_police integer,
--     engine_volume integer,
--     engine_volume_hebrew text COLLATE pg_catalog."default",
--     manufacturing_year integer,
--     driving_directions integer,
--     driving_directions_hebrew text COLLATE pg_catalog."default",
    vehicle_status integer,
--     vehicle_status_hebrew text COLLATE pg_catalog."default",
    vehicle_attribution integer,
--     vehicle_attribution_hebrew text COLLATE pg_catalog."default",
    seats integer,
    total_weight integer,
--     total_weight_hebrew text COLLATE pg_catalog."default",
    vehicle_type integer,
--     vehicle_type_hebrew text COLLATE pg_catalog."default",
    vehicle_damage integer,
--     vehicle_damage_hebrew text COLLATE pg_catalog."default",
    car_id integer,
    CONSTRAINT vehicles_markers_hebrew_small_pkey PRIMARY KEY (accident_year, id, accident_id, provider_code)
    )
    WITH (
        OIDS = FALSE
        )
    TABLESPACE pg_default;

ALTER TABLE public.vehicles_markers_hebrew_small
    OWNER to anyway;
-- Index: idx_accident_timestamp

-- DROP INDEX public.idx_accident_timestamp;

CREATE INDEX idx_vehicles_markers_hebrew_accident_timestamp
    ON public.vehicles_markers_hebrew_small USING btree
    (accident_timestamp ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_vehicles_markers_hebrew_small_geom

-- DROP INDEX public.idx_vehicles_markers_hebrew_small_geom;

-- CREATE INDEX idx_vehicles_markers_hebrew_small_geom
--     ON public.vehicles_markers_hebrew_small USING gist
--     (geom)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_accident_severity

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_accident_severity;

CREATE INDEX ix_vehicles_markers_hebrew_small_accident_severity
    ON public.vehicles_markers_hebrew_small USING btree
    (accident_severity ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_accident_severity_hebrew

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_accident_severity_hebrew;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_accident_severity_hebrew
--     ON public.vehicles_markers_hebrew_small USING btree
--     (accident_severity_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_accident_type

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_accident_type;

CREATE INDEX ix_vehicles_markers_hebrew_small_accident_type
    ON public.vehicles_markers_hebrew_small USING btree
    (accident_type ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_accident_type_hebrew

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_accident_type_hebrew;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_accident_type_hebrew
--     ON public.vehicles_markers_hebrew_small USING btree
--     (accident_type_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_accident_year

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_accident_year;

CREATE INDEX ix_vehicles_markers_hebrew_small_accident_year
    ON public.vehicles_markers_hebrew_small USING btree
    (accident_year ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_accident_yishuv_name

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_accident_yishuv_name;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_accident_yishuv_name
--     ON public.vehicles_markers_hebrew_small USING btree
--     (accident_yishuv_name COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_geom

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_geom;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_geom
--     ON public.vehicles_markers_hebrew_small USING btree
--     (geom ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_road1

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_road1;

CREATE INDEX ix_vehicles_markers_hebrew_small_road1
    ON public.vehicles_markers_hebrew_small USING btree
    (road1 ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_road2

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_road2;

CREATE INDEX ix_vehicles_markers_hebrew_small_road2
    ON public.vehicles_markers_hebrew_small USING btree
    (road2 ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_road_segment_id

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_road_segment_id;

CREATE INDEX ix_vehicles_markers_hebrew_small_road_segment_id
    ON public.vehicles_markers_hebrew_small USING btree
    (road_segment_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_road_segment_name

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_road_segment_name;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_road_segment_name
--     ON public.vehicles_markers_hebrew_small USING btree
--     (road_segment_name COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_road_segment_number

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_road_segment_number;

CREATE INDEX ix_vehicles_markers_hebrew_small_road_segment_number
    ON public.vehicles_markers_hebrew_small USING btree
    (road_segment_number ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_street1_hebrew

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_street1_hebrew;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_street1_hebrew
--     ON public.vehicles_markers_hebrew_small USING btree
--     (street1_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_street2_hebrew

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_street2_hebrew;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_street2_hebrew
--     ON public.vehicles_markers_hebrew_small USING btree
--     (street2_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_vehicle_type

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_vehicle_type;

CREATE INDEX ix_vehicles_markers_hebrew_small_vehicle_type
    ON public.vehicles_markers_hebrew_small USING btree
    (vehicle_type ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_vehicles_markers_hebrew_small_vehicle_type_hebrew

-- DROP INDEX public.ix_vehicles_markers_hebrew_small_vehicle_type_hebrew;

-- CREATE INDEX ix_vehicles_markers_hebrew_small_vehicle_type_hebrew
--     ON public.vehicles_markers_hebrew_small USING btree
--     (vehicle_type_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;

insert into vehicles_markers_hebrew_small(
    accident_timestamp,
    accident_type,
    accident_severity,
    location_accuracy,
    road_type,
    road_shape,
    day_type,
    one_lane,
    multi_lane,
    speed_limit,
    road_width,
    road_sign,
    road_light,
    weather,
    road_surface,
    object_distance,
    road1,
    road2,
    km,
    km_accurate,
    road_segment_id,
    road_segment_number,
    road_segment_length_km,
    accident_yishuv_symbol,
    geo_area,
    day_night,
    traffic_light,
    accident_region,
    accident_district,
    accident_natural_area,
    accident_municipal_status,
    street1,
    street2,
    non_urban_intersection,
    accident_day,
    accident_hour_raw,
    accident_hour,
    accident_year,
    id,
    accident_id,
    provider_and_id,
    provider_code,
    vehicle_status,
    vehicle_attribution,
    seats,
    total_weight,
    vehicle_type,
    vehicle_damage,
    car_id)
    select
        accident_timestamp,
        accident_type,
        accident_severity,
        location_accuracy,
        road_type,
        road_shape,
        day_type,
        one_lane,
        multi_lane,
        speed_limit,
        road_width,
        road_sign,
        road_light,
        weather,
        road_surface,
        object_distance,
        road1,
        road2,
        km,
        km_accurate,
        road_segment_id,
        road_segment_number,
        road_segment_length_km,
        accident_yishuv_symbol,
        geo_area,
        day_night,
        traffic_light,
        accident_region,
        accident_district,
        accident_natural_area,
        accident_municipal_status,
        street1,
        street2,
        non_urban_intersection,
        accident_day,
        accident_hour_raw,
        accident_hour,
        accident_year,
        id,
        accident_id,
        provider_and_id,
        provider_code,
        vehicle_status,
        vehicle_attribution,
        seats,
        total_weight,
        vehicle_type,
        vehicle_damage,
        car_id
from vehicles_markers_hebrew;
    """)


def create_markers_hebrew_small():
    op.execute("""
-- Table: public.markers_hebrew_small

DROP TABLE IF EXISTS markers_hebrew_small;

CREATE TABLE IF NOT EXISTS public.markers_hebrew_small
(
    id bigint NOT NULL,
--     provider_and_id bigint,
    provider_code integer NOT NULL,
--     provider_code_hebrew text COLLATE pg_catalog."default",
--     file_type_police integer,
    accident_type integer,
--     accident_type_hebrew text COLLATE pg_catalog."default",
    accident_severity integer,
--     accident_severity_hebrew text COLLATE pg_catalog."default",
    accident_timestamp timestamp without time zone,
    location_accuracy integer,
--     location_accuracy_hebrew text COLLATE pg_catalog."default",
    road_type integer,
--     road_type_hebrew text COLLATE pg_catalog."default",
--     road_shape integer,
--     road_shape_hebrew text COLLATE pg_catalog."default",
--     day_type integer,
--     day_type_hebrew text COLLATE pg_catalog."default",
--     police_unit integer,
--     police_unit_hebrew text COLLATE pg_catalog."default",
--     one_lane integer,
--     one_lane_hebrew text COLLATE pg_catalog."default",
--     multi_lane integer,
--     multi_lane_hebrew text COLLATE pg_catalog."default",
--     speed_limit integer,
--     speed_limit_hebrew text COLLATE pg_catalog."default",
--     road_intactness integer,
--     road_intactness_hebrew text COLLATE pg_catalog."default",
--     road_width integer,
--     road_width_hebrew text COLLATE pg_catalog."default",
--     road_sign integer,
--     road_sign_hebrew text COLLATE pg_catalog."default",
    road_light integer,
--     road_light_hebrew text COLLATE pg_catalog."default",
--     road_control integer,
--     road_control_hebrew text COLLATE pg_catalog."default",
--     weather integer,
--     weather_hebrew text COLLATE pg_catalog."default",
--     road_surface integer,
--     road_surface_hebrew text COLLATE pg_catalog."default",
--     road_object integer,
--     road_object_hebrew text COLLATE pg_catalog."default",
--     object_distance integer,
--     object_distance_hebrew text COLLATE pg_catalog."default",
--     didnt_cross integer,
--     didnt_cross_hebrew text COLLATE pg_catalog."default",
--     cross_mode integer,
--     cross_mode_hebrew text COLLATE pg_catalog."default",
--     cross_location integer,
--     cross_location_hebrew text COLLATE pg_catalog."default",
--     cross_direction integer,
--     cross_direction_hebrew text COLLATE pg_catalog."default",
    road1 integer,
    road2 integer,
--     km double precision,
--     km_raw text COLLATE pg_catalog."default",
--     km_accurate boolean,
    road_segment_id integer,
    road_segment_number integer,
--     road_segment_name text COLLATE pg_catalog."default",
--     road_segment_from_km double precision,
--     road_segment_to_km double precision,
    road_segment_length_km double precision,
    yishuv_symbol integer,
--     yishuv_name text COLLATE pg_catalog."default",
    geo_area integer,
--     geo_area_hebrew text COLLATE pg_catalog."default",
    day_night integer,
--     day_night_hebrew text COLLATE pg_catalog."default",
--     day_in_week integer,
--     day_in_week_hebrew text COLLATE pg_catalog."default",
--     traffic_light integer,
--     traffic_light_hebrew text COLLATE pg_catalog."default",
    region integer,
--     region_hebrew text COLLATE pg_catalog."default",
    district integer,
--    district_hebrew text COLLATE pg_catalog."default",
--    natural_area integer,
--    natural_area_hebrew text COLLATE pg_catalog."default",
--    municipal_status integer,
--    municipal_status_hebrew text COLLATE pg_catalog."default",
--    yishuv_shape integer,
--    yishuv_shape_hebrew text COLLATE pg_catalog."default",
    street1 integer,
--     street1_hebrew text COLLATE pg_catalog."default",
    street2 integer,
--     street2_hebrew text COLLATE pg_catalog."default",
--     house_number integer,
    non_urban_intersection integer,
    non_urban_intersection_hebrew text COLLATE pg_catalog."default",
    non_urban_intersection_by_junction_number text COLLATE pg_catalog."default",
    urban_intersection integer,
    accident_year integer NOT NULL,
--     accident_month integer,
--     accident_day integer,
--     accident_hour_raw integer,
--     accident_hour_raw_hebrew text COLLATE pg_catalog."default",
--     accident_hour integer,
--     accident_minute integer,
--     geom geometry(Point),
--     longitude double precision,
--     latitude double precision,
--     x double precision,
--     y double precision,
    CONSTRAINT markers_hebrew_fast_pkey PRIMARY KEY (id, provider_code, accident_year)
    )
    WITH (
        OIDS = FALSE
        )
    TABLESPACE pg_default;

ALTER TABLE public.markers_hebrew_small
    OWNER to anyway;
-- Index: idx_markers_hebrew_small_geom

-- DROP INDEX public.idx_markers_hebrew_small_geom;

-- CREATE INDEX idx_markers_hebrew_small_geom
--     ON public.markers_hebrew_small USING gist
--     (geom)
--     TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_accident_severity

-- DROP INDEX public.ix_markers_hebrew_small_accident_severity;

CREATE INDEX ix_markers_hebrew_small_accident_severity
    ON public.markers_hebrew_small USING btree
    (accident_severity ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_accident_severity_hebrew

-- DROP INDEX public.ix_markers_hebrew_small_accident_severity_hebrew;

-- CREATE INDEX ix_markers_hebrew_small_accident_severity_hebrew
--     ON public.markers_hebrew_small USING btree
--     (accident_severity_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_accident_timestamp

-- DROP INDEX public.ix_markers_hebrew_small_accident_timestamp;

CREATE INDEX ix_markers_hebrew_small_accident_timestamp
    ON public.markers_hebrew_small USING btree
    (accident_timestamp ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_accident_type

-- DROP INDEX public.ix_markers_hebrew_small_accident_type;

CREATE INDEX ix_markers_hebrew_small_accident_type
    ON public.markers_hebrew_small USING btree
    (accident_type ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_accident_type_hebrew

-- DROP INDEX public.ix_markers_hebrew_small_accident_type_hebrew;

-- CREATE INDEX ix_markers_hebrew_small_accident_type_hebrew
--     ON public.markers_hebrew_small USING btree
--     (accident_type_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_accident_year

-- DROP INDEX public.ix_markers_hebrew_small_accident_year;

CREATE INDEX ix_markers_hebrew_small_accident_year
    ON public.markers_hebrew_small USING btree
    (accident_year ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_geom

-- DROP INDEX public.ix_markers_hebrew_small_geom;

-- CREATE INDEX ix_markers_hebrew_small_geom
--     ON public.markers_hebrew_small USING btree
--     (geom ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_road1

-- DROP INDEX public.ix_markers_hebrew_small_road1;

CREATE INDEX ix_markers_hebrew_small_road1
    ON public.markers_hebrew_small USING btree
    (road1 ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_road2

-- DROP INDEX public.ix_markers_hebrew_small_road2;

CREATE INDEX ix_markers_hebrew_small_road2
    ON public.markers_hebrew_small USING btree
    (road2 ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_road_segment_id

-- DROP INDEX public.ix_markers_hebrew_small_road_segment_id;

CREATE INDEX ix_markers_hebrew_small_road_segment_id
    ON public.markers_hebrew_small USING btree
    (road_segment_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_road_segment_name

-- DROP INDEX public.ix_markers_hebrew_small_road_segment_name;

-- CREATE INDEX ix_markers_hebrew_small_road_segment_name
--     ON public.markers_hebrew_small USING btree
--     (road_segment_name COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_road_segment_number

-- DROP INDEX public.ix_markers_hebrew_small_road_segment_number;

CREATE INDEX ix_markers_hebrew_small_road_segment_number
    ON public.markers_hebrew_small USING btree
    (road_segment_number ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_street1_hebrew

-- DROP INDEX public.ix_markers_hebrew_small_street1_hebrew;

-- CREATE INDEX ix_markers_hebrew_small_street1_hebrew
--     ON public.markers_hebrew_small USING btree
--     (street1_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_street2_hebrew

-- DROP INDEX public.ix_markers_hebrew_small_street2_hebrew;

-- CREATE INDEX ix_markers_hebrew_small_street2_hebrew
--     ON public.markers_hebrew_small USING btree
--     (street2_hebrew COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;
-- Index: ix_markers_hebrew_small_yishuv_name

-- DROP INDEX public.ix_markers_hebrew_small_yishuv_name;

-- CREATE INDEX ix_markers_hebrew_small_yishuv_name
--     ON public.markers_hebrew_small USING btree
--     (yishuv_name COLLATE pg_catalog."default" ASC NULLS LAST)
--     TABLESPACE pg_default;

insert into markers_hebrew_small(
    id,
    provider_code,
    accident_type,
    accident_severity,
    accident_timestamp,
    location_accuracy,
    road_light,
    road1,
    road2,
    road_segment_id,
    road_segment_number,
    road_segment_length_km,
    yishuv_symbol,
    geo_area,
    day_night,
    region,
    district,
    street1,
    street2,
    non_urban_intersection,
    non_urban_intersection_hebrew,
    non_urban_intersection_by_junction_number,
    urban_intersection,
    accident_year)
select
    id,
    provider_code,
    accident_type,
    accident_severity,
    accident_timestamp,
    location_accuracy,
    road_light,
    road1,
    road2,
    road_segment_id,
    road_segment_number,
    road_segment_length_km,
    yishuv_symbol,
    geo_area,
    day_night,
    region,
    district,
    street1,
    street2,
    non_urban_intersection,
    non_urban_intersection_hebrew,
    non_urban_intersection_by_junction_number,
    urban_intersection,
    accident_year
from markers_hebrew;
    """)


def create_involved_markers_hebrew_small():
    op.execute("""
DROP TABLE IF EXISTS involved_markers_hebrew_small;

CREATE TABLE involved_markers_hebrew_small
(
    accident_id bigint NOT NULL,
    provider_and_id bigint,
    provider_code integer NOT NULL,
    involved_type integer,
    age_group integer,
    sex integer,
    involve_vehicle_type integer,
    involve_yishuv_symbol integer,
    injury_severity integer,
    injured_type integer,
    involve_id integer NOT NULL,
    accident_year integer NOT NULL,
    accident_timestamp timestamp without time zone,
    accident_type integer,
    accident_severity integer,
    location_accuracy integer,
    road_type integer,
    road_shape integer,
    road1 integer,
    road2 integer,
    km double precision,
    road_segment_id integer,
    road_segment_number integer,
    accident_yishuv_symbol integer,
    geo_area integer,
    day_night integer,
    traffic_light integer,
    accident_region integer,
    accident_district integer,
    street1 integer,
    street2 integer,
    non_urban_intersection integer,
    vehicle_vehicle_type integer,
    vehicle_damage integer,
    CONSTRAINT involved_markers_hebrew_small_pkey PRIMARY KEY (accident_id, provider_code, involve_id, accident_year)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

ALTER TABLE involved_markers_hebrew_small
    OWNER to anyway;
-- Index: idx_injury_severity

-- DROP INDEX public.idx_injury_severity;

CREATE INDEX idx_involved_markers_hebrew_small_injury_severity
    ON involved_markers_hebrew_small USING btree
    (injury_severity ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_involved_markers_hebrew__ziv

-- DROP INDEX public.idx_involved_markers_hebrew_small_ziv;

CREATE INDEX idx_involved_markers_hebrew_small_ziv
    ON involved_markers_hebrew_small USING btree
    (accident_timestamp ASC NULLS LAST, provider_code ASC NULLS LAST, injury_severity ASC NULLS LAST, road1 ASC NULLS LAST, road2 ASC NULLS LAST, age_group ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX idx_involved_markers_hebrew_small_year_ziv
    ON involved_markers_hebrew_small USING btree
    (accident_year ASC NULLS LAST, provider_code ASC NULLS LAST, injury_severity ASC NULLS LAST, road1 ASC NULLS LAST, road2 ASC NULLS LAST, age_group ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: idx_involved_markers_hebrew_geom

-- DROP INDEX public.idx_involved_markers_hebrew_geom;

-- Index: idx_provider_code

-- DROP INDEX public.idx_provider_code;

CREATE INDEX idx_involved_markers_hebrew_small_provider_code
    ON involved_markers_hebrew_small USING btree
    (provider_code ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_accident_severity

-- DROP INDEX public.ix_involved_markers_hebrew_accident_severity;

CREATE INDEX ix_involved_markers_hebrew_small_accident_severity
    ON involved_markers_hebrew_small USING btree
    (accident_severity ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_accident_severity_hebrew

-- DROP INDEX public.ix_involved_markers_hebrew_accident_severity_hebrew;

-- Index: ix_involved_markers_hebrew_accident_timestamp

-- DROP INDEX public.ix_involved_markers_hebrew_accident_timestamp;

CREATE INDEX ix_involved_markers_hebrew_small_accident_timestamp
    ON involved_markers_hebrew_small USING btree
    (accident_timestamp ASC NULLS LAST)
    TABLESPACE pg_default;

CREATE INDEX ix_involved_markers_hebrew_small_accident_year
    ON involved_markers_hebrew_small USING btree
    (accident_year ASC NULLS LAST)
    TABLESPACE pg_default;

-- Index: ix_involved_markers_hebrew_accident_year

-- DROP INDEX public.ix_involved_markers_hebrew_accident_year;

-- Index: ix_involved_markers_hebrew_accident_yishuv_name

-- DROP INDEX public.ix_involved_markers_hebrew_accident_yishuv_name;

-- Index: ix_involved_markers_hebrew_geom

-- DROP INDEX public.ix_involved_markers_hebrew_geom;

-- Index: ix_involved_markers_hebrew_involve_vehicle_type

-- DROP INDEX public.ix_involved_markers_hebrew_involve_vehicle_type;

CREATE INDEX ix_involved_markers_hebrew_small_involve_vehicle_type
    ON involved_markers_hebrew_small USING btree
    (involve_vehicle_type ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_involve_vehicle_type_hebrew

-- DROP INDEX public.ix_involved_markers_hebrew_involve_vehicle_type_hebrew;

-- Index: ix_involved_markers_hebrew_involved_type

-- DROP INDEX public.ix_involved_markers_hebrew_involved_type;

CREATE INDEX ix_involved_markers_hebrew_small_involved_type
    ON involved_markers_hebrew_small USING btree
    (involved_type ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_involved_type_hebrew

-- DROP INDEX public.ix_involved_markers_hebrew_involved_type_hebrew;

-- Index: ix_involved_markers_hebrew_road1

-- DROP INDEX public.ix_involved_markers_hebrew_road1;

CREATE INDEX ix_involved_markers_hebrew_small_road1
    ON involved_markers_hebrew_small USING btree
    (road1 ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_road2

-- DROP INDEX public.ix_involved_markers_hebrew_road2;

CREATE INDEX ix_involved_markers_hebrew_small_road2
    ON involved_markers_hebrew_small USING btree
    (road2 ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_road_segment_id

-- DROP INDEX public.ix_involved_markers_hebrew_road_segment_id;

CREATE INDEX ix_involved_markers_hebrew_small_road_segment_id
    ON involved_markers_hebrew_small USING btree
    (road_segment_id ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_road_segment_name

-- DROP INDEX public.ix_involved_markers_hebrew_road_segment_name;

-- Index: ix_involved_markers_hebrew_road_segment_number

-- DROP INDEX public.ix_involved_markers_hebrew_road_segment_number;

CREATE INDEX ix_involved_markers_hebrew_small_road_segment_number
    ON involved_markers_hebrew_small USING btree
    (road_segment_number ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_road_type

-- DROP INDEX public.ix_involved_markers_hebrew_road_type;

CREATE INDEX ix_involved_markers_hebrew_small_road_type
    ON involved_markers_hebrew_small USING btree
    (road_type ASC NULLS LAST)
    TABLESPACE pg_default;
-- Index: ix_involved_markers_hebrew_road_type_hebrew

-- DROP INDEX public.ix_involved_markers_hebrew_road_type_hebrew;

-- Index: ix_involved_markers_hebrew_street1_hebrew

-- DROP INDEX public.ix_involved_markers_hebrew_street1_hebrew;

-- Index: ix_involved_markers_hebrew_street2_hebrew

-- DROP INDEX public.ix_involved_markers_hebrew_street2_hebrew;
insert into involved_markers_hebrew_small(accident_id, provider_and_id, provider_code, involved_type, age_group, sex, involve_vehicle_type, involve_yishuv_symbol, injury_severity, injured_type, involve_id, accident_year, accident_timestamp, accident_type, accident_severity, location_accuracy, road_type, road_shape, road1, road2, km, road_segment_id, road_segment_number, accident_yishuv_symbol, geo_area, day_night, traffic_light, accident_region, accident_district, street1, street2, non_urban_intersection, vehicle_vehicle_type,  vehicle_damage)
select
    accident_id,
    provider_and_id,
    provider_code,
    involved_type,
    age_group,
    sex,
    involve_vehicle_type,
    involve_yishuv_symbol,
    injury_severity,
    injured_type,
    involve_id,
    accident_year,
    accident_timestamp,
    accident_type,
    accident_severity,
    location_accuracy,
    road_type,
    road_shape,
    road1,
    road2,
    km,
    road_segment_id,
    road_segment_number,
    accident_yishuv_symbol,
    geo_area,
    day_night,
    traffic_light,
    accident_region,
    accident_district,
    street1,
    street2,
    non_urban_intersection,
    vehicle_vehicle_type,
    vehicle_damage
from public.involved_markers_hebrew;
      """)


def downgrade():
    op.execute("""
DROP TABLE IF EXISTS involved_markers_hebrew_small;
DROP TABLE IF EXISTS vehicles_markers_hebrew_small;
DROP TABLE IF EXISTS markers_hebrew_small;
    """)
