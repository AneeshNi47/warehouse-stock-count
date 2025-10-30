"""Remove unique index from barcode_entry

Revision ID: 2e23b49a610f
Revises: a84d9b454918
Create Date: 2025-10-28 18:00:20.213930

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e23b49a610f'
down_revision = 'a84d9b454918'
branch_labels = None
depends_on = None

def upgrade():
    # Drop the unique index (if it exists)
    op.drop_index('idx_barcode_unique', table_name='barcode_entry')

def downgrade():
    # Recreate the unique index if rolled back
    op.create_index('idx_barcode_unique', 'barcode_entry', ['barcode'], unique=True)