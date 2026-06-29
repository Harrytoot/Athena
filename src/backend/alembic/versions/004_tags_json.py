"""change watchlist_items.tags from ARRAY to JSON

Revision ID: 004
Revises: 003
Create Date: 2026-06-29

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("ALTER TABLE watchlist_items ALTER COLUMN tags DROP DEFAULT")
    op.execute("ALTER TABLE watchlist_items ALTER COLUMN tags TYPE JSON USING array_to_json(tags)")
    op.execute("ALTER TABLE watchlist_items ALTER COLUMN tags SET DEFAULT '[]'::json")
    op.execute("ALTER TABLE watchlist_items ALTER COLUMN tags SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE watchlist_items ALTER COLUMN tags DROP DEFAULT")
    op.execute("ALTER TABLE watchlist_items ALTER COLUMN tags TYPE character varying[] USING string_to_array(tags::text, ',')")
    op.alter_column(
        "watchlist_items",
        "tags",
        server_default=sa.text("'{}'::character varying[]"),
    )
