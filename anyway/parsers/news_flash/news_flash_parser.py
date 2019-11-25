from anyway.utilities import init_flask
from flask_sqlalchemy import SQLAlchemy

app = init_flask()
db = SQLAlchemy(app)


def get_description(ind):
    """
    get description by news_flash id
    :param ind: news_flash id
    :return: description of news_flash
    """
    description = db.session.execute('SELECT description FROM news_flash WHERE id=:id', {'id': ind}).fetchone()
    return description


def insert_new_flash_news(id_flash, title, link, date_parsed, author, description, location, lat, lon, road1,
                          road2, intersection, city, street, street2, resolution, geo_extracted_street,
                          geo_extracted_road_no, geo_extracted_intersection, geo_extracted_city,
                          geo_extracted_address, geo_extracted_district, accident, source):
    """
    insert new news_flash to db
    :param id_flash: id of the news_flash, which should be the last one + 1
    :param title: title of the news_flash
    :param link: link to the news_flash
    :param date_parsed: parsed date of the news_flash
    :param author: author of the news_flash
    :param description: description of the news flash
    :param location: location of the news flash (textual)
    :param lat: latitude
    :param lon: longitude
    :param road1: road 1 if found
    :param road2: road 2 if found
    :param intersection: intersection if found
    :param city: city if found
    :param street: street if found
    :param street2: street 2 if found
    :param resolution: resolution of found location
    :param geo_extracted_street: street from data extracted from the geopoint
    :param geo_extracted_road_no: road number from data extracted from the geopoint
    :param geo_extracted_intersection: intersection from data extracted from the geopoint
    :param geo_extracted_city: city from data extracted from the geopoint
    :param geo_extracted_address: address from data extracted from the geopoint
    :param geo_extracted_district: district from data extracted from the geopoint
    :param accident: is the news flash an accident
    :param source: source of the news flash
    """
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
    """
    update news flash with new parameters
    :param ind: id of news flash to update
    :param accident: update accident status
    :param location: update of textual location
    :param lat: new found latitude
    :param lon: new found longitude
    :return:
    """
    db.session.execute(
        'UPDATE news_flash SET accident = :accident, location = :location, lat = :lat, lon = :lon WHERE id=:id',
        {'accident': accident, 'location': location, 'lat': lat, 'lon': lon, 'id': ind})
    db.session.commit()


def get_title(ind):
    """
    title of news flash by id
    :param ind: id
    :return: title of corresponding news flash
    """
    title = db.session.execute('SELECT title FROM news_flash WHERE id=:id', {'id': ind}).fetchone()
    return title


def get_latest_date_from_db():
    """
    returns latest date of news flash
    :return: latest date of news flash
    """
    latest_date = db.session.execute('SELECT date FROM news_flash ORDER BY id DESC LIMIT 1').fetchone()
    if latest_date is None:
        return None
    return latest_date[0].replace(tzinfo=None)


def get_latest_id_from_db():
    """
    returns latest news flash id
    :return: latest news flash id
    """
    id_flash = db.session.execute('SELECT id FROM news_flash ORDER BY id DESC LIMIT 1').fetchone()
    if id_flash is None:
        return -1
    return id_flash[0]
