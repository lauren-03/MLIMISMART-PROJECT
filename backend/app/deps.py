"""Shared FastAPI dependencies for authentication and authorisation."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Farmer, Role
from .security import decode_access_token

bearer = HTTPBearer(auto_error=False)


def get_current_farmer(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> Farmer:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )
    farmer = db.get(Farmer, int(payload["sub"]))
    if farmer is None or not farmer.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Account not found or disabled")
    return farmer


def get_current_admin(farmer: Farmer = Depends(get_current_farmer)) -> Farmer:
    if farmer.role != Role.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Administrator access required")
    return farmer
