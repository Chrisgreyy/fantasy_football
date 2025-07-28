"""update weekly points constraint

Revision ID: update_weekly_points_constraint
Revises: verify_league_columns
Create Date: 2025-07-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'update_weekly_points_constraint'
down_revision: Union[str, None] = 'verify_league_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # First ensure any NULL values are set to 0
    op.execute("UPDATE teams SET weekly_points = 0 WHERE weekly_points IS NULL")
    
    # Then alter the column to be not nullable with a default value
    op.alter_column('teams', 'weekly_points',
                   existing_type=sa.Integer(),
                   nullable=False,
                   server_default='0')


def downgrade() -> None:
    op.alter_column('teams', 'weekly_points',
                   existing_type=sa.Integer(),
                   nullable=True,
                   server_default=None)
