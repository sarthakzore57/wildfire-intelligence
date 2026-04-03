from __future__ import annotations

from datetime import datetime
from typing import Optional

from app import schemas
from app.services.firebase_service import get_firestore_client

RISK_ZONES_COLLECTION = "fire_risk_zones"
INCIDENTS_COLLECTION = "fire_incidents"
SAVED_REGIONS_COLLECTION = "saved_regions"
ALERTS_COLLECTION = "alerts"


def _normalize(doc_id: str, data: dict, defaults: Optional[dict] = None) -> dict:
    payload = {"id": doc_id, **data}
    if defaults:
        for key, value in defaults.items():
            payload.setdefault(key, value)
    return payload


def get_fire_risk_zone(zone_id: str) -> Optional[dict]:
    snapshot = get_firestore_client().collection(RISK_ZONES_COLLECTION).document(zone_id).get()
    if not snapshot.exists:
        return None
    return _normalize(snapshot.id, snapshot.to_dict(), {"timestamp": datetime.utcnow()})


def get_fire_risk_zones(
    skip: int = 0,
    limit: int = 100,
    min_risk_level: Optional[float] = None,
    max_risk_level: Optional[float] = None,
    region_name: Optional[str] = None,
    risk_category: Optional[str] = None,
) -> list[dict]:
    docs = get_firestore_client().collection(RISK_ZONES_COLLECTION).stream()
    zones = [_normalize(doc.id, doc.to_dict(), {"timestamp": datetime.utcnow()}) for doc in docs]

    if min_risk_level is not None:
        zones = [zone for zone in zones if zone.get("risk_level", 0) >= min_risk_level]
    if max_risk_level is not None:
        zones = [zone for zone in zones if zone.get("risk_level", 0) <= max_risk_level]
    if region_name:
        needle = region_name.lower()
        zones = [zone for zone in zones if needle in zone.get("region_name", "").lower()]
    if risk_category:
        zones = [zone for zone in zones if zone.get("risk_category") == risk_category]

    zones.sort(key=lambda zone: zone.get("risk_level", 0), reverse=True)
    return zones[skip : skip + limit]


def get_fire_risk_zone_by_coords(latitude: float, longitude: float, tolerance: float = 0.01) -> Optional[dict]:
    docs = get_firestore_client().collection(RISK_ZONES_COLLECTION).stream()
    matches = []
    for doc in docs:
        zone = _normalize(doc.id, doc.to_dict(), {"timestamp": datetime.utcnow()})
        if abs(zone.get("latitude", 0) - latitude) <= tolerance and abs(zone.get("longitude", 0) - longitude) <= tolerance:
            matches.append(zone)

    matches.sort(key=lambda zone: zone.get("timestamp") or datetime.min, reverse=True)
    return matches[0] if matches else None


def create_fire_risk_zone(fire_risk_in: schemas.FireRiskZoneCreate) -> dict:
    risk_data = fire_risk_in.model_dump()
    risk_data["timestamp"] = datetime.utcnow()
    ref = get_firestore_client().collection(RISK_ZONES_COLLECTION).document()
    ref.set(risk_data)
    return _normalize(ref.id, risk_data)


def update_fire_risk_zone(zone_id: str, fire_risk_in: schemas.FireRiskZoneUpdate) -> Optional[dict]:
    existing = get_fire_risk_zone(zone_id)
    if not existing:
        return None
    update_data = fire_risk_in.model_dump(exclude_unset=True)
    get_firestore_client().collection(RISK_ZONES_COLLECTION).document(zone_id).update(update_data)
    existing.update(update_data)
    return existing


def delete_fire_risk_zone(zone_id: str) -> bool:
    if not get_fire_risk_zone(zone_id):
        return False
    get_firestore_client().collection(RISK_ZONES_COLLECTION).document(zone_id).delete()
    return True


