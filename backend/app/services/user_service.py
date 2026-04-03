from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from app import schemas
from app.core.security import get_password_hash, verify_password
from app.services.firebase_service import get_firestore_client

logger = logging.getLogger(__name__)

USERS_COLLECTION = "users"


def _normalize_user(doc_id: str, data: dict) -> dict:
    payload = {"id": doc_id, **data}
    payload.setdefault("created_at", datetime.utcnow())
    payload.setdefault("is_active", True)
    payload.setdefault("is_superuser", False)
    payload.setdefault("alert_threshold", 0.7)
    payload.setdefault("email_alerts", True)
    payload.setdefault("sms_alerts", False)
    return payload


def get_user(user_id: str) -> Optional[dict]:
    firestore_db = get_firestore_client()
    snapshot = firestore_db.collection(USERS_COLLECTION).document(user_id).get()
    if not snapshot.exists:
        return None
    return _normalize_user(snapshot.id, snapshot.to_dict())


def get_user_by_email(email: str) -> Optional[dict]:
    firestore_db = get_firestore_client()
    docs = (
        firestore_db.collection(USERS_COLLECTION)
        .where("email", "==", email)
        .limit(1)
        .stream()
    )
    for doc in docs:
        return _normalize_user(doc.id, doc.to_dict())
    return None


def get_user_by_username(username: str) -> Optional[dict]:
    firestore_db = get_firestore_client()
    docs = (
        firestore_db.collection(USERS_COLLECTION)
        .where("username", "==", username)
        .limit(1)
        .stream()
    )
    for doc in docs:
        return _normalize_user(doc.id, doc.to_dict())
    return None


def get_users(skip: int = 0, limit: int = 100) -> list[dict]:
    firestore_db = get_firestore_client()
    docs = firestore_db.collection(USERS_COLLECTION).stream()
    users = [_normalize_user(doc.id, doc.to_dict()) for doc in docs]
    users.sort(key=lambda user: user.get("created_at") or datetime.min)
    return users[skip : skip + limit]


def create_user(user_in: schemas.UserCreate) -> Optional[dict]:
    if get_user_by_email(user_in.email) or get_user_by_username(user_in.username):
        return None

    firestore_db = get_firestore_client()
    user_data = {
        "email": user_in.email,
        "username": user_in.username,
        "hashed_password": get_password_hash(user_in.password),
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow(),
        "latitude": user_in.latitude,
        "longitude": user_in.longitude,
        "region_name": user_in.region_name,
        "alert_threshold": user_in.alert_threshold,
        "email_alerts": user_in.email_alerts,
        "sms_alerts": user_in.sms_alerts,
        "phone_number": user_in.phone_number,
    }
    ref = firestore_db.collection(USERS_COLLECTION).document()
    ref.set(user_data)
    logger.info("Created Firebase user %s", user_in.email)
    return _normalize_user(ref.id, user_data)


def update_user(user_id: str, user_in: schemas.UserUpdate) -> Optional[dict]:
    existing = get_user(user_id)
    if not existing:
        return None

    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    elif "password" in update_data:
        update_data.pop("password")

    firestore_db = get_firestore_client()
    firestore_db.collection(USERS_COLLECTION).document(user_id).update(update_data)
    existing.update(update_data)
    return existing


def delete_user(user_id: str) -> bool:
    existing = get_user(user_id)
    if not existing:
        return False

    firestore_db = get_firestore_client()
    firestore_db.collection(USERS_COLLECTION).document(user_id).delete()
    return True


def authenticate(email: str, password: str) -> Optional[dict]:
    user = get_user_by_email(email)
    if not user:
        return None
    hashed_password = user.get("hashed_password")
    if not hashed_password or not verify_password(password, hashed_password):
        return None
    return user


def check_db_connection() -> bool:
    try:
        list(get_firestore_client().collections())
        return True
    except Exception as exc:
        logger.error("Firebase connection error: %s", exc)
        return False
