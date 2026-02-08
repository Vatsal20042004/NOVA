"""
User Service
Handles user profile management
"""

from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ConflictError
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service for user operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: int) -> User:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            NotFoundError: If user not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("User", user_id)
        
        return user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def list_users(
        self,
        page: int = 1,
        per_page: int = 20,
        role: Optional[UserRole] = None,
        active_only: bool = True
    ) -> tuple[List[User], int]:
        """
        List users with pagination.
        
        Returns:
            Tuple of (users list, total count)
        """
        query = select(User)
        count_query = select(func.count(User.id))
        
        if role:
            query = query.where(User.role == role)
            count_query = count_query.where(User.role == role)
        
        if active_only:
            query = query.where(User.is_active == True)
            count_query = count_query.where(User.is_active == True)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        users = list(result.scalars().all())
        
        return users, total
    
    async def update(self, user_id: int, data: UserUpdate) -> User:
        """
        Update user profile.
        
        Args:
            user_id: User ID
            data: Update data
            
        Returns:
            Updated user object
        """
        user = await self.get_by_id(user_id)
        
        update_data = data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            True if successful
            
        Raises:
            AuthenticationError: If current password is incorrect
        """
        from app.core.security import verify_password
        from app.core.exceptions import AuthenticationError
        
        user = await self.get_by_id(user_id)
        
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        
        return True
    
    async def deactivate(self, user_id: int) -> User:
        """Deactivate user account"""
        user = await self.get_by_id(user_id)
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def activate(self, user_id: int) -> User:
        """Activate user account"""
        user = await self.get_by_id(user_id)
        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def set_role(self, user_id: int, role: UserRole) -> User:
        """Set user role (admin only)"""
        user = await self.get_by_id(user_id)
        user.role = role
        await self.db.commit()
        await self.db.refresh(user)
        return user
