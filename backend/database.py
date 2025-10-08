from supabase import create_client, Client
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()


class Database:
    _instance: Optional[Client] = None
    
    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
            
            cls._instance = create_client(supabase_url, supabase_key)
        
        return cls._instance
