"""empty message

Revision ID: 1ebd745ae92c
Revises: 4f583717507b
Create Date: 2021-06-11 22:38:15.478154

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ebd745ae92c'
down_revision = '4f583717507b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'cathedra', ['name'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'cathedra', type_='unique')
    # ### end Alembic commands ###
