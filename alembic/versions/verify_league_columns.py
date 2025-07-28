"""verify league columns

Revision ID: verify_league_columns
Revises: 6832055c452d
Create Date: 2025-07-28 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'verify_league_columns'
down_revision: Union[str, None] = '6832055c452d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def verify_column_exists(table, column):
    from sqlalchemy.engine.reflection import Inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    columns = [col['name'] for col in inspector.get_columns(table)]
    return column in columns

def upgrade() -> None:
    # Verify all required columns exist
    columns_to_check = [
        'budget',
        'max_players_per_team',
        'max_teams',
        'max_goalkeepers',
        'max_defenders',
        'max_midfielders',
        'max_forwards',
        'total_squad_size',
        'free_transfers_per_gameweek',
        'transfer_penalty_points',
        'max_transfers_per_gameweek',
        'points_per_goal_forward',
        'points_per_goal_midfielder',
        'points_per_goal_defender',
        'points_per_goal_goalkeeper',
        'points_per_assist',
        'points_per_clean_sheet',
        'points_per_yellow_card',
        'points_per_red_card',
        'points_per_own_goal',
        'points_per_penalty_save',
        'points_per_penalty_miss',
        'allow_wildcards',
        'allow_bench_boost',
        'allow_triple_captain'
    ]
    
    # Add any missing columns
    for column in columns_to_check:
        if not verify_column_exists('leagues', column):
            if column in ['allow_wildcards', 'allow_bench_boost', 'allow_triple_captain']:
                op.add_column('leagues', sa.Column(column, sa.Boolean(), nullable=True, server_default='true'))
            elif column == 'budget':
                op.add_column('leagues', sa.Column(column, sa.Float(), nullable=True, server_default='100.0'))
            else:
                # All other columns are integers with their default values
                default_values = {
                    'max_players_per_team': '3',
                    'max_teams': '20',
                    'max_goalkeepers': '2',
                    'max_defenders': '5',
                    'max_midfielders': '5',
                    'max_forwards': '3',
                    'total_squad_size': '15',
                    'free_transfers_per_gameweek': '1',
                    'transfer_penalty_points': '4',
                    'max_transfers_per_gameweek': '5',
                    'points_per_goal_forward': '4',
                    'points_per_goal_midfielder': '5',
                    'points_per_goal_defender': '6',
                    'points_per_goal_goalkeeper': '6',
                    'points_per_assist': '3',
                    'points_per_clean_sheet': '4',
                    'points_per_yellow_card': '-1',
                    'points_per_red_card': '-3',
                    'points_per_own_goal': '-2',
                    'points_per_penalty_save': '5',
                    'points_per_penalty_miss': '-2'
                }
                op.add_column('leagues', sa.Column(column, sa.Integer(), nullable=True, 
                                                 server_default=default_values.get(column, '0')))

def downgrade() -> None:
    # No downgrade needed for verification
    pass
