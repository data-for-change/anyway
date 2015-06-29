import config

# This is hack, no need to change the config file.
# Make this change before importing 'database' and initializing the engine with the real DATABASE_URI
db_name = "local-testing.db"
config.SQLALCHEMY_DATABASE_URI  = "sqlite:///" + db_name

import unittest
import os

from sqlalchemy import Column, Integer, MetaData
from sqlalchemy.schema import Table

from database import Base, insert_table, engine
from models import Marker


table_name = 'test'

class Test(Base):
    __tablename__ = table_name
    id = Column('id', Integer, primary_key = True)
    number = Column('number', Integer)

class TeseDBInsert(unittest.TestCase):

    def setUp(self):
        Base.metadata.create_all(engine)

    def tearDown(self):
        Base.metadata.drop_all(engine)
        # option to delete the db testing file
        # if os.path.isfile(db_name):
        #     os.remove(os.path.join(db_name))

    good_data = {
        "number": 100
    }

    bad_data = {
        "number": "hello world"
    }

    def test_bad_table_name(self):
        self.assertEqual(insert_table("bad table name", self.good_data), False)

    def test_null_insertion(self):
        self.assertEqual(insert_table(table_name, None), False)

    def test_bad_obj_insertion(self):
        self.assertEqual(insert_table(table_name, 123), False)     

    # This isn't the way to insert a model to the table (only dict will pass).
    def test_bad_model_object_insertion(self):
        self.assertEqual(insert_table(table_name, Test(number=300)), False)

    # Yes, SQLAlchemy allow to insert wrong types, so insert 'hello world' string to Integer column will return True
    def test_worng_type_insert(self):
        self.assertEqual(insert_table(table_name, self.bad_data), True)   

    def test_good_single_raw_object_insertion(self):
        self.assertEqual(insert_table(table_name, self.good_data), True)

    def test_good_raw_array_insertion(self):
        arr = []
        for x in xrange(1,10):
            arr.append(self.good_data)
        self.assertEqual(insert_table(table_name, arr), True)

if __name__ == '__main__':
     unittest.main()