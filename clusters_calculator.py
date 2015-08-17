from models import Marker
from static.pymapcluster import calculate_clusters
import time
import logging
import concurrent.futures
import multiprocessing


def retrieve_clusters(ne_lat, ne_lng, sw_lat, sw_lng, start_date, end_date, fatal, severe, light, approx, accurate,
                      show_urban, show_intersection, show_lane, show_day, show_holiday, show_time, start_time, end_time,
                      weather, separation, road, surface, acctype, controlmeasure, district, zoom):
    marker_boxes = divide_to_boxes(ne_lat, ne_lng, sw_lat, sw_lng)
    result_futures = []
    logging.info('number of cores: ' + str(multiprocessing.cpu_count()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for marker_box in marker_boxes:
            markers_in_box = Marker.bounding_box_query(marker_box[0], marker_box[1], marker_box[2], marker_box[3],
                                                       start_date, end_date, fatal,
                                                       severe, light, approx, accurate, show_urban, show_intersection,
                                                       show_lane, show_day, show_holiday, show_time, start_time,
                                                       end_time, weather, separation, road, surface, acctype,
                                                       controlmeasure, district).all()
            result_futures.append(executor.submit(calculate_clusters, markers_in_box, zoom))

    completed_futures = concurrent.futures.wait(result_futures)
    result = []
    for future in completed_futures.done:
        result.extend(future.result())

    return result


def divide_to_boxes(ne_lat, ne_lng, sw_lat, sw_lng):
    cpu_count = multiprocessing.cpu_count()
    lat_box_size = (ne_lat - sw_lat) / cpu_count
    # lng_box_size = (sw_lng - ne_lng) / cpu_count
    boxes = []
    for i in xrange(cpu_count):
        boxes.append((sw_lat + (i + 1) * lat_box_size, ne_lng, sw_lat + i * lat_box_size, sw_lng))

    return boxes