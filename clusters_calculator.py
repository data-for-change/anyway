import itertools
from celery import Celery, group
from models import Marker
from static.pymapcluster import calculate_clusters
import multiprocessing


celery_app = Celery('tasks', backend='rpc://', broker='pyamqp://guest@localhost//')

@celery_app.task
def calculate_marker_box(kwargs, marker_box):
    kwargs.update(marker_box)
    markers_in_box = Marker.bounding_box_query(**kwargs).markers.all()
    return calculate_clusters(markers_in_box, kwargs['zoom'])


def retrieve_clusters(**kwargs):
    marker_boxes = divide_to_boxes(kwargs['ne_lat'], kwargs['ne_lng'], kwargs['sw_lat'], kwargs['sw_lng'])
    job = group([calculate_marker_box.s(kwargs, marker_box) for marker_box in marker_boxes])
    result = job.apply_async()
    result.join()
    return list(itertools.chain.from_iterable(result.get()))


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
