"""
Authentication API endpoints.
"""
from collections import defaultdict
from time import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models import User
from app.schemas import UserLogin, TokenResponse, CurrentUser
from app.services import authenticate_user
from app.core.security import create_access_token


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# In-memory rate limiter for login endpoint
_login_attempts: dict[str, list[float]] = defaultdict(list)
_MAX_LOGIN_ATTEMPTS = 5
_LOGIN_WINDOW_SECONDS = 60


def _check_login_rate_limit(ip: str) -> None:
    """
    Check if the IP has exceeded the login rate limit.
    Raises HTTPException 429 if too many attempts.
    """
    now = time()
    # Clean up old attempts outside the window
    _login_attempts[ip] = [
        t for t in _login_attempts[ip] if now - t < _LOGIN_WINDOW_SECONDS
    ]
    if len(_login_attempts[ip]) >= _MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    _login_attempts[ip].append(now)


@router.post("/login", response_model=TokenResponse)
def login(user_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token.
    Rate limited to 5 attempts per minute per IP.
    """
    # Get client IP (check X-Forwarded-For header for proxy setups)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host)
    if client_ip and "," in client_ip:
        # Take the first IP if multiple are present
        client_ip = client_ip.split(",")[0].strip()

    _check_login_rate_limit(client_ip)

    user = authenticate_user(db, user_data.login, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=access_token)


@router.get("/me", response_model=CurrentUser)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    """
    spo_name = None
    if current_user.spo:
        spo_name = current_user.spo.name

    return CurrentUser(
        id=current_user.id,
        login=current_user.login,
        role=current_user.role,
        spo_id=current_user.spo_id,
        spo_name=spo_name
    )
