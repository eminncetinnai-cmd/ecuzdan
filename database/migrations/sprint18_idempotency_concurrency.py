"""Phase 3 idempotency and optimistic concurrency schema migration."""
import sqlalchemy as sa
from alembic import op


def upgrade():
    for table_name in ("transaction", "recurring_plan", "asset"):
        op.add_column(table_name, sa.Column("updated_at", sa.DateTime(), nullable=True))
        op.add_column(table_name, sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("transaction", sa.Column("idempotency_key", sa.String(length=64), nullable=True))
    op.create_index("uq_transaction_idempotency_key", "transaction", ["idempotency_key"], unique=True)

def downgrade():
    op.drop_index("uq_transaction_idempotency_key", table_name="transaction")
    op.drop_column("transaction", "idempotency_key")
    for table_name in ("asset", "recurring_plan", "transaction"):
        op.drop_column(table_name, "version")
        op.drop_column(table_name, "updated_at")
