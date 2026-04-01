from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    region_name: Optional[str] = None
    alert_threshold: Optional[float] = 0.7
    email_alerts: Optional[bool] = True
    sms_alerts: Optional[bool] = False
    phone_number: Optional[str] = None


class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str

    @field_validator("alert_threshold")
    @classmethod
    def validate_threshold(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not 0 <= value <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        return value


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDBBase(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    created_at: Optional[datetime] = None


class User(UserInDBBase):
    pass


class UserInDB(UserInDBBase):
    hashed_password: str
