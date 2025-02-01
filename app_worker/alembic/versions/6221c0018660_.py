"""empty message.

Revision ID: 6221c0018660
Revises: 2689b03525f8
Create Date: 2022-02-20 03:00:01.366172

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '6221c0018660'
down_revision = '2689b03525f8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'yt_dlp',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('current_version', sa.String(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('yt_dlp')
    # ### end Alembic commands ###
