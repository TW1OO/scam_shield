from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from database import Base


class Recording(Base):
    __tablename__ = "recordings"

    id = Column(Integer, primary_key=True, index=True)
    video_path = Column(String)
    audio_path = Column(String)
    duration = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
