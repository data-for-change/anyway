import math


def batch_iterator(iterable, batch_size):
    iterator = iter(iterable)
    iteration_stopped = False

    while True:
        batch = []
        for _ in range(batch_size):
            try:
                batch.append(next(iterator))
            except StopIteration:
                iteration_stopped = True
                break

        yield batch
        if iteration_stopped:
            break


def get_bounding_box_polygon(latitude, longitude, distance_in_km):
    latitude = math.radians(latitude)
    longitude = math.radians(longitude)

    radius = 6371
    # Radius of the parallel at given latitude
    parallel_radius = radius * math.cos(latitude)

    lat_min = latitude - distance_in_km / radius
    lat_max = latitude + distance_in_km / radius
    lon_min = longitude - distance_in_km / parallel_radius
    lon_max = longitude + distance_in_km / parallel_radius

    rad2deg = math.degrees
    baseX = rad2deg(lon_min)
    baseY = rad2deg(lat_min)
    distanceX = rad2deg(lon_max)
    distanceY = rad2deg(lat_max)

    return f"POLYGON(({baseX} {baseY},{baseX} {distanceY},{distanceX} {distanceY},{distanceX} {baseY},{baseX} {baseY}))"
