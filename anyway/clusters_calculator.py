import logging
import multiprocessing
import time

from .models import AccidentMarker
from .pymapcluster import calculate_clusters
from .task_queue import task_queue


@task_queue.task
def calculate_marker_box(marker_box, kwargs):
    kwargs.update(marker_box)
    markers_in_box = AccidentMarker.bounding_box_query(**kwargs)
    markers = markers_in_box['accidnet_markers'].all()
    markers += markers_in_box['rsa_markers'].all()
    return calculate_clusters(markers, kwargs['zoom'])


def retrieve_clusters(**kwargs):
    start_time = time.time()
    result = AccidentMarker.bounding_box_query(**kwargs)
    accident_markers_in_box = result.accident_markers.with_entities(AccidentMarker.latitude,
                                                                    AccidentMarker.longitude).all()
    rsa_markers_in_box = result.rsa_markers.with_entities(AccidentMarker.latitude, AccidentMarker.longitude).all()
    logging.debug('getting cluster data from db took %f seconds' % (time.time() - start_time))
    start_time = time.time()
    clusters = calculate_clusters(accident_markers_in_box + rsa_markers_in_box, kwargs['zoom'])
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
