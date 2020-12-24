"""Change user_oauth table for new use case

Revision ID: 10023013f155
Revises: 2a849701bd03
Create Date: 2020-12-18 20:41:19.386588

"""

# revision identifiers, used by Alembic.
revision = "10023013f155"
down_revision = "2a849701bd03"
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column("user_oauth", "name", new_column_name="oauth_provider_user_name")
    op.add_column("user_oauth", sa.Column("first_name", sa.String(255)))
    op.add_column("user_oauth", sa.Column("last_name", sa.String(255)))
    # By the international standard(E.164 ITU-T Recommendation) phone numbers are limited to up to 15 chars
    # notice that the chars '+' and '-' are not included in the 15 chars limit, so i added 1 for the '+' and 1 for '-'
    # so numbers like "+972 050-123-1234" will pass
    op.add_column("user_oauth", sa.Column("phone", sa.String(17)))
    op.add_column("user_oauth", sa.Column("user_type", sa.String(64), index=True))
    # The RFC 2616("Hypertext Transfer Protocol -- HTTP/1.1,") does not specify any requirement for URL length,
    # but Microsoft Internet Explorer have a maximum URL length of 2,083 characters and as i believe that we will not
    # get a url length that is even near to 2,083 characters, i decided to set the max url to 2,083 characters.
    op.add_column("user_oauth", sa.Column("user_url", sa.String(2083)))
    op.add_column("user_oauth", sa.Column("user_desc", sa.String(2048)))
    # The registration is build from 2 parts: 1. OAuth 2. user is giving us his contacts information
    op.add_column("user_oauth", sa.Column("is_user_completed_registration", sa.Boolean))


def downgrade():
    op.drop_column("user_oauth", "first_name")
    op.drop_column("user_oauth", "last_name")
    op.drop_column("user_oauth", "phone")
    op.drop_column("user_oauth", "user_type")
    op.drop_column("user_oauth", "user_url")
    op.drop_column("user_oauth", "user_desc")
    op.drop_column("user_oauth", "is_user_completed_registration")
    op.alter_column("user_oauth", "oauth_provider_user_name", new_column_name="name")
