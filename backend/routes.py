from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from .auth import get_current_user
from .models import (
    SignUpRequest,
    SignInRequest,
    AuthResponse,
    ProfileData,
    AddTokensRequest,
    TokenBalance,
    DeductTokensRequest,
)
from .profile_service import ProfileService
from .database import Database
from .token_service import TokenService

router = APIRouter()


@router.post("/auth/signup", response_model=AuthResponse, tags=["Authentication"])
async def sign_up(request: SignUpRequest):
    supabase = Database.get_client()
    
    try:
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )

        balance = TokenService.initialize_balance(response.user.id)
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at
            },
            token=balance["token"],
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/auth/signin", response_model=AuthResponse, tags=["Authentication"])
async def sign_in(request: SignInRequest):
    supabase = Database.get_client()
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        balance = TokenService.get_balance(response.user.id)
        
        return AuthResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user={
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at
            },
            token=balance["token"],
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/auth/signout", tags=["Authentication"])
async def sign_out(current_user: Dict[str, Any] = Depends(get_current_user)):
    supabase = Database.get_client()
    
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully signed out"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/profile", tags=["Profile"])
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    profile = ProfileService.get_profile(current_user["id"])
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return profile


@router.post("/profile", tags=["Profile"])
async def create_or_update_profile(
    profile_data: ProfileData,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    profile = ProfileService.upsert_profile(current_user["id"], profile_data)
    return profile


@router.put("/profile", tags=["Profile"])
async def update_profile(
    profile_data: ProfileData,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    profile = ProfileService.update_profile(current_user["id"], profile_data)
    return profile


@router.delete("/profile", tags=["Profile"])
async def delete_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    success = ProfileService.delete_profile(current_user["id"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    return {"message": "Profile deleted successfully"}


@router.get("/tokens", response_model=TokenBalance, tags=["Tokens"])
async def get_tokens(current_user: Dict[str, Any] = Depends(get_current_user)):
    balance = TokenService.get_balance(current_user["id"])
    return balance


@router.post("/tokens/add", response_model=TokenBalance, tags=["Tokens"])
async def add_tokens(
    request: AddTokensRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    balance = TokenService.add_tokens(current_user["id"], request.amount)
    return balance


@router.post("/tokens/deduct", response_model=TokenBalance, tags=["Tokens"])
async def deduct_tokens(
    request: DeductTokensRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        balance = TokenService.deduct_tokens(current_user["id"], request.amount)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    return balance
