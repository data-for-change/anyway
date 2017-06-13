"""
Get accidents around a location. The input is currently the schools CSV list obtained by the project's team
This script is a standalone (using the API itself and not directly to DB) and can be run without setting up dev env.
Script support python 2.7+
To run:
python accidents_around_location.py <input_file> [flags]

"""
import argparse
import io

import math

import requests

DEFAULT_NAME_COL = 4
DEFAULT_CITY_COL = 3
DEFAULT_LON_COL = 10
DEFAULT_LAT_COL = 11
START_DATE_EPOCH = 1325376000
END_DATE_EPOCH = 1735689600
START_DATE = "2012-01-01"
END_DATE = "2025-01-01"

ANYWAY_MARKERS_FORMAT = "https://www.anyway.co.il/markers?ne_lat={lat_max}&ne_lng={lon_max}&sw_lat={lat_min}&sw_lng={lon_min}&zoom=17&thin_markers=false&start_date={start_date}&end_date={end_date}&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0"
ANYWAY_UI_FORMAT = "https://www.anyway.co.il/?zoom=17&start_date={start_date}&end_date={end_date}&lat={lat}&lon={lon}&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=1&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0"


def get_bounding_box(lat, lon, distance_in_km):

    lat = math.radians(lat)
    lon = math.radians(lon)

    radius = 6371
    # Radius of the parallel at given latitude
    parallel_radius = radius*math.cos(lat)

    lat_min = lat - distance_in_km/radius
    lat_max = lat + distance_in_km/radius
    lon_min = lon - distance_in_km/parallel_radius
    lon_max = lon + distance_in_km/parallel_radius
    rad2deg = math.degrees

    return rad2deg(lat_min), rad2deg(lon_min), rad2deg(lat_max), rad2deg(lon_max)


def parse_csv_line(str_row):
    row = str_row.split(',')
    try:
        lat = float(row[DEFAULT_LAT_COL])
        lon = float(row[DEFAULT_LON_COL])
    except ValueError:
        return row[DEFAULT_CITY_COL], row[DEFAULT_NAME_COL], None, None
    return row[DEFAULT_CITY_COL], row[DEFAULT_NAME_COL], lat, lon


def calc_markers(markers):
    DEADLY_WEIGHT = 7
    HARD_WEIGHT = 5
    LIGHT_WEIGHT = 1
    severities = [x.get("severity", 1) for x in markers]
    light_count = severities.count(3)
    hard_count = severities.count(2)
    deadly_count = severities.count(1)

    return {'grade': deadly_count * DEADLY_WEIGHT + hard_count * HARD_WEIGHT + light_count * LIGHT_WEIGHT,
            'light': light_count,
            'hard': hard_count,
            'deadly': deadly_count
            }


def get_accidents_around(city, name, lat, lon, distance, pedestrians_only, file_obj):
    lat_min, lon_min, lat_max, lon_max = get_bounding_box(lat, lon, distance)
    acc_type = 0
    if pedestrians_only:
        acc_type = 1
    markers_url = ANYWAY_MARKERS_FORMAT.format(lat_min=lat_min,
                                               lat_max=lat_max,
                                               lon_min=lon_min,
                                               lon_max=lon_max,
                                               start_date=START_DATE_EPOCH,
                                               end_date=END_DATE_EPOCH,
                                               acc_type=acc_type)
    ui_url = ANYWAY_UI_FORMAT.format(lat=lat,
                                     lon=lon,
                                     start_date=START_DATE,
                                     end_date=END_DATE,
                                     acc_type=acc_type)
    markers_res = requests.get(markers_url)
    try:
        markers = markers_res.json()['markers']
    except Exception as e:
        print 'failed to parse:', markers_res.text
        raise e
    markers_data = calc_markers(markers)
    file_obj.write(u'{city},{name},{grade},{deadly},{hard},{light},{ui_url}\n'.format(city=city,
                                                                                      name=name,
                                                                                      grade=markers_data['grade'],
                                                                                      ui_url=ui_url,
                                                                                      deadly=markers_data['deadly'],
                                                                                      hard=markers_data['hard'],
                                                                                      light=markers_data['light']))


def main(csv_filename, distance, pedestrian_only, output_filename):
    with io.open(csv_filename, 'r', encoding='utf-8') as csvfile:
        with io.open(output_filename, 'w', encoding='utf-8') as out_file:
            out_file.write(u'CITY,NAME,GRADE,DEADLY,HARD,LIGHT,UI_URL\n')
            i = 0
            for row in csvfile:
                (city, name, lat, lon) = parse_csv_line(row.strip())
                print u'{0} working on {1}'.format(i, name)
                i += 1
                if lat is None or lon is None:
                    continue
                get_accidents_around(city, name, lat, lon, distance, pedestrian_only, out_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_filename', metavar='csv_filename', type=str, help='input csv file path')

    #TODO: augment to any CSV that contains relevant data
    #TODO: add argument to date
    parser.add_argument('--distance', default=0.5, help= 'float In KM. Default is 0.5 (500m)')
    parser.add_argument('--output_file', default='output.csv', help='output file of the results. Default is output.csv')
    parser.add_argument('--pedestrians_only', action='store_true', default=False,
                        help='use the flag for pedestrian only results')
    args = parser.parse_args()
    main(args.csv_filename, args.distance, args.pedestrians_only, args.output_file)
