from collections.abc import Iterator

from enum import Enum as PyEnum

from sqlalchemy import Enum, MetaData, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

SUPABASE_TRANSACTION_POOLER_PORT = 6543

# Nombres de constraints estables para que las migraciones de Alembic sean reproducibles.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def str_enum(enum_class: type[PyEnum], name: str) -> Enum:
    """VARCHAR + CHECK en vez de un ENUM nativo: añadir valores no exige una migración especial."""
    return Enum(
        enum_class,
        name=name,
        native_enum=False,
        create_constraint=True,
        length=20,
        values_callable=lambda members: [member.value for member in members],
    )


def engine_options(database_url: str) -> dict:
    """En serverless se conecta por el pooler de transacciones de Supabase, que ya
    reutiliza las conexiones y no admite prepared statements."""
    if make_url(database_url).port == SUPABASE_TRANSACTION_POOLER_PORT:
        return {"poolclass": NullPool, "connect_args": {"prepare_threshold": None}}
    return {"pool_pre_ping": True}


_database_url = get_settings().database_url
engine = create_engine(_database_url, **engine_options(_database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
