from datetime import datetime, timezone
import uuid6
from sqlalchemy.orm import Mapped, mapped_column
from app.extensions import db

def generate_uuid():
    return uuid6.uuid7()

class BaseModel(db.Model):
    __abstract__ = True
    
    id: Mapped[uuid6.UUID] = mapped_column(db.Uuid, primary_key=True, default=generate_uuid)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