def get_fire_incidents(
    skip: int = 0,
    limit: int = 100,
    region_name: Optional[str] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> list[dict]:
    docs = get_firestore_client().collection(INCIDENTS_COLLECTION).stream()
    incidents = [_normalize(doc.id, doc.to_dict()) for doc in docs]

    if region_name:
        zone_ids = {
            zone["id"]
            for zone in get_fire_risk_zones(limit=10000, region_name=region_name)
        }
        incidents = [incident for incident in incidents if incident.get("risk_zone_id") in zone_ids]
    if start_date_from:
        incidents = [incident for incident in incidents if incident.get("start_date") and incident["start_date"] >= start_date_from]
    if start_date_to:
        incidents = [incident for incident in incidents if incident.get("start_date") and incident["start_date"] <= start_date_to]
    if status:
        incidents = [incident for incident in incidents if incident.get("status") == status]
    if severity:
        incidents = [incident for incident in incidents if incident.get("severity") == severity]

    incidents.sort(key=lambda incident: incident.get("start_date") or datetime.min, reverse=True)
    return incidents[skip : skip + limit]


def get_fire_incident(incident_id: str) -> Optional[dict]:
    snapshot = get_firestore_client().collection(INCIDENTS_COLLECTION).document(incident_id).get()
    if not snapshot.exists:
        return None
    return _normalize(snapshot.id, snapshot.to_dict())


def create_fire_incident(incident_in: schemas.FireIncidentCreate) -> dict:
    incident_data = incident_in.model_dump()
    ref = get_firestore_client().collection(INCIDENTS_COLLECTION).document()
    ref.set(incident_data)
    return _normalize(ref.id, incident_data)


def update_fire_incident(incident_id: str, incident_in: schemas.FireIncidentUpdate) -> Optional[dict]:
    existing = get_fire_incident(incident_id)
    if not existing:
        return None
    update_data = incident_in.model_dump(exclude_unset=True)
    get_firestore_client().collection(INCIDENTS_COLLECTION).document(incident_id).update(update_data)
    existing.update(update_data)
    return existing


def delete_fire_incident(incident_id: str) -> bool:
    if not get_fire_incident(incident_id):
        return False
    get_firestore_client().collection(INCIDENTS_COLLECTION).document(incident_id).delete()
    return True


def get_saved_regions_by_user(user_id: str, skip: int = 0, limit: int = 100) -> list[dict]:
    docs = (
        get_firestore_client()
        .collection(SAVED_REGIONS_COLLECTION)
        .where("user_id", "==", user_id)
        .stream()
    )
    regions = [_normalize(doc.id, doc.to_dict(), {"created_at": datetime.utcnow()}) for doc in docs]
    regions.sort(key=lambda region: region.get("created_at") or datetime.min, reverse=True)
    return regions[skip : skip + limit]


def get_saved_region(region_id: str) -> Optional[dict]:
    snapshot = get_firestore_client().collection(SAVED_REGIONS_COLLECTION).document(region_id).get()
    if not snapshot.exists:
        return None
    return _normalize(snapshot.id, snapshot.to_dict(), {"created_at": datetime.utcnow()})


def save_region_for_user(region_in: schemas.SavedRegionCreate) -> dict:
    region_data = region_in.model_dump()
    region_data["created_at"] = datetime.utcnow()
    ref = get_firestore_client().collection(SAVED_REGIONS_COLLECTION).document()
    ref.set(region_data)
    return _normalize(ref.id, region_data)


def delete_saved_region(region_id: str) -> bool:
    if not get_saved_region(region_id):
        return False
    get_firestore_client().collection(SAVED_REGIONS_COLLECTION).document(region_id).delete()
    return True


def get_alerts_by_user(user_id: str, skip: int = 0, limit: int = 100, is_read: Optional[bool] = None) -> list[dict]:
    docs = (
        get_firestore_client()
        .collection(ALERTS_COLLECTION)
        .where("user_id", "==", user_id)
        .stream()
    )
    alerts = [_normalize(doc.id, doc.to_dict(), {"alert_time": datetime.utcnow()}) for doc in docs]
    if is_read is not None:
        alerts = [alert for alert in alerts if alert.get("is_read") == is_read]
    alerts.sort(key=lambda alert: alert.get("alert_time") or datetime.min, reverse=True)
    return alerts[skip : skip + limit]


def get_alert(alert_id: str) -> Optional[dict]:
    snapshot = get_firestore_client().collection(ALERTS_COLLECTION).document(alert_id).get()
    if not snapshot.exists:
        return None
    return _normalize(snapshot.id, snapshot.to_dict(), {"alert_time": datetime.utcnow()})


def create_alert(user_id: str, risk_zone_id: str, risk_level: float, message: str) -> dict:
    alert_data = {
        "user_id": user_id,
        "risk_zone_id": risk_zone_id,
        "risk_level": risk_level,
        "message": message,
        "is_read": False,
        "is_sent_email": False,
        "is_sent_sms": False,
        "alert_time": datetime.utcnow(),
    }
    ref = get_firestore_client().collection(ALERTS_COLLECTION).document()
    ref.set(alert_data)
    return _normalize(ref.id, alert_data)


def update_alert(alert_id: str, alert_in: schemas.AlertUpdate) -> Optional[dict]:
    existing = get_alert(alert_id)
    if not existing:
        return None
    update_data = alert_in.model_dump(exclude_unset=True)
    get_firestore_client().collection(ALERTS_COLLECTION).document(alert_id).update(update_data)
    existing.update(update_data)
    return existing


def delete_alert(alert_id: str) -> bool:
    if not get_alert(alert_id):
        return False
    get_firestore_client().collection(ALERTS_COLLECTION).document(alert_id).delete()
    return True


def mark_all_alerts_read(user_id: str) -> None:
    alerts = get_alerts_by_user(user_id, skip=0, limit=10000, is_read=False)
    firestore_db = get_firestore_client()
    for alert in alerts:
        firestore_db.collection(ALERTS_COLLECTION).document(alert["id"]).update({"is_read": True})
