from database import engine

from utilities import File
import config
from database import Base, insert_table, delete_table
from sqlalchemy.schema import Table

from sqlalchemy import Column, Integer
from geoalchemy2 import types
from database import db_session
from sqlalchemy.orm import load_only

# Different names required because when declaring MarkerIndex(Base) class
# Engine cause override the table reflection when using SQLite
SQLITE_MARKER_INDEX_TABLE_NAME = 'marker_index'
POSTGRESQL_MARKER_INDEX_TABLE_NAME = 'marker_index_gis'


# Extract marker index data from a marker, as Marker object or a dictionary
def _get_id_lat_lng(marker):
    import collections
    from models import Marker

    try:
        if type(marker) is dict:
            id = marker["id"]
            lat = marker["latitude"]
            lng = marker["longitude"]
        elif type(marker) is Marker:
            id = marker.id
            lat = marker.latitude
            lng = marker.longitude
        else:
            raise AttributeError("Bad marker type: {0}, for marker: {1}.".format(type(marker), str(marker)))
    except:
        raise AttributeError("Getting marker data faild for marker: {0}".format(str(marker)))

    if id is None:
        raise AttributeError("Could not get id for marker: {0}".format(str(marker)))

    result = collections.namedtuple('SimpleMarker', ['id', 'lat', 'lng'])
    return result(id, lat, lng)


class MarkerIndexProvider(object):

    @staticmethod
    def factory(type):
        class SQLiteMarkerIndexProvider(MarkerIndexProvider):
            def create_table(self):
                sql = File.read(config.BUILD_MARKER_INDEX_SQL_FILE)
                engine.execute(sql)

            def delete_table(self):
                delete_table(self.get_table_name())

            def insert_indexes(self, indexes):
                insert_table(self.get_table_name(), indexes)

            def create_index(self, marker):
                simple_marker = _get_id_lat_lng(marker)

                # getting the marker data as: marker.id or marker["id"],
                # for Marker object and raw object respectively
                return {
                    "id": simple_marker.id,
                    "minLng": simple_marker.lng,
                    "maxLng": simple_marker.lng,
                    "minLat": simple_marker.lat,
                    "maxLat": simple_marker.lat
                }

            def get_bounding_indexes(self, ne_lat, ne_lng, sw_lat, sw_lng):
                # Get the ids of the bounding markers from the R*Tree index first
                indexes_table = Table(self.get_table_name(), Base.metadata, autoload=True, autoload_with=engine)

                result = db_session.query(indexes_table).with_entities(indexes_table.c.id) \
                    .filter(indexes_table.c.minLng <= ne_lng) \
                    .filter(indexes_table.c.maxLng >= sw_lng) \
                    .filter(indexes_table.c.minLat <= ne_lat) \
                    .filter(indexes_table.c.maxLat >= sw_lat)
                return result

            def get_table_name(self):
                return SQLITE_MARKER_INDEX_TABLE_NAME

        class PostgreMarkerIndexProvider(MarkerIndexProvider):
            def _is_iterable(self, obj):
                return hasattr(obj, '__iter__')

            def create_table(self):
                # Creates the table only if not exists
                MarkerIndex.__table__.create(engine, checkfirst=True)

            def delete_table(self):
                db_session.query(MarkerIndex).delete()

            def drop_table(self):
                MarkerIndex.__table__.drop(engine)

            def insert_indexes(self, indexes):
                if self._is_iterable(indexes):
                    db_session.add_all(indexes)
                else:
                    db_session.add(indexes)

                db_session.commit()

            def create_index(self, marker):
                simple_marker = _get_id_lat_lng(marker)
                return MarkerIndex(id=simple_marker.id,
                                   geom='SRID=4326; POINT({0} {1})'.format(simple_marker.lat, simple_marker.lng))

            def get_bounding_indexes(self, ne_lat, ne_lng, sw_lat, sw_lng):
                result = db_session.query(MarkerIndex).filter(
                    MarkerIndex.geom.intersects('POLYGON(({0} {1}, {2} {3}, {4} {5}, {6} {7}, {8} {9}))'
                        .format(ne_lat, ne_lng, ne_lat, sw_lng, sw_lat, sw_lng, sw_lat, ne_lng, ne_lat, ne_lng))) \
                .options(load_only("id"))
                return result

            def get_table_name(self):
                return POSTGRESQL_MARKER_INDEX_TABLE_NAME

        if type == "SQLite": return SQLiteMarkerIndexProvider()
        if type == "PostgreSQL":
            class MarkerIndex(Base):
                __tablename__ = POSTGRESQL_MARKER_INDEX_TABLE_NAME
                __table_args__ = {'extend_existing': True}
                id = Column(Integer, primary_key=True)
                geom = Column(types.Geometry(geometry_type='POINT', srid=4326))
            return PostgreMarkerIndexProvider()
        raise TypeError('Bad MarkerIndexProvider creation: ' + type)


def create_provider(override_config_type=None):
    return MarkerIndexProvider.factory(override_config_type or config.MARKER_INDEX_PROVIDER_TYPE)
