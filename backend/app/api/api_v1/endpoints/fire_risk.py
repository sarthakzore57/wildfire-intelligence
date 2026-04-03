from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps
from app.services import fire_risk_service

router = APIRouter()


@router.get("/zones", response_model=List[schemas.FireRiskZone])
def read_fire_risk_zones(
    skip: int = 0,
    limit: int = 100,
    min_risk_level: Optional[float] = None,
    max_risk_level: Optional[float] = None,
    region_name: Optional[str] = None,
    risk_category: Optional[str] = None,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    zones = fire_risk_service.get_fire_risk_zones(
        skip=skip,
        limit=limit,
        min_risk_level=min_risk_level,
        max_risk_level=max_risk_level,
        region_name=region_name,
        risk_category=risk_category,
    )
    return [schemas.FireRiskZone.model_validate(zone) for zone in zones]


@router.get("/zones/{zone_id}", response_model=schemas.FireRiskZone)
def read_fire_risk_zone(
    zone_id: str,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    zone = fire_risk_service.get_fire_risk_zone(zone_id=zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Fire risk zone not found")
    return schemas.FireRiskZone.model_validate(zone)


@router.get("/zones/by-coordinates", response_model=schemas.FireRiskZone)
def read_fire_risk_zone_by_coords(
    latitude: float,
    longitude: float,
    tolerance: float = 0.01,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    zone = fire_risk_service.get_fire_risk_zone_by_coords(
        latitude=latitude, longitude=longitude, tolerance=tolerance
    )
    if not zone:
        raise HTTPException(
            status_code=404,
            detail="No fire risk zone found at these coordinates",
        )
    return schemas.FireRiskZone.model_validate(zone)


@router.post("/zones", response_model=schemas.FireRiskZone)
def create_fire_risk_zone(
    *,
    fire_risk_in: schemas.FireRiskZoneCreate,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    return schemas.FireRiskZone.model_validate(
        fire_risk_service.create_fire_risk_zone(fire_risk_in=fire_risk_in)
    )


@router.put("/zones/{zone_id}", response_model=schemas.FireRiskZone)
def update_fire_risk_zone(
    *,
    zone_id: str,
    fire_risk_in: schemas.FireRiskZoneUpdate,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    zone = fire_risk_service.update_fire_risk_zone(zone_id=zone_id, fire_risk_in=fire_risk_in)
    if not zone:
        raise HTTPException(status_code=404, detail="Fire risk zone not found")
    return schemas.FireRiskZone.model_validate(zone)


@router.delete("/zones/{zone_id}", response_model=schemas.Msg)
def delete_fire_risk_zone(
    *,
    zone_id: str,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    if fire_risk_service.delete_fire_risk_zone(zone_id=zone_id):
        return {"msg": "Fire risk zone deleted successfully"}
    raise HTTPException(status_code=404, detail="Fire risk zone not found")


@router.get("/regions/saved", response_model=List[schemas.SavedRegion])
def read_saved_regions(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    regions = fire_risk_service.get_saved_regions_by_user(
        user_id=current_user.id, skip=skip, limit=limit
    )
    return [schemas.SavedRegion.model_validate(region) for region in regions]


@router.post("/regions/saved", response_model=schemas.SavedRegion)
def create_saved_region(
    *,
    region_in: schemas.SavedRegionCreate,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    if region_in.user_id != current_user.id:
        raise HTTPException(
            status_code=400,
            detail="User ID in request does not match authenticated user",
        )
    return schemas.SavedRegion.model_validate(
        fire_risk_service.save_region_for_user(region_in=region_in)
    )


@router.delete("/regions/saved/{region_id}", response_model=schemas.Msg)
def delete_saved_region(
    *,
    region_id: str,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    region = fire_risk_service.get_saved_region(region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Saved region not found")
    if region["user_id"] != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to delete this region",
        )
    if fire_risk_service.delete_saved_region(region_id=region_id):
        return {"msg": "Saved region deleted successfully"}
    raise HTTPException(status_code=500, detail="Error deleting saved region")
