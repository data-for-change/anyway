from flask_sqlalchemy import SQLAlchemy

from anyway.utilities import init_flask

app = init_flask()
db = SQLAlchemy(app)


def get_description(ind):
    description = db.session.execute('SELECT description FROM news_flash WHERE id=:id', {'id': ind}).fetchone()
    return description


def insert_new_flash_news(id_flash, title, link, date_parsed, author, description, location, lat, lon, accident,
                          source):
    db.session.execute('INSERT INTO news_flash (id,title, link, date, author, description, location, lat, lon, '
                       'accident, source) VALUES \
                       (:id, :title, :link, :date, :author, :description, :location, :lat, :lon, :accident, :source)',
                       {'id': id_flash, 'title': title, 'link': link, 'date': date_parsed, 'author': author,
                        'description': description, 'location': location, 'lat': lat, 'lon': lon, 'accident': accident,
                        'source': source})
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
