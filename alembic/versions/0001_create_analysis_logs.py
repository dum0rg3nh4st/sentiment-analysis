"""create analysis_logs

Revision ID: 0001_create_analysis_logs
Revises: 
Create Date: 2026-05-05

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_create_analysis_logs"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "analysis_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column(
            "sentiment_label",
            sa.Enum("NEUTRAL", "POSITIVE", "NEGATIVE", name="sentiment_label_enum"),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_analysis_logs_id", "analysis_logs", ["id"])


def downgrade() -> None:
    op.drop_index("ix_analysis_logs_id", table_name="analysis_logs")
    op.drop_table("analysis_logs")
    op.execute("DROP TYPE IF EXISTS sentiment_label_enum")

