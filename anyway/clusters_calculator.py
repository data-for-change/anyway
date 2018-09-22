from .models import AccidentMarker
from .pymapcluster import calculate_clusters
from .task_queue import task_queue, map_task, task_signature
import time
import logging
import multiprocessing


@task_queue.task
def calculate_marker_box(marker_box, kwargs):
    kwargs.update(marker_box)
    markers_in_box = AccidentMarker.bounding_box_query(**kwargs).markers.all()
    return calculate_clusters(markers_in_box, kwargs['zoom'])


# def retrieve_clusters(**kwargs):
#     marker_boxes = divide_to_boxes(kwargs['ne_lat'], kwargs['ne_lng'], kwargs['sw_lat'], kwargs['sw_lng'])
#     return map_task(task_signature(calculate_marker_box, kwargs), marker_boxes)


def retrieve_clusters(**kwargs):
    start_time = time.time()
    markers_in_box = AccidentMarker.bounding_box_query(**kwargs).markers.all()
    logging.debug('getting cluster data from db took %f seconds' % (time.time() - start_time))
    start_time = time.time()
    clusters = calculate_clusters(markers_in_box, kwargs['zoom'])
    logging.debug('calculating clusters took %f seconds' % (time.time() - start_time))
    return clusters


def divide_to_boxes(ne_lat, ne_lng, sw_lat, sw_lng):
    cpu_count = multiprocessing.cpu_count()
    lat_box_size = (ne_lat - sw_lat) / cpu_count
    # lng_box_size = (sw_lng - ne_lng) / cpu_count
    boxes = []
    for i in range(cpu_count):
        # TODO: the below calculation is using sw_lat as first param instead of ne_lat. Plz verify my fix for that:
        # boxes.append((sw_lat + (i + 1) * lat_box_size, ne_lng, sw_lat + i * lat_box_size, sw_lng))
        boxes.append({'ne_lat': ne_lat + (i + 1) * lat_box_size, 'ne_lng': ne_lng,
                      'sw_lat': sw_lat + i * lat_box_size, 'sw_lng': sw_lng})

    return boxes
