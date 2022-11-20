import factory

from . import models
from anyway.app_and_db import db

class DefaultFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'flush'


class AccidentMarkerFactory(DefaultFactory):
    class Meta:
        model = models.AccidentMarker

    id = factory.Sequence(lambda n: n)
    provider_code = 1
    accident_year = 2020


class RoadSegmentFactory(DefaultFactory):
    class Meta:
        model = models.RoadSegments


class SuburbanAccidentMarkerFactory(AccidentMarkerFactory):
    road1 = factory.Sequence(lambda n: n)


class UrbanAccidentMarkerFactory(AccidentMarkerFactory):
    yishuv_symbol=1


class InvolvedFactory(DefaultFactory):
    class Meta:
        model = models.Involved

    id = factory.Sequence(lambda n: n)


