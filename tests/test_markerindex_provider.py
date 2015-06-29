import config

# This is hack, no need to change the config file.
# Make this change before importing 'database' and initializing
# the engine with the real DATABASE_URI
db_name = "local-testing.db"
config.SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_name

import unittest

from markerindex_provider import create_provider

from sqlalchemy.schema import Table
import database
from sqlalchemy.engine.reflection import Inspector


class TestFactory(unittest.TestCase):
    def test_create_provider_bad_type(self):
        with self.assertRaises(TypeError):
            create_provider("BadTypeSQL")

    def test_create_two_diffrent_providers(self):
        import markerindex_provider
        sql_provider = create_provider("SQLite")
        postgres_provider = create_provider("PostgreSQL")
        self.assertEqual(sql_provider.get_table_name(), markerindex_provider.SQLITE_MARKER_INDEX_TABLE_NAME)
        self.assertEqual(postgres_provider.get_table_name(), markerindex_provider.POSTGRESQL_MARKER_INDEX_TABLE_NAME)


class TestSQLiteProvider(unittest.TestCase):
    provider = Base = db_session = engine = ""

    def _create_default_dict_marker(self, id=1):
        marker = {
            "id": id,
            "latitude": 2.0,
            "longitude": 3.0
        }
        return marker

    def _count_all_indexes(self):
        table = Table(self.provider.get_table_name(), self.Base.metadata,
                      autoload=True, autoload_with=self.engine)
        result = self.db_session.query(table.c.id).count()
        return result

    @classmethod
    def setUpClass(cls):
        db_name = "local-testing.db"
        config.SQLALCHEMY_DATABASE_URI = "sqlite:///" + db_name
        import imp
        imp.reload(database)
        import markerindex_provider
        imp.reload(markerindex_provider)
        from database import engine, db_session, Base
        cls.engine = engine
        cls.db_session = db_session
        cls.Base = Base

    def setUp(self):
        self.provider = create_provider("SQLite")

    def tearDown(self):
        self.Base.metadata.drop_all(self.engine)
        # option to delete the db testing file
        # if os.path.isfile(db_name):
        #     os.remove(os.path.join(db_name))

    def test_table_creation(self):
        self.provider.create_table()
        inspector = Inspector.from_engine(self.engine)
        self.assertTrue(
            self.provider.get_table_name() in inspector.get_table_names())

    def test_table_creation_empty_table(self):
        self.provider.create_table()
        rows = self._count_all_indexes()
        self.assertEqual(rows, 0)

    def test_create_index(self):
        marker = self._create_default_dict_marker()
        result = self.provider.create_index(marker)
        self.assertEqual(result["id"], 1)
        self.assertEqual(result["minLat"], 2.0)
        self.assertEqual(result["maxLat"], 2.0)
        self.assertEqual(result["minLng"], 3.0)
        self.assertEqual(result["maxLng"], 3.0)

    def test_create_bad_index(self):
        no_id_marker = {
            "latitude": 2.0,
            "longitude": 3.0
        }
        with self.assertRaises(AttributeError):
            self.provider.create_index(no_id_marker)

    def test_create_none_index(self):
        with self.assertRaises(AttributeError):
            self.provider.create_index(None)

    def test_create_table_when_exists(self):
        self.provider.create_table()
        self.provider.create_table()
        inspector = Inspector.from_engine(self.engine)
        self.assertTrue(
            self.provider.get_table_name() in inspector.get_table_names())

    def test_insert_single_index(self):
        self.provider.create_table()
        marker = self._create_default_dict_marker()
        index = self.provider.create_index(marker)
        self.provider.insert_indexes(index)
        rows = self._count_all_indexes()
        self.assertEqual(rows, 1)

    def test_insert_indexes(self):
        self.provider.create_table()
        markers = [
            self._create_default_dict_marker(1),
            self._create_default_dict_marker(2),
            self._create_default_dict_marker(3)
        ]

        indexes = []
        for marker in markers:
            indexes.append(self.provider.create_index(marker))

        self.provider.insert_indexes(indexes)
        rows = self._count_all_indexes()
        self.assertEqual(rows, 3)

    def test_create_table_when_exists_not_overwriting_data(self):
        self.test_insert_indexes()
        self.provider.create_table()
        rows = self._count_all_indexes()
        self.assertEqual(rows, 3)


class TestPostgreSQLProvider(unittest.TestCase):
    provider = Base = db_session = engine = ""

    def _create_default_dict_marker(self, id=1):
        marker = {
            "id": id,
            "latitude": 2.0,
            "longitude": 3.0
        }
        return marker

    def _count_all_indexes(self):
        table = Table(self.provider.get_table_name(), self.Base.metadata,
                      autoload=True, autoload_with=self.engine)
        result = self.db_session.query(table.c.id).count()
        # Close session to unblock DROP command (tearDown)
        self.db_session.close()
        return result

    @classmethod
    def setUpClass(cls):
        config.SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost/test_db"
        import imp
        imp.reload(database)
        import markerindex_provider
        imp.reload(markerindex_provider)
        from database import engine, db_session, Base
        cls.engine = engine
        cls.db_session = db_session
        cls.Base = Base

    def setUp(self):
        self.provider = create_provider("PostgreSQL")

    def tearDown(self):
        self.Base.metadata.drop_all(self.engine)

    def test_table_creation(self):
        self.provider.create_table()
        inspector = Inspector.from_engine(self.engine)
        self.assertTrue(
            self.provider.get_table_name() in inspector.get_table_names())

    def test_table_creation_empty_table(self):
        self.provider.create_table()
        rows = self._count_all_indexes()
        self.assertEqual(rows, 0)

    def test_create_index_from_dictionary(self):
        marker = self._create_default_dict_marker()
        result = self.provider.create_index(marker)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.geom, 'SRID=4326; POINT(2.0 3.0)')

    def test_create_index_from_marker_class(self):
        from models import Marker
        data = {
            "title": None,
            "description": None,
            "latitude": 2.0,
            "longitude": 3.0
        }
        marker = Marker.parse(data)
        marker.id = 1

        result = self.provider.create_index(marker)
        self.assertEqual(result.id, 1)
        self.assertEqual(result.geom, 'SRID=4326; POINT(2.0 3.0)')

    def test_create_bad_index(self):
        no_id_marker = self._create_default_dict_marker()
        del no_id_marker["id"]
        with self.assertRaises(AttributeError):
            self.provider.create_index(no_id_marker)

    def test_create_none_index(self):
        with self.assertRaises(AttributeError):
            self.provider.create_index(None)

    def test_create_table_when_exists(self):
        self.provider.create_table()
        self.provider.create_table()
        inspector = Inspector.from_engine(self.engine)
        self.assertTrue(
            self.provider.get_table_name() in inspector.get_table_names())

    def test_insert_single_index(self):
        self.provider.create_table()
        marker = self._create_default_dict_marker()
        index = self.provider.create_index(marker)
        self.provider.insert_indexes(index)
        rows = self._count_all_indexes()
        self.assertEqual(rows, 1)

    def test_insert_indexes(self):
        self.provider.create_table()
        markers = [
            self._create_default_dict_marker(1),
            self._create_default_dict_marker(2),
            self._create_default_dict_marker(3)
        ]

        indexes = []
        for marker in markers:
            indexes.append(self.provider.create_index(marker))

        self.provider.insert_indexes(indexes)
        rows = self._count_all_indexes()
        self.assertEqual(rows, 3)

    def test_create_table_when_exists_not_overwriting_data(self):
        self.test_insert_indexes()
        self.provider.create_table()
        rows = self._count_all_indexes()
        self.assertEqual(rows, 3)


if __name__ == '__main__':
    unittest.main()
