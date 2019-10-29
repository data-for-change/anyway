from anyway.app import db


def get_description(ind):
    description = db.session.execute('SELECT description FROM news_flash WHERE id=:id', {'id': ind}).fetchone()
    return description


def insert_new_flash_news(id_flash, title, link, date_parsed, author, description, location, lat, lon, road1,
                          road2, intersection, city, street, street2, resolution, geo_extracted_street,
                          geo_extracted_road_no, geo_extracted_intersection, geo_extracted_city,
                          geo_extracted_address, geo_extracted_district, accident, source):
    db.session.execute('INSERT INTO news_flash (id,title, link, date, author, description, location, lat, lon, '
                       'road1, road2, intersection, city, street, accident, source) VALUES \
                       (:id, :title, :link, :date, :author, :description, :location, :lat, :lon, \
                       :road1, :road2, :intersection, :city, :street, :street2, :resolution, :geo_extracted_street,\
                       :geo_extracted_road_no, :geo_extracted_intersection, :geo_extracted_city, \
                       :geo_extracted_address, :geo_extracted_district, :accident, :source)',
                       {'id': id_flash, 'title': title, 'link': link, 'date': date_parsed, 'author': author,
                        'description': description, 'location': location, 'lat': lat, 'lon': lon,
                        'road1': int(road1) if road1 else road1,
                        'road2': int(road2) if road2 else road2, 'intersection': intersection, 'city': city,
                        'street': street, 'street2': street2,
                        'resolution': resolution, 'geo_extracted_street': geo_extracted_street,
                        'geo_extracted_road_no': geo_extracted_road_no,
                        'geo_extracted_intersection': geo_extracted_intersection,
                        'geo_extracted_city': geo_extracted_city,
                        'geo_extracted_address': geo_extracted_address,
                        'geo_extracted_district': geo_extracted_district,
                        'accident': accident, 'source': source})
    db.session.commit()


def update_location_by_id(ind, accident, location, lat, lon):
    db.session.execute(
        'UPDATE news_flash SET accident = :accident, location = :location, lat = :lat, lon = :lon WHERE id=:id',
        {'accident': accident, 'location': location, 'lat': lat, 'lon': lon, 'id': ind})
    db.session.commit()


def get_title(ind):
    title = db.session.execute('SELECT title FROM news_flash WHERE id=:id', {'id': ind}).fetchone()
    return title


def get_latest_date_from_db():
    latest_date = db.session.execute('SELECT date FROM news_flash ORDER BY id DESC LIMIT 1').fetchone()
    if latest_date is None:
        return None
    return latest_date[0].replace(tzinfo=None)


def get_latest_id_from_db():
    id_flash = db.session.execute('SELECT id FROM news_flash ORDER BY id DESC LIMIT 1').fetchone()
    if id_flash is None:
        return -1
    return id_flash[0]
