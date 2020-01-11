import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType

from anyway.models import AccidentMarkerView as AccidentMarkerViewModel


class AccidentMarkerHebrew(SQLAlchemyObjectType):
    class Meta:
        model = AccidentMarkerViewModel
        interfaces = (relay.Node,)


class AccidentMarkerHebrewConnection(relay.Connection):
    class Meta:
        node = AccidentMarkerHebrew


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    accident_markers_hebrew = graphene.List(AccidentMarkerHebrew)

    def resolve_accident_markers_hebrew(self, info):
        query = AccidentMarkerHebrew.get_query(info)
        return query.all()


schema = graphene.Schema(query=Query)
