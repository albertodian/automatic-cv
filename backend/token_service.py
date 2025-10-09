from __future__ import annotations

from typing import Dict, Any
from datetime import datetime, timezone

from .database import Database


class TokenService:
    """Service layer for managing user tokens stored in Supabase."""

    _TABLE_NAME = "user_tokens"

    @classmethod
    def _table(cls):
        supabase = Database.get_client()
        return supabase.table(cls._TABLE_NAME)

    @classmethod
    def initialize_balance(cls, user_id: str) -> Dict[str, Any]:
        """Ensure a token balance row exists for the user."""
        existing = cls._table().select("token", "updated_at").eq("user_id", user_id).limit(1).execute()
        if existing.data:
            return cls._normalize(existing.data[0])

        result = cls._table().insert({
            "user_id": user_id,
            "token": 0,
        }).execute()

        if not result.data:
            raise RuntimeError("Failed to initialize token balance")

        return cls._normalize(result.data[0])

    @classmethod
    def get_balance(cls, user_id: str) -> Dict[str, Any]:
        """Return the current token balance for the user."""
        result = cls._table().select("token", "updated_at").eq("user_id", user_id).limit(1).execute()
        if result.data:
            return cls._normalize(result.data[0])

        return cls.initialize_balance(user_id)

    @classmethod
    def add_tokens(cls, user_id: str, amount: int) -> Dict[str, Any]:
        """Increment the token balance by the requested amount."""
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        current = cls.get_balance(user_id)
        new_total = current["token"] + amount

        result = cls._table().update({
            "token": new_total,
            "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        }).eq("user_id", user_id).execute()

        if not result.data:
            raise RuntimeError("Failed to update token balance")

        return cls._normalize(result.data[0])

    @classmethod
    def deduct_tokens(cls, user_id: str, amount: int) -> Dict[str, Any]:
        """Decrease the token balance by the requested amount."""
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")

        current = cls.get_balance(user_id)
        if current["token"] < amount:
            raise ValueError("Insufficient token balance")

        new_total = current["token"] - amount

        result = cls._table().update({
            "token": new_total,
            "updated_at": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
        }).eq("user_id", user_id).execute()

        if not result.data:
            raise RuntimeError("Failed to update token balance")

        return cls._normalize(result.data[0])

    @staticmethod
    def _normalize(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure consistent typing from Supabase responses."""
        token_value = payload.get("token", 0)
        try:
            token_int = int(token_value)
        except (TypeError, ValueError):
            token_int = 0

        updated_at_raw = payload.get("updated_at")
        updated_at_value = None

        if isinstance(updated_at_raw, datetime):
            updated_at_value = updated_at_raw
        elif isinstance(updated_at_raw, str):
            try:
                updated_at_value = datetime.fromisoformat(updated_at_raw.replace("Z", "+00:00"))
            except ValueError:
                updated_at_value = None

        normalized = {
            "token": token_int,
            "updated_at": updated_at_value,
        }
        return normalized
