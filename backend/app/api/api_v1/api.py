from fastapi import APIRouter

from app.api.api_v1.endpoints import users, auth, fire_risk, fire_incidents, alerts, predictions

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(fire_risk.router, prefix="/fire-risk", tags=["fire risk"])
api_router.include_router(fire_incidents.router, prefix="/fire-incidents", tags=["fire incidents"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"]) 