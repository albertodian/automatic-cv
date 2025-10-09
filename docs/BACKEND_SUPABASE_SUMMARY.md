# Backend + Supabase Integration Summary

## Overview
- **Framework**: FastAPI (served from `app/app.py`) exposes the public API.
- **Auth & Storage**: Supabase handles authentication and persistence through thin service layers in `/backend`.
- **Profiles**: User CV data lives in the `profiles` table and is managed via `ProfileService`.
- **Tokens**: Monetisation lever uses a `user_tokens` table with the new `TokenService` for balance management.

## Environment
1. Install dependencies (includes Supabase Python SDK):
   ```bash
   pip install -r requirements.txt
   ```
2. Provide Supabase credentials in `.env` at the project root:
   ```env
   SUPABASE_URL=...supabase.co
   SUPABASE_KEY=... (anon/public key)
   ```

## Database Schema
Run the SQL block inside the Supabase SQL editor (it creates all required tables, indexes, and policies).

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own profile"   ON profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own profile" ON profiles FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users delete own profile" ON profiles FOR DELETE USING (auth.uid() = user_id);
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

CREATE TABLE IF NOT EXISTS user_tokens (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    token INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE user_tokens ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users view own tokens"   ON user_tokens FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert own tokens" ON user_tokens FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update own tokens" ON user_tokens FOR UPDATE USING (auth.uid() = user_id);
CREATE INDEX IF NOT EXISTS idx_user_tokens_user_id ON user_tokens(user_id);

CREATE OR REPLACE FUNCTION public.update_user_tokens_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_user_tokens_updated_at ON user_tokens;
CREATE TRIGGER trg_user_tokens_updated_at
BEFORE UPDATE ON user_tokens
FOR EACH ROW
EXECUTE FUNCTION public.update_user_tokens_updated_at();
```

## Python Service Layer
- `backend/database.py`: lazy Supabase client loader.
- `backend/auth.py`: FastAPI dependency that verifies bearer tokens and enriches the user context with the latest token balance.
- `backend/profile_service.py`: CRUD helpers for `profiles` (UTC timestamps for auditability).
- `backend/token_service.py`: New helper providing `initialize_balance`, `get_balance`, and `add_tokens` to manage `user_tokens` rows safely.

## Pydantic Models (`backend/models.py`)
- `AuthResponse` now reports the `token` balance alongside auth tokens.
- `TokenBalance` / `AddTokensRequest` drive the new token endpoints.
- Profile-related models remain unchanged and power both public and authenticated CV flows.

## API Surface (`backend/routes.py`)
All endpoints live under `/api/v1` via the router included inside `app/app.py`.

### Auth
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/signup` | Creates a Supabase auth user, initializes `user_tokens` (0 balance), returns tokens + token balance. |
| `POST` | `/auth/signin` | Authenticates via Supabase password flow and returns session tokens + current balance. |
| `POST` | `/auth/signout` | Revokes current Supabase session. |

### Profile
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/profile` | Fetch the caller's stored CV. |
| `POST` | `/profile` | Insert-or-update (upsert) a CV document. |
| `PUT` | `/profile` | Update the CV document. |
| `DELETE` | `/profile` | Remove the stored CV. |

### Tokens
| Method | Path | Body | Description |
|--------|------|------|-------------|
| `GET` | `/tokens` | — | Retrieve the caller's token balance. |
| `POST` | `/tokens/add` | `{ "amount": int > 0 }` | Increase the balance (used after a purchase). |
| `POST` | `/tokens/deduct` | `{ "amount": int > 0 }` | Decrease the balance (consume tokens for services). |

All protected endpoints rely on the `get_current_user` dependency, which now injects `{"id", "email", "token", "token_updated_at"}` into the request scope.

## Typical Flow
1. **Sign up** → Auth user is created, `user_tokens` row is seeded at 0 via `TokenService.initialize_balance`.
2. **Sign in** → Returns Supabase access/refresh tokens and current `token` balance.
3. **Purchase** → Call `POST /api/v1/tokens/add` with the number of purchased tokens; balance is atomically incremented in Supabase.
4. **Spend tokens** → Call `POST /api/v1/tokens/deduct` when the user consumes the service; responses include the updated balance for downstream logic.

## Local Testing
- Start the API: `cd app && python app.py`
- Visit `http://localhost:8000/docs` to try the new endpoints.
- Token routes appear under the **Tokens** tag once authentication succeeds.

## Next Extensions
- Implement token deduction & transaction history (new table) for full billing visibility.
- Add async job to reconcile token purchases from payment provider webhooks.
- Expand automated tests with mocked Supabase client for token workflows.

This document is the canonical reference for the backend + Supabase integration moving forward.
