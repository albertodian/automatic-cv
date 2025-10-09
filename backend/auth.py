from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
from .database import Database
from .token_service import TokenService

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided"
        )

    token = credentials.credentials
    
    supabase = Database.get_client()

    try:
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        try:
            balance = TokenService.get_balance(user.user.id)
        except Exception:
            balance = {"token": 0, "updated_at": None}

        return {
            "id": user.user.id,
            "email": user.user.email,
            "created_at": user.user.created_at,
            "token": balance.get("token", 0),
            "token_updated_at": balance.get("updated_at")
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[Dict[str, Any]]:
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
