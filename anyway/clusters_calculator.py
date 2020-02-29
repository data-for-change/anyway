import logging
import multiprocessing
import time
from .models import AccidentMarker
from .pymapcluster import calculate_clusters
from .task_queue import task_queue

@task_queue.task
def retrieve_clusters(**kwargs):
    start_time = time.time()
    result = AccidentMarker.bounding_box_query(is_thin=True, **kwargs)
    accident_markers_in_box = result.accident_markers.all()
    rsa_markers_in_box = result.rsa_markers.all()
    logging.debug('getting cluster data from db took %f seconds' % (time.time() - start_time))
    start_time = time.time()
    clusters = calculate_clusters(accident_markers_in_box + rsa_markers_in_box, kwargs['zoom'])
    logging.debug('calculating clusters took %f seconds' % (time.time() - start_time))
    return clusters
