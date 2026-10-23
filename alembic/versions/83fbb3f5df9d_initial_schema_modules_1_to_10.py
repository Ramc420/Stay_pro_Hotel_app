"""initial_schema_modules_1_to_10

Revision ID: 83fbb3f5df9d
Revises: 
Create Date: 2026-10-21 09:01:59.191699

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83fbb3f5df9d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from database import Base
    import models
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from database import Base
    import models
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)

