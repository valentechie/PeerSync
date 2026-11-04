from sqlalchemy.pool import NullPool

from app.core.database import engine_options


def test_transaction_pooler_disables_local_pool_and_prepared_statements():
    options = engine_options("postgresql+psycopg://u:p@aws.pooler.supabase.com:6543/postgres")

    assert options["poolclass"] is NullPool
    assert options["connect_args"]["prepare_threshold"] is None


def test_session_connection_keeps_local_pool():
    options = engine_options("postgresql+psycopg://u:p@aws.pooler.supabase.com:5432/postgres")

    assert options == {"pool_pre_ping": True}
