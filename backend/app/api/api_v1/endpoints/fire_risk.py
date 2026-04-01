from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.services import fire_risk_service

router = APIRouter()


@router.get("/zones", response_model=List[schemas.FireRiskZone])
def read_fire_risk_zones(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    min_risk_level: Optional[float] = None,
    max_risk_level: Optional[float] = None,
    region_name: Optional[str] = None,
    risk_category: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve fire risk zones with filtering options.
    """
    zones = fire_risk_service.get_fire_risk_zones(
        db, 
        skip=skip, 
        limit=limit,
        min_risk_level=min_risk_level,
        max_risk_level=max_risk_level,
        region_name=region_name,
        risk_category=risk_category
    )
    return zones


@router.get("/zones/{zone_id}", response_model=schemas.FireRiskZone)
def read_fire_risk_zone(
    zone_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get specific fire risk zone by ID.
    """
    zone = fire_risk_service.get_fire_risk_zone(db, zone_id=zone_id)
    if not zone:
        raise HTTPException(
            status_code=404,
            detail="Fire risk zone not found",
        )
    return zone


@router.get("/zones/by-coordinates", response_model=schemas.FireRiskZone)
def read_fire_risk_zone_by_coords(
    latitude: float,
    longitude: float,
    tolerance: float = 0.01,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get fire risk zone by coordinates within a tolerance.
    """
    zone = fire_risk_service.get_fire_risk_zone_by_coords(
        db, 
        latitude=latitude, 
        longitude=longitude,
        tolerance=tolerance
    )
    if not zone:
        raise HTTPException(
            status_code=404,
            detail="No fire risk zone found at these coordinates",
        )
    return zone


@router.post("/zones", response_model=schemas.FireRiskZone)
def create_fire_risk_zone(
    *,
    db: Session = Depends(deps.get_db),
    fire_risk_in: schemas.FireRiskZoneCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new fire risk zone. Only accessible by superusers.
    """
    zone = fire_risk_service.create_fire_risk_zone(db, fire_risk_in=fire_risk_in)
    return zone


@router.put("/zones/{zone_id}", response_model=schemas.FireRiskZone)
def update_fire_risk_zone(
    *,
    zone_id: int,
    db: Session = Depends(deps.get_db),
    fire_risk_in: schemas.FireRiskZoneUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a fire risk zone. Only accessible by superusers.
    """
    zone = fire_risk_service.get_fire_risk_zone(db, zone_id=zone_id)
    if not zone:
        raise HTTPException(
            status_code=404,
            detail="Fire risk zone not found",
        )
    
    zone = fire_risk_service.update_fire_risk_zone(db, zone_id=zone_id, fire_risk_in=fire_risk_in)
    return zone


@router.delete("/zones/{zone_id}", response_model=schemas.Msg)
def delete_fire_risk_zone(
    *,
    zone_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a fire risk zone. Only accessible by superusers.
    """
    zone = fire_risk_service.get_fire_risk_zone(db, zone_id=zone_id)
    if not zone:
        raise HTTPException(
            status_code=404,
            detail="Fire risk zone not found",
        )
    
    success = fire_risk_service.delete_fire_risk_zone(db, zone_id=zone_id)
    if success:
        return {"msg": "Fire risk zone deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Error deleting fire risk zone")


@router.get("/regions/saved", response_model=List[schemas.SavedRegion])
def read_saved_regions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve saved regions for current user.
    """
    regions = fire_risk_service.get_saved_regions_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )
    return regions


@router.post("/regions/saved", response_model=schemas.SavedRegion)
def create_saved_region(
    *,
    db: Session = Depends(deps.get_db),
    region_in: schemas.SavedRegionCreate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Save a new region for monitoring.
    """
    # Verify that the user_id in the request matches the current user
    if region_in.user_id != current_user.id:
        raise HTTPException(
            status_code=400,
            detail="User ID in request does not match authenticated user",
        )
    
    region = fire_risk_service.save_region_for_user(db, region_in=region_in)
    return region


@router.delete("/regions/saved/{region_id}", response_model=schemas.Msg)
def delete_saved_region(
    *,
    region_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete a saved region.
    """
    # Get the region to check ownership
    region = db.query(models.SavedRegion).filter(models.SavedRegion.id == region_id).first()
    if not region:
        raise HTTPException(
            status_code=404,
            detail="Saved region not found",
        )
    
    # Verify ownership
    if region.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to delete this region",
        )
    
    success = fire_risk_service.delete_saved_region(db, region_id=region_id)
    if success:
        return {"msg": "Saved region deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Error deleting saved region") 