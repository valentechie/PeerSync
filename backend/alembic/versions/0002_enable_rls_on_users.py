"""enable row level security on users

Supabase publica el esquema `public` en su API REST. Con RLS activo y sin
políticas, esa API no puede leer ni escribir `users`. El backend no se ve
afectado: conecta como propietario de la tabla, al que RLS no se aplica.

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
