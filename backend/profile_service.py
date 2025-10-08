from typing import Optional, Dict, Any
from .database import Database
from .models import ProfileData
from datetime import datetime


class ProfileService:
    
    @staticmethod
    def create_profile(user_id: str, profile_data: ProfileData) -> Dict[str, Any]:
        supabase = Database.get_client()
        
        data = {
            "user_id": user_id,
            "profile_data": profile_data.model_dump(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("profiles").insert(data).execute()
        
        if not result.data:
            raise Exception("Failed to create profile")
        
        return result.data[0]
    
    @staticmethod
    def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
        supabase = Database.get_client()
        
        result = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        
        if not result.data:
            return None
        
        return result.data[0]
    
    @staticmethod
    def update_profile(user_id: str, profile_data: ProfileData) -> Dict[str, Any]:
        supabase = Database.get_client()
        
        data = {
            "profile_data": profile_data.model_dump(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("profiles").update(data).eq("user_id", user_id).execute()
        
        if not result.data:
            raise Exception("Failed to update profile")
        
        return result.data[0]
    
    @staticmethod
    def delete_profile(user_id: str) -> bool:
        supabase = Database.get_client()
        
        result = supabase.table("profiles").delete().eq("user_id", user_id).execute()
        
        return bool(result.data)
    
    @staticmethod
    def upsert_profile(user_id: str, profile_data: ProfileData) -> Dict[str, Any]:
        existing = ProfileService.get_profile(user_id)
        
        if existing:
            return ProfileService.update_profile(user_id, profile_data)
        else:
            return ProfileService.create_profile(user_id, profile_data)
