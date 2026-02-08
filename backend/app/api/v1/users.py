"""
User API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.exceptions import NotFoundError
from app.services.user import UserService
from app.schemas.user import UserResponse, UserUpdate
from app.api.deps import get_current_active_user
from app.models.user import User


router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile.
    """
    user_service = UserService(db)
    
    updated_user = await user_service.update(current_user.id, data)
    return updated_user


@router.post("/me/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password.
    """
    from app.core.exceptions import AuthenticationError
    
    user_service = UserService(db)
    
    try:
        await user_service.change_password(
            current_user.id,
            current_password,
            new_password
        )
        return {"message": "Password changed successfully"}
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID.
    
    Regular users can only view their own profile.
    Admins can view any profile.
    """
    from app.models.user import UserRole
    
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' profiles"
        )
    
    user_service = UserService(db)
    
    try:
        user = await user_service.get_by_id(user_id)
        return user
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
