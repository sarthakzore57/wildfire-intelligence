from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app import models, schemas


def get_fire_risk_zone(db: Session, zone_id: int) -> Optional[models.FireRiskZone]:
    """
    Get a fire risk zone by ID
    """
    return db.query(models.FireRiskZone).filter(models.FireRiskZone.id == zone_id).first()


def get_fire_risk_zones(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    min_risk_level: Optional[float] = None,
    max_risk_level: Optional[float] = None,
    region_name: Optional[str] = None,
    risk_category: Optional[str] = None,
) -> List[models.FireRiskZone]:
    """
    Get multiple fire risk zones with filtering options
    """
    query = db.query(models.FireRiskZone)
    
    if min_risk_level is not None:
        query = query.filter(models.FireRiskZone.risk_level >= min_risk_level)
    
    if max_risk_level is not None:
        query = query.filter(models.FireRiskZone.risk_level <= max_risk_level)
    
    if region_name:
        query = query.filter(models.FireRiskZone.region_name.ilike(f"%{region_name}%"))
    
    if risk_category:
        query = query.filter(models.FireRiskZone.risk_category == risk_category)
    
    # Order by risk_level descending to get highest risk zones first
    query = query.order_by(models.FireRiskZone.risk_level.desc())
    
    return query.offset(skip).limit(limit).all()


def get_fire_risk_zone_by_coords(
    db: Session, 
    latitude: float, 
    longitude: float,
    tolerance: float = 0.01
) -> Optional[models.FireRiskZone]:
    """
    Get a fire risk zone by coordinates within a tolerance
    """
    return db.query(models.FireRiskZone).filter(
        models.FireRiskZone.latitude.between(latitude - tolerance, latitude + tolerance),
        models.FireRiskZone.longitude.between(longitude - tolerance, longitude + tolerance)
    ).order_by(models.FireRiskZone.timestamp.desc()).first()


def create_fire_risk_zone(
    db: Session, fire_risk_in: schemas.FireRiskZoneCreate
) -> models.FireRiskZone:
    """
    Create a new fire risk zone
    """
    risk_data = fire_risk_in.model_dump()
    db_fire_risk = models.FireRiskZone(**risk_data)
    db.add(db_fire_risk)
    db.commit()
    db.refresh(db_fire_risk)
    return db_fire_risk


def update_fire_risk_zone(
    db: Session, zone_id: int, fire_risk_in: schemas.FireRiskZoneUpdate
) -> Optional[models.FireRiskZone]:
    """
    Update a fire risk zone
    """
    db_fire_risk = get_fire_risk_zone(db, zone_id=zone_id)
    if not db_fire_risk:
        return None
    
    update_data = fire_risk_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_fire_risk, field, value)
    
    db.add(db_fire_risk)
    db.commit()
    db.refresh(db_fire_risk)
    return db_fire_risk


def delete_fire_risk_zone(db: Session, zone_id: int) -> bool:
    """
    Delete a fire risk zone
    """
    db_fire_risk = get_fire_risk_zone(db, zone_id=zone_id)
    if not db_fire_risk:
        return False
    db.delete(db_fire_risk)
    db.commit()
    return True


def get_fire_incidents(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    region_name: Optional[str] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> List[models.FireIncident]:
    """
    Get fire incidents with filtering options
    """
    query = db.query(models.FireIncident)
    
    # Join with FireRiskZone to filter by region name
    if region_name:
        query = query.join(models.FireRiskZone).filter(
            models.FireRiskZone.region_name.ilike(f"%{region_name}%")
        )
    
    if start_date_from:
        query = query.filter(models.FireIncident.start_date >= start_date_from)
    
    if start_date_to:
        query = query.filter(models.FireIncident.start_date <= start_date_to)
    
    if status:
        query = query.filter(models.FireIncident.status == status)
    
    if severity:
        query = query.filter(models.FireIncident.severity == severity)
    
    # Order by start_date descending to get latest incidents first
    query = query.order_by(models.FireIncident.start_date.desc())
    
    return query.offset(skip).limit(limit).all()


def create_fire_incident(
    db: Session, incident_in: schemas.FireIncidentCreate
) -> models.FireIncident:
    """
    Create a new fire incident
    """
    incident_data = incident_in.model_dump()
    db_incident = models.FireIncident(**incident_data)
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident


def get_saved_regions_by_user(
    db: Session, user_id: int, skip: int = 0, limit: int = 100
) -> List[models.SavedRegion]:
    """
    Get saved regions for a user
    """
    return db.query(models.SavedRegion).filter(
        models.SavedRegion.user_id == user_id
    ).offset(skip).limit(limit).all()


def save_region_for_user(
    db: Session, region_in: schemas.SavedRegionCreate
) -> models.SavedRegion:
    """
    Save a region for a user
    """
    region_data = region_in.model_dump()
    db_region = models.SavedRegion(**region_data)
    db.add(db_region)
    db.commit()
    db.refresh(db_region)
    return db_region


def delete_saved_region(db: Session, region_id: int) -> bool:
    """
    Delete a saved region
    """
    db_region = db.query(models.SavedRegion).filter(
        models.SavedRegion.id == region_id
    ).first()
    if not db_region:
        return False
    db.delete(db_region)
    db.commit()
    return True 
