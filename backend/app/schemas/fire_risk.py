from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class FireRiskZoneBase(BaseModel):
    region_name: str
    latitude: float
    longitude: float
    risk_level: float
    risk_category: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    wind_speed: Optional[float] = None
    precipitation: Optional[float] = None
    vegetation_density: Optional[float] = None
    vegetation_type: Optional[str] = None
    soil_moisture: Optional[float] = None
    prediction_model: str
    confidence_score: float

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("Risk level must be between 0 and 1")
        return value

    @field_validator("risk_category")
    @classmethod
    def validate_risk_category(cls, value: str) -> str:
        valid_categories = {"Low", "Medium", "High"}
        if value not in valid_categories:
            raise ValueError(f'Risk category must be one of: {", ".join(sorted(valid_categories))}')
        return value

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def normalize_longitude(cls, value: float) -> float:
        normalized = ((value + 180) % 360) - 180
        return 180.0 if normalized == -180 and value > 0 else normalized


class FireRiskZoneCreate(FireRiskZoneBase):
    pass


class FireRiskZoneUpdate(FireRiskZoneBase):
    region_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    risk_level: Optional[float] = None
    risk_category: Optional[str] = None
    prediction_model: Optional[str] = None
    confidence_score: Optional[float] = None


class FireRiskZoneInDBBase(FireRiskZoneBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    timestamp: datetime


class FireRiskZone(FireRiskZoneInDBBase):
    pass


class FireIncidentBase(BaseModel):
    risk_zone_id: str
    latitude: float
    longitude: float
    start_date: datetime
    end_date: Optional[datetime] = None
    severity: str
    area_affected: Optional[float] = None
    status: str
    source: str
    description: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        valid_severities = {"Low", "Medium", "High"}
        if value not in valid_severities:
            raise ValueError(f'Severity must be one of: {", ".join(sorted(valid_severities))}')
        return value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        valid_statuses = {"Active", "Contained", "Controlled", "Extinguished"}
        if value not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(sorted(valid_statuses))}')
        return value

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        valid_sources = {
            "Ground Report",
            "NASA FIRMS",
            "NASA FIRMS Realtime",
            "NIFC Realtime",
            "Official",
            "Satellite",
            "Test Script",
            "USFS",
        }
        if value not in valid_sources:
            raise ValueError(f'Source must be one of: {", ".join(sorted(valid_sources))}')
        return value

    @field_validator("latitude")
    @classmethod
    def validate_incident_latitude(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def normalize_incident_longitude(cls, value: float) -> float:
        normalized = ((value + 180) % 360) - 180
        return 180.0 if normalized == -180 and value > 0 else normalized


class FireIncidentCreate(FireIncidentBase):
    pass


class FireIncidentUpdate(FireIncidentBase):
    risk_zone_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_date: Optional[datetime] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None


class FireIncidentInDBBase(FireIncidentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str


class FireIncident(FireIncidentInDBBase):
    pass


class SavedRegionBase(BaseModel):
    user_id: str
    region_name: str
    latitude: float
    longitude: float
    alert_threshold: Optional[float] = 0.7

    @field_validator("alert_threshold")
    @classmethod
    def validate_threshold(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not 0 <= value <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return value

    @field_validator("latitude")
    @classmethod
    def validate_saved_region_latitude(cls, value: float) -> float:
        if not -90 <= value <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def normalize_saved_region_longitude(cls, value: float) -> float:
        normalized = ((value + 180) % 360) - 180
        return 180.0 if normalized == -180 and value > 0 else normalized


class SavedRegionCreate(SavedRegionBase):
    pass


class SavedRegionUpdate(BaseModel):
    region_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    alert_threshold: Optional[float] = None


class SavedRegionInDBBase(SavedRegionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class SavedRegion(SavedRegionInDBBase):
    pass


class AlertBase(BaseModel):
    user_id: str
    risk_zone_id: str
    risk_level: float
    message: str
    is_read: Optional[bool] = False
    is_sent_email: Optional[bool] = False
    is_sent_sms: Optional[bool] = False


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_sent_email: Optional[bool] = None
    is_sent_sms: Optional[bool] = None


class AlertInDBBase(AlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    alert_time: datetime


class Alert(AlertInDBBase):
    pass
