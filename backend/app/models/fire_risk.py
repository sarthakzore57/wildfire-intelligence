from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List

from app.db.session import Base


class FireRiskZone(Base):
    __tablename__ = "fire_risk_zones"

    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    risk_level = Column(Float)  # 0-1 scale
    risk_category = Column(String)  # "Low", "Medium", "High"
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Weather conditions at the time of prediction
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    
    # Vegetation details
    vegetation_density = Column(Float, nullable=True)
    vegetation_type = Column(String, nullable=True)
    soil_moisture = Column(Float, nullable=True)
    
    # Prediction details
    prediction_model = Column(String)
    confidence_score = Column(Float)
    
    # Relationships
    fire_incidents = relationship("FireIncident", back_populates="risk_zone")
    alerts = relationship("Alert", back_populates="risk_zone")


class FireIncident(Base):
    __tablename__ = "fire_incidents"

    id = Column(Integer, primary_key=True, index=True)
    risk_zone_id = Column(Integer, ForeignKey("fire_risk_zones.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    severity = Column(String)  # "Low", "Medium", "High"
    area_affected = Column(Float, nullable=True)  # in square kilometers
    status = Column(String)  # "Active", "Contained", "Extinguished"
    source = Column(String)  # "Satellite", "Ground Report", "Official"
    description = Column(Text, nullable=True)
    
    # Relationships
    risk_zone = relationship("FireRiskZone", back_populates="fire_incidents")


class SavedRegion(Base):
    __tablename__ = "saved_regions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    region_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Alert preferences specific to this region
    alert_threshold = Column(Float, default=0.7)
    
    # Relationships
    user = relationship("User", back_populates="saved_regions")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    risk_zone_id = Column(Integer, ForeignKey("fire_risk_zones.id"))
    alert_time = Column(DateTime, default=datetime.utcnow)
    risk_level = Column(Float)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    is_sent_email = Column(Boolean, default=False)
    is_sent_sms = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    risk_zone = relationship("FireRiskZone", back_populates="alerts") 