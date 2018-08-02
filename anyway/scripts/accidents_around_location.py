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
from datetime import datetime

DEFAULT_NAME_COL = 4
DEFAULT_CITY_COL = 3
DEFAULT_LON_COL = 10
DEFAULT_LAT_COL = 11
DATE_INPUT_FORMAT = '%d-%m-%Y'
DATE_URL_FORMAT = '%Y-%m-%d'

ANYWAY_MARKERS_FORMAT = "http://anyway-unstable.herokuapp.com/markers?ne_lat={lat_max}&ne_lng={lon_max}&sw_lat={lat_min}&sw_lng={lon_min}&zoom=17&thin_markers=false&start_date={start_date}&end_date={end_date}&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0"
ANYWAY_UI_FORMAT = "https://www.anyway.co.il/?zoom={zoom}&start_date={start_date}&end_date={end_date}&lat={lat}&lon={lon}&show_fatal=1&show_severe=1&show_light=1&approx=1&accurate=1&show_markers=1&show_discussions=&show_urban=3&show_intersection=3&show_lane=3&show_day=7&show_holiday=0&show_time=24&start_time=25&end_time=25&weather=0&road=0&separation=0&surface=0&acctype={acc_type}&controlmeasure=0&district=0&case_type=0"


def get_timestamp_since_epoch_in_seconds(dt):
    (dt - datetime(1970, 1, 1)).total_seconds()
    return int((dt - datetime(1970, 1, 1)).total_seconds())


def valid_date(date_string):
    try:
        return datetime.strptime(date_string, DATE_INPUT_FORMAT)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(date_string)
        raise argparse.ArgumentTypeError(msg)


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


def get_accidents_around(city, name, lat, lon, start_date, end_date, distance, pedestrians_only):
    lat_min, lon_min, lat_max, lon_max = get_bounding_box(lat, lon, distance)
    acc_type = 0
    if pedestrians_only:
        acc_type = 1
    zoom = 17
    if distance <= 0.1:
        zoom = 18

    markers_url = ANYWAY_MARKERS_FORMAT.format(lat_min=lat_min,
                                               lat_max=lat_max,
                                               lon_min=lon_min,
                                               lon_max=lon_max,
                                               start_date=get_timestamp_since_epoch_in_seconds(start_date),
                                               end_date=get_timestamp_since_epoch_in_seconds(end_date),
                                               acc_type=acc_type)
    ui_url = ANYWAY_UI_FORMAT.format(lat=lat,
                                     lon=lon,
                                     start_date=start_date.strftime(DATE_URL_FORMAT),
                                     end_date=end_date.strftime(DATE_URL_FORMAT),
                                     acc_type=acc_type,
                                     zoom=zoom)
    markers_res = requests.get(markers_url)
    try:
        markers = markers_res.json()['markers']

    except Exception as e:
        print 'failed to parse:', markers_res.text
        raise e
    markers = [x for x in markers if x['locationAccuracy'] not in (2, 9)]
    markers_data = calc_markers(markers)

    accidents_details = dict()
    accidents_details['CITY'] = city
    accidents_details['NAME'] = name
    accidents_details['GRADE'] = markers_data['grade']
    accidents_details['DEADLY'] = markers_data['deadly']
    accidents_details['HARD'] = markers_data['hard']
    accidents_details['LIGHT'] = markers_data['light']
    accidents_details['UI_URL'] = ui_url
    accidents_details['MARKERS_URL'] = markers_url
    return accidents_details


def main(input_csv_filename, start_date, end_date, distance, pedestrian_only, output_filename):
    headers = ['INDEX BY GRADE', 'CITY', 'NAME', 'GRADE', 'DEADLY', 'HARD', 'LIGHT', 'UI_URL', 'MARKERS_URL']
    accidents_list = []
    with io.open(input_csv_filename, 'r', encoding='utf-8') as csvfile:
        i = 0
        for row in csvfile:
            (city, name, lat, lon) = parse_csv_line(row.strip())
            print u'{0} working on {1}'.format(i, name)
            i += 1
            if lat is None or lon is None:
                continue
            accidents_list.append(get_accidents_around(city, name, lat, lon, start_date, end_date, distance, pedestrian_only))
    accidents_list = sorted(accidents_list, key=lambda x: x['GRADE'], reverse=True)
    for idx in range(1,len(accidents_list) + 1):
        accidents_list[idx - 1]['INDEX BY GRADE'] = idx
    with io.open(output_filename, 'w', encoding='utf-16') as out_file:
        out_file.write(unicode('\t'.join(headers) + '\n'))
        for accidents_details in accidents_list:
            out_file.write(u'{index}\t{city}\t{name}\t{grade}\t{deadly}\t{hard}\t{light}\t{ui_url}\t{markers_url}\n'.format(
                index=accidents_details['INDEX BY GRADE'],
                city=accidents_details['CITY'],
                name=accidents_details['NAME'],
                grade=accidents_details['GRADE'],
                deadly=accidents_details['DEADLY'],
                hard=accidents_details['HARD'],
                light=accidents_details['LIGHT'],
                ui_url=accidents_details['UI_URL'],
                markers_url=accidents_details['MARKERS_URL']))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_csv_filename', default='schools.csv', type=str, help='input csv file path')
    parser.add_argument('--start_date', default='01-01-2012', type=valid_date, help='The Start Date - format DD-MM-YYYY')
    parser.add_argument('--end_date', default='01-01-2025', type=valid_date, help='The End Date - format DD-MM-YYYY')
    parser.add_argument('--distance', default=0.5, help='float In KM. Default is 0.5 (500m)', type=float)
    parser.add_argument('--pedestrians_only', action='store_true', default=False,
                        help='use the flag for pedestrian only results')
    parser.add_argument('--output_file', default='output.csv', help='output file of the results. Default is output.csv')
    args = parser.parse_args()
    main(args.input_csv_filename, args.start_date, args.end_date, args.distance, args.pedestrians_only, args.output_file)
