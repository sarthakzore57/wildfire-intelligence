from typing import Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.Alert])
def read_alerts(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = None,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve alerts for the current user.
    """
    query = db.query(models.Alert).filter(models.Alert.user_id == current_user.id)
    
    if is_read is not None:
        query = query.filter(models.Alert.is_read == is_read)
    
    # Order by alert_time descending to get latest alerts first
    query = query.order_by(models.Alert.alert_time.desc())
    
    alerts = query.offset(skip).limit(limit).all()
    return alerts


@router.get("/{alert_id}", response_model=schemas.Alert)
def read_alert(
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get a specific alert by ID.
    """
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )
    
    return alert


@router.put("/{alert_id}", response_model=schemas.Alert)
def update_alert(
    *,
    alert_id: int,
    db: Session = Depends(deps.get_db),
    alert_in: schemas.AlertUpdate,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Update an alert (e.g., mark as read).
    """
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )
    
    update_data = alert_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(alert, field, value)
    
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/{alert_id}", response_model=schemas.Msg)
def delete_alert(
    *,
    alert_id: int,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Delete an alert.
    """
    alert = db.query(models.Alert).filter(
        models.Alert.id == alert_id,
        models.Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )
    
    db.delete(alert)
    db.commit()
    return {"msg": "Alert deleted successfully"}


@router.post("/mark-all-read", response_model=schemas.Msg)
def mark_all_alerts_read(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Mark all alerts as read for the current user.
    """
    db.query(models.Alert).filter(
        models.Alert.user_id == current_user.id,
        models.Alert.is_read == False
    ).update({"is_read": True})
    
    db.commit()
    return {"msg": "All alerts marked as read"} 
