from alembic import context
from app.core.database import Base
from app.domain.models import *

target_metadata = Base.metadata
