"""complete_schema_modules_11_to_50

Revision ID: 378ed64b09b6
Revises: 83fbb3f5df9d
Create Date: 2026-10-23 15:10:44.713060

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '378ed64b09b6'
down_revision = '83fbb3f5df9d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    from database import Base
    import models
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    pass

