# Data-Safety schema
1. Data-Safety will use two new dedicated tables, `data_safety_involved` and `data_safety_accidents`
2. We will add fields to `cbs_cities` table that are needed for Data-Safety.
3. Data-Safety queries will use`streets` and `road_segments` for Hebrew names. The other Hebrew names will be obtained from dictionaries or arrays in memory.
## Tables
### `data_safety_involved` table:
```
    _id: int
    acc_provider_and_id: int
    injury_severity: int
    injured_type: int
    age_group: int
    sex: int
    # fields for filtering:
    age_group: int
    population_type: int
```
### `data_safety_accident` table:
```
    provider_and_id: int
    vehicle_types: Array of int? Bitmap?
    year: int. Do we want to calculate from time-stamp?
    timestamp: int
    month: int
    lat: float
    lon: float
    road_type: int
    speed_limit_type: int
    road_width_type: int
    multi_lane_type: int
    one_lane_type: int
    day_night: int
    # fields for filtering
    yishuv_symbol
    street1: int
    street2: int
    road: int
    road_segment: int
```
### `cbs_cities` table:
Consider adding the fields:
```
    id_osm: integer
    population: integer
```
## `/involved` Query
The query will join `data_safety_involved` and `data_safety_accident` using `accident_id`. In addition, the query will join 
* `cbs_cities`,
* `streets`,
* `road_segments`,

 for city data and hebrew names.
 
 Regarding the following data items, we will probably replace the integer values with hebrew strings using dictionaries or arrays in memory:
* `road_type`
* `one_lane`
* `multi_lane`
* `day_night`
* `speed_limit`
* `road_width`
* `injury_severity`
* `injured_type`
* `age_group`
* `sex`
* `age_group`
* `population_type`
* `month`
