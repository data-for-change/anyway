##
from math import cos, sin, atan2, sqrt

from anyway import globalmaptiles as globaltiles


##


def latlng_to_zoompixels(mercator, lat, lng, zoom):
    mx, my = mercator.LatLonToMeters(lat, lng)
    pix = mercator.MetersToPixels(mx, my, zoom)
    return pix


def in_cluster(center, radius, point):
    return sqrt((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2) <= radius


def cluster_markers(mercator, latlngs, zoom, gridsize=50):
    """
    Args:
        mercator: instance of GlobalMercator()
        latlngs: list of (lat,lng) tuple
        zoom: current zoom level
        gridsize: cluster radius (in pixels in current zoom level)
    Returns:
        centers: list of indices in latlngs of points used as centers
        clusters: list of same length as latlngs giving assigning each point to
                  a cluster
    """
    centers = []
    clusters = []
    sizes = []
    latlngs = [{"latitude": latlng.latitude, "longitude": latlng.longitude} for latlng in latlngs]
    for i, latlng in enumerate(latlngs):
        lat = latlng["latitude"]
        lng = latlng["longitude"]
        point_pix = latlng_to_zoompixels(mercator, lat, lng, zoom)
        assigned = False
        for cidx, c in enumerate(centers):
            center = latlngs[c]
            center = latlng_to_zoompixels(mercator, center["latitude"], center["longitude"], zoom)
            if in_cluster(center, gridsize, point_pix):
                # Assign point to cluster
                clusters.append(cidx)
                sizes[cidx] += 1
                assigned = True
                break
        if not assigned:
            # Create new cluster for point
            centers.append(i)
            sizes.append(1)
            clusters.append(len(centers) - 1)

    return centers, clusters, sizes


def create_clusters_centers(markers, zoom, radius):
    mercator = globaltiles.GlobalMercator()
    centers, clusters, sizes = cluster_markers(mercator, markers, zoom, radius)
    centers_markers = [markers[i] for i in centers]
    return centers_markers, clusters, sizes


def get_cluster_json(clust_marker, clust_size):
    return {
        "longitude": clust_marker.longitude,
        "latitude": clust_marker.latitude,
        "size": clust_size,
    }


def calculate_clusters(markers, zoom, radius=50):
    centers, _, sizes = create_clusters_centers(markers, zoom, radius)
    json_clusts = []

    for i, point in enumerate(centers):
        json_clusts.append(get_cluster_json(point, sizes[i]))

    return json_clusts


##
if __name__ == "__main__":
    ##
    mercator = globaltiles.GlobalMercator()
    latlngs = [(28.43, 8), (28.43, 8), (28.44, 8), (35, 8)]
    centers, clusters, _ = cluster_markers(mercator, latlngs, 21)
    ##
