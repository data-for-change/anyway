import json

from flask import Response

from anyway.clusters_calculator import retrieve_clusters
from anyway.helpers import get_kwargs


def clusters():
    # start_time = time.time()
    kwargs = get_kwargs()
    results = retrieve_clusters(**kwargs)

    # logging.debug('calculating clusters took %f seconds' % (time.time() - start_time))
    return Response(json.dumps({'clusters': results}), mimetype="application/json")
