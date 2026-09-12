"""Add messages.email_status for persisted agent-reply delivery status.

Revision ID: b7c4e2a91f03
Revises: f8392d31e608
Create Date: 2026-09-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c4e2a91f03'
down_revision: Union[str, Sequence[str], None] = 'f8392d31e608'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'messages',
        sa.Column(
            'email_status',
            sa.String(length=32),
            nullable=False,
            server_default='skipped_no_config',
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('messages', 'email_status')
