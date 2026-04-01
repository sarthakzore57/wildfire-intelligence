from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # User's preferred region for monitoring
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    region_name = Column(String, nullable=True)
    
    # User's alert preferences
    alert_threshold = Column(Float, default=0.7)  # Fire risk threshold (0-1)
    email_alerts = Column(Boolean, default=True)
    sms_alerts = Column(Boolean, default=False)
    phone_number = Column(String, nullable=True)
    
    # Relationships
    alerts = relationship("Alert", back_populates="user")
    saved_regions = relationship("SavedRegion", back_populates="user") 