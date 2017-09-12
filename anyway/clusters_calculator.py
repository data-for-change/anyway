from .models import Marker
from .pymapcluster import calculate_clusters
import logging
import concurrent.futures
import multiprocessing


def retrieve_clusters(**kwargs):
    marker_boxes = divide_to_boxes(kwargs['ne_lat'], kwargs['ne_lng'], kwargs['sw_lat'], kwargs['sw_lng'])
    result_futures = []
    logging.info('number of cores: ' + str(multiprocessing.cpu_count()))
    with concurrent.futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for marker_box in marker_boxes:

            kwargs.update(marker_box)
            markers_in_box = Marker.bounding_box_query(**kwargs).markers.all()
            result_futures.append(executor.submit(calculate_clusters, markers_in_box, kwargs['zoom']))

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
        # TODO: the below calculation is using sw_lat as first param instead of ne_lat. Plz verify my fix for that:
        # boxes.append((sw_lat + (i + 1) * lat_box_size, ne_lng, sw_lat + i * lat_box_size, sw_lng))
        boxes.append({'ne_lat': ne_lat + (i + 1) * lat_box_size, 'ne_lng': ne_lng,
                      'sw_lat': sw_lat + i * lat_box_size, 'sw_lng': sw_lng})

    return boxes
