import googlemaps


def geocode_extract(location, maps_key):
    gmaps = googlemaps.Client(key=maps_key)
    geocode_result = gmaps.geocode(location, language="iw", region="il")
    lat = geocode_result[0]["geometry"]["location"]["lat"]
    lng = geocode_result[0]["geometry"]["location"]["lng"]
    if 29.479700 <= lat <= 33.332805 and 34.267387 <= lng <= 35.896244:
        return geocode_result[0]["geometry"]["location"]
    else:
        return {"lat": -1, "lng": -1}
