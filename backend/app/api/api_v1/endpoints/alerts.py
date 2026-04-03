from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app import schemas
from app.api import deps
from app.services import fire_risk_service

router = APIRouter()


@router.get("/", response_model=List[schemas.Alert])
def read_alerts(
    skip: int = 0,
    limit: int = 100,
    is_read: Optional[bool] = None,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    alerts = fire_risk_service.get_alerts_by_user(
        user_id=current_user.id, skip=skip, limit=limit, is_read=is_read
    )
    return [schemas.Alert.model_validate(alert) for alert in alerts]


@router.get("/{alert_id}", response_model=schemas.Alert)
def read_alert(
    alert_id: str,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    alert = fire_risk_service.get_alert(alert_id)
    if not alert or alert["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    return schemas.Alert.model_validate(alert)


@router.put("/{alert_id}", response_model=schemas.Alert)
def update_alert(
    *,
    alert_id: str,
    alert_in: schemas.AlertUpdate,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    alert = fire_risk_service.get_alert(alert_id)
    if not alert or alert["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    updated = fire_risk_service.update_alert(alert_id=alert_id, alert_in=alert_in)
    return schemas.Alert.model_validate(updated)


@router.delete("/{alert_id}", response_model=schemas.Msg)
def delete_alert(
    *,
    alert_id: str,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    alert = fire_risk_service.get_alert(alert_id)
    if not alert or alert["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="Alert not found")
    fire_risk_service.delete_alert(alert_id=alert_id)
    return {"msg": "Alert deleted successfully"}


@router.post("/mark-all-read", response_model=schemas.Msg)
def mark_all_alerts_read(
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    fire_risk_service.mark_all_alerts_read(user_id=current_user.id)
    return {"msg": "All alerts marked as read"}
