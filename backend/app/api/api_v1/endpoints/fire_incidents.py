from typing import Any, List, Optional
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps
from app.services import fire_risk_service

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[schemas.FireIncident])
def read_fire_incidents(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    region_name: Optional[str] = None,
    start_date_from: Optional[datetime] = None,
    start_date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve fire incidents with filtering options.
    """
    try:
        logger.info("Starting read_fire_incidents endpoint")
        logger.info(f"Parameters: skip={skip}, limit={limit}, region_name={region_name}, " +
                   f"start_date_from={start_date_from}, start_date_to={start_date_to}, " +
                   f"status={status}, severity={severity}")
        
        incidents = fire_risk_service.get_fire_incidents(
            db,
            skip=skip,
            limit=limit,
            region_name=region_name,
            start_date_from=start_date_from,
            start_date_to=start_date_to,
            status=status,
            severity=severity,
        )
        
        logger.info(f"Retrieved {len(incidents)} incidents")
        
        # Try without using the schema
        result = []
        for incident in incidents:
            result.append({
                "id": incident.id,
                "risk_zone_id": incident.risk_zone_id,
                "latitude": float(incident.latitude),
                "longitude": float(incident.longitude),
                "start_date": incident.start_date.isoformat() if incident.start_date else None,
                "end_date": incident.end_date.isoformat() if incident.end_date else None,
                "severity": incident.severity,
                "area_affected": float(incident.area_affected) if incident.area_affected else None,
                "status": incident.status,
                "source": incident.source,
                "description": incident.description
            })
        
        return result
    except Exception as e:
        logger.error(f"Error in read_fire_incidents: {str(e)}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/simple", response_model=List[schemas.FireIncident])
def test_fire_incidents(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    A simplified test endpoint for fire incidents without filtering.
    """
    try:
        # Log the step
        logger.info("Starting test_fire_incidents endpoint")
        
        # Get a small number of incidents
        query = db.query(models.FireIncident)
        logger.info(f"Created query: {query}")
        
        incidents = query.limit(5).all()
        logger.info(f"Retrieved {len(incidents)} incidents")
        
        # Check the data
        for i, incident in enumerate(incidents):
            logger.info(f"Incident {i+1}:")
            logger.info(f"  ID: {incident.id}")
            logger.info(f"  Risk Zone ID: {incident.risk_zone_id}")
            logger.info(f"  Location: {incident.latitude}, {incident.longitude}")
            logger.info(f"  Severity: {incident.severity}")
            logger.info(f"  Status: {incident.status}")
            logger.info(f"  Source: {incident.source}")
        
        # Try without using the schema
        result = []
        for incident in incidents:
            result.append({
                "id": incident.id,
                "risk_zone_id": incident.risk_zone_id,
                "latitude": float(incident.latitude),
                "longitude": float(incident.longitude),
                "start_date": incident.start_date.isoformat() if incident.start_date else None,
                "end_date": incident.end_date.isoformat() if incident.end_date else None,
                "severity": incident.severity,
                "area_affected": float(incident.area_affected) if incident.area_affected else None,
                "status": incident.status,
                "source": incident.source,
                "description": incident.description
            })
        
        return result
    except Exception as e:
        logger.error(f"Error in test_fire_incidents: {str(e)}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


@router.get("/{incident_id}", response_model=schemas.FireIncident)
def read_fire_incident(
    incident_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get specific fire incident by ID.
    """
    incident = db.query(models.FireIncident).filter(models.FireIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Fire incident not found",
        )
    return incident


@router.post("/", response_model=schemas.FireIncident)
def create_fire_incident(
    *,
    db: Session = Depends(deps.get_db),
    incident_in: schemas.FireIncidentCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new fire incident. Only accessible by superusers.
    """
    # Verify that the risk zone exists
    risk_zone = fire_risk_service.get_fire_risk_zone(db, zone_id=incident_in.risk_zone_id)
    if not risk_zone:
        raise HTTPException(
            status_code=404,
            detail=f"Fire risk zone with ID {incident_in.risk_zone_id} not found",
        )
    
    incident = fire_risk_service.create_fire_incident(db, incident_in=incident_in)
    return incident


@router.put("/{incident_id}", response_model=schemas.FireIncident)
def update_fire_incident(
    *,
    incident_id: int,
    db: Session = Depends(deps.get_db),
    incident_in: schemas.FireIncidentUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Update a fire incident. Only accessible by superusers.
    """
    incident = db.query(models.FireIncident).filter(models.FireIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Fire incident not found",
        )
    
    # If risk_zone_id is being updated, verify that the new risk zone exists
    if incident_in.risk_zone_id is not None and incident_in.risk_zone_id != incident.risk_zone_id:
        risk_zone = fire_risk_service.get_fire_risk_zone(db, zone_id=incident_in.risk_zone_id)
        if not risk_zone:
            raise HTTPException(
                status_code=404,
                detail=f"Fire risk zone with ID {incident_in.risk_zone_id} not found",
            )
    
    # Update the incident
    update_data = incident_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incident, field, value)
    
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


@router.delete("/{incident_id}", response_model=schemas.Msg)
def delete_fire_incident(
    *,
    incident_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Delete a fire incident. Only accessible by superusers.
    """
    incident = db.query(models.FireIncident).filter(models.FireIncident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Fire incident not found",
        )
    
    db.delete(incident)
    db.commit()
    return {"msg": "Fire incident deleted successfully"} 
