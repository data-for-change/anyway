import googlemaps


def geocode_extract(location, maps_key):
    """
    this method takes a string representing location and a google maps key and returns a dict of the corresponding
    location found on google maps (by that string), describing details of the location found and the geometry
    :param location: string representing location
    :param maps_key: google maps API key
    :return: a dict containing data about the found location on google maps, with the keys: street,
    road_no [road number], intersection, city, address, district and the geometry of the location.
    """
    gmaps = googlemaps.Client(key=maps_key)
    geocode_result = gmaps.geocode(location, region='il', language='iw')
    if geocode_result is None or geocode_result == []:
        return None
    response = geocode_result[0]
    geom = response['geometry']['location']
    street = ''
    road_no = ''
    intersection = ''
    city = ''
    district = ''
    for item in response['address_components']:
        if 'route' in item['types']:
            if item['short_name'].isdigit():
                road_no = item['short_name']
            else:
                street = item['long_name']
        elif 'point_of_interest' in item['types'] or 'intersection' in item['types']:
            intersection = item['long_name']
        elif 'locality' in item['types']:
            city = item['long_name']
        elif 'administrative_area_level_1' in item['types']:
            district = item['long_name']
    address = response['formatted_address']
    return {'street': street, 'road_no': road_no, 'intersection': intersection,
            'city': city, 'address': address,
            'district': district, 'geom': geom}
