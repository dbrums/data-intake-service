"""add idempotency_key column and unique constraint

Revision ID: b313808e82f4
Revises: b8aca45600cf
Create Date: 2026-04-26 01:03:08.667537

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b313808e82f4"
down_revision: Union[str, Sequence[str], None] = "b8aca45600cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add idempotency_key column if it doesn't exist
    # (Some databases may already have this column from model changes)
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col["name"] for col in inspector.get_columns("jobs")]

    if "idempotency_key" not in columns:
        op.add_column(
            "jobs", sa.Column("idempotency_key", sa.String(length=100), nullable=True)
        )

    # SQLite requires batch mode for adding constraints
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_jobs_idempotency_key", ["idempotency_key"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("jobs", schema=None) as batch_op:
        batch_op.drop_constraint("uq_jobs_idempotency_key", type_="unique")
    op.drop_column("jobs", "idempotency_key")
