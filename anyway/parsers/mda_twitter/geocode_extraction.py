import googlemaps


def geocode_extract(location, maps_key):
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
