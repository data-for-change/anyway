import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from models import AccidentMarkerView as AccidentMarkerViewModel


class AccidentMarkerHebrew(SQLAlchemyObjectType):
    class Meta:
        model = AccidentMarkerViewModel
        interfaces = (relay.Node, )


class AccidentMarkerHebrewConnection(relay.Connection):
    class Meta:
        node = AccidentMarkerHebrew


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    # Allows sorting over multiple columns, by default over the primary key
    accident_markers_hebrew = graphene.List(AccidentMarkerHebrew)

    def resolve_accident_markers_hebrew(self, info):
        query = AccidentMarkerHebrew.get_query(info)  # SQLAlchemy query
        return query.all()


schema = graphene.Schema(query=Query)
