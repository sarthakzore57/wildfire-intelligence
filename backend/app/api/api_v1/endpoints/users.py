from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from app import schemas
from app.api import deps
from app.services import user_service

router = APIRouter()


@router.get("/", response_model=List[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    return [schemas.User.model_validate(user) for user in user_service.get_users(skip=skip, limit=limit)]


@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(*, user_in: schemas.UserCreate) -> Any:
    if not user_service.check_db_connection():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection error. Please try again later.",
        )
    if user_service.get_user_by_email(email=user_in.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    if user_service.get_user_by_username(username=user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this username already exists.",
        )
    if user_in.alert_threshold is not None and not 0 <= user_in.alert_threshold <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Alert threshold must be between 0 and 1.",
        )

    user = user_service.create_user(user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Please try again later.",
        )
    return schemas.User.model_validate(user)


@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    user_in: schemas.UserUpdate,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    user = user_service.update_user(user_id=current_user.id, user_in=user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user. Please try again later.",
        )
    return schemas.User.model_validate(user)


@router.get("/me", response_model=schemas.User)
def read_user_me(current_user: schemas.User = Depends(deps.get_current_user)) -> Any:
    return current_user


@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: str,
    current_user: schemas.User = Depends(deps.get_current_user),
) -> Any:
    user = user_service.get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this ID does not exist in the system",
        )
    if user["id"] != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to access this user",
        )
    return schemas.User.model_validate(user)


@router.delete("/{user_id}", response_model=schemas.Msg)
def delete_user(
    user_id: str,
    current_user: schemas.User = Depends(deps.get_current_active_superuser),
) -> Any:
    user = user_service.get_user(user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this ID does not exist in the system",
        )
    if user_service.delete_user(user_id=user_id):
        return {"msg": "User deleted successfully"}
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error deleting user",
    )
