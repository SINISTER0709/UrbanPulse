from typing import Annotated, Sequence
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.enums import UserRole

# HTTP Bearer scheme for JWT header: Authorization: Bearer <token>
security_scheme = HTTPBearer(auto_error=True)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Extracts Bearer token, validates signature/expiration, and loads the active user.
    """
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )

    return user


def require_role(allowed_roles: Sequence[UserRole]):
    """
    Role-Based Access Control (RBAC) dependency factory.
    Enforces user role membership against allowed_roles (Citizen, Admin, Department).
    """
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        user_role_str = str(current_user.role.value if hasattr(current_user.role, "value") else current_user.role)
        allowed_str = [r.value if hasattr(r, "value") else str(r) for r in allowed_roles]
        
        if user_role_str not in allowed_str:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required role: one of {allowed_str}. Current role: {user_role_str}",
            )
        return current_user

    return role_checker


# Convenient RBAC role guards
require_citizen = require_role([UserRole.Citizen, UserRole.Admin])
require_admin = require_role([UserRole.Admin])
require_department = require_role([UserRole.Department, UserRole.Admin])
