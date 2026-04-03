from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps
from app.services import fire_risk_service

router = APIRouter()


@router.get("/", response_model=List[schemas.FireIncident])
def read_fire_incidents(
    skip: int = 0,
    limit: int = 100,
    region_name: Optional[str] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    incidents = fire_risk_service.get_fire_incidents(
        skip=skip,
        limit=limit,
        region_name=region_name,
        start_date_from=start_date_from,
        start_date_to=start_date_to,
        status=status,
        severity=severity,
    )
    return [schemas.FireIncident.model_validate(incident) for incident in incidents]


@router.get("/simple", response_model=List[schemas.FireIncident])
def test_fire_incidents(
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    incidents = fire_risk_service.get_fire_incidents(limit=5)
    return [schemas.FireIncident.model_validate(incident) for incident in incidents]


@router.get("/{incident_id}", response_model=schemas.FireIncident)
def read_fire_incident(
    incident_id: str,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    incident = fire_risk_service.get_fire_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Fire incident not found")
    return schemas.FireIncident.model_validate(incident)


@router.post("/", response_model=schemas.FireIncident)
def create_fire_incident(
    *,
    incident_in: schemas.FireIncidentCreate,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    risk_zone = fire_risk_service.get_fire_risk_zone(zone_id=incident_in.risk_zone_id)
    if not risk_zone:
        raise HTTPException(
            status_code=404,
            detail=f"Fire risk zone with ID {incident_in.risk_zone_id} not found",
        )
    return schemas.FireIncident.model_validate(
        fire_risk_service.create_fire_incident(incident_in=incident_in)
    )


@router.put("/{incident_id}", response_model=schemas.FireIncident)
def update_fire_incident(
    *,
    incident_id: str,
    incident_in: schemas.FireIncidentUpdate,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    if incident_in.risk_zone_id is not None:
        risk_zone = fire_risk_service.get_fire_risk_zone(zone_id=incident_in.risk_zone_id)
        if not risk_zone:
            raise HTTPException(
                status_code=404,
                detail=f"Fire risk zone with ID {incident_in.risk_zone_id} not found",
            )
    incident = fire_risk_service.update_fire_incident(incident_id=incident_id, incident_in=incident_in)
    if not incident:
        raise HTTPException(status_code=404, detail="Fire incident not found")
    return schemas.FireIncident.model_validate(incident)


@router.delete("/{incident_id}", response_model=schemas.Msg)
def delete_fire_incident(
    *,
    incident_id: str,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    if fire_risk_service.delete_fire_incident(incident_id=incident_id):
        return {"msg": "Fire incident deleted successfully"}
    raise HTTPException(status_code=404, detail="Fire incident not found")
