import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import ValidationError

from app import schemas
from app.core import security
from app.core.config import settings
from app.db.influx import get_influxdb_client
from app.services import user_service

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login/access-token")


def get_db():
    yield None


def get_influx():
    client = get_influxdb_client()
    if client is None:
        logger.warning("InfluxDB client not available, yielding None")
        yield None
        return

    try:
        yield client
    finally:
        try:
            client.close()
        except Exception as exc:
            logger.error("Error closing InfluxDB client: %s", exc)


def get_current_user(token: str = Depends(oauth2_scheme)) -> schemas.User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = schemas.TokenPayload(**payload)
    except (jwt.JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    if not token_data.sub:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    user = user_service.get_user(token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return schemas.User.model_validate(user)


def get_current_active_superuser(
    current_user: schemas.User = Depends(get_current_user),
) -> schemas.User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user
