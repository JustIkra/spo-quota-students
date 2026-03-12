"""
API dependencies - common dependencies for endpoints.
"""
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token
from app.models import User, UserRole


# Security scheme
security = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"}
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Check if current user is admin."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_current_operator(current_user: User = Depends(get_current_user)) -> User:
    """Check if current user is operator."""
    if current_user.role != UserRole.OPERATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator access required"
        )
    if current_user.spo_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operator not assigned to any SPO"
        )
    return current_user
