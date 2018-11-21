import googlemaps


def geocode_extract(location, maps_key):
    gmaps = googlemaps.Client(key=maps_key)
    geocode_result = gmaps.geocode(location, language="iw", region="il")
    if geocode_result is None or geocode_result == []:
        return None
    country = ""
    for address in geocode_result[0]["address_components"]:
        if any("country" in s for s in address["types"]):
            country = address["short_name"]
            break
    if country == "IL":
        return geocode_result[0]["geometry"]["location"]
    else:
        return None
