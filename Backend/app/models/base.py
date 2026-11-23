from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeDecorator, String
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement


class Base(DeclarativeBase):
    pass


class SpatialPoint(TypeDecorator):
    """
    PostgreSQL/PostGIS Geometry(POINT, 4326) with GIST spatial index support.
    Gracefully falls back to String(128) for SQLite in-memory test suites.
    """
    impl = Geometry
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect is None or dialect.name == "postgresql":
            geom = Geometry(geometry_type="POINT", srid=4326, spatial_index=True)
            return dialect.type_descriptor(geom) if dialect else geom
        return dialect.type_descriptor(String(128))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect is not None and dialect.name != "postgresql":
            if isinstance(value, WKTElement):
                return str(value.data)
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        return value
