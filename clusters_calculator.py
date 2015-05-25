from models import Marker
from static.pymapcluster import generate_clusters_json
import time

def retrieve_clusters(ne_lat, ne_lng, sw_lat, sw_lng, start_date, end_date, fatal, severe, light, inaccurate, zoom):
    start_time = time.time()
    filtered_markers = Marker.bounding_box_query(ne_lat, ne_lng, sw_lat, sw_lng, start_date, end_date, fatal,
                                                 severe, light, inaccurate).all()
    print('bounding_box_query took ' + str(time.time() - start_time))
    return generate_clusters_json(filtered_markers, zoom)
