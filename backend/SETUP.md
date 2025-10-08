# Backend Setup Guide - Supabase Authentication & Profile Storage

## Overview

This backend implementation provides:
- **User Authentication** via Supabase Auth (JWT-based)
- **Profile Storage** - One baseline CV profile per user
- **Clean Architecture** - Service layer, models, routes separation
- **Secure** - Token-based auth, user isolation

---

## Architecture

```
backend/
├── __init__.py              # Package initialization
├── database.py              # Supabase client singleton
├── auth.py                  # Authentication dependencies
├── models.py                # Pydantic models
├── profile_service.py       # Profile CRUD operations
├── routes.py                # API endpoints
└── SETUP.md                 # This file
```

---

## Supabase Setup

### 1. Create Supabase Project

1. Go to https://supabase.com
2. Click "New Project"
3. Name: `cv-generator`
4. Database Password: (save this!)
5. Region: Choose closest to you
6. Click "Create project"

### 2. Create Database Table

Go to SQL Editor and run:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create profiles table
CREATE TABLE profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only read their own profile
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Users can insert their own profile
CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own profile
CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Users can delete their own profile
CREATE POLICY "Users can delete own profile"
    ON profiles FOR DELETE
    USING (auth.uid() = user_id);

-- Create index for faster lookups
CREATE INDEX idx_profiles_user_id ON profiles(user_id);
```

### 3. Get API Keys

1. Go to Project Settings → API
2. Copy:
   - `Project URL` (SUPABASE_URL)
   - `anon public` key (SUPABASE_KEY)

### 4. Configure Authentication

1. Go to Authentication → Providers
2. Enable "Email" provider
3. (Optional) Enable Google, GitHub, etc.
4. Configure email templates (optional)

---

## Environment Configuration

Add to your `.env` file:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-public-key
```

---

## Dependencies

Add to `requirements.txt`:

```txt
supabase==2.3.0
```

Install:

```bash
pip install supabase
```

---

## Integration with Existing App

Update `app/app.py`:

```python
from backend.routes import router as backend_router

# Add backend routes
app.include_router(backend_router, prefix="/api/v1")
```

---

## API Endpoints

### Authentication

**Sign Up**
```http
POST /api/v1/auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123"
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2025-10-08T..."
  }
}
```

**Sign In**
```http
POST /api/v1/auth/signin
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password123"
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {...}
}
```

**Sign Out**
```http
POST /api/v1/auth/signout
Authorization: Bearer <access_token>

Response: 200 OK
{
  "message": "Successfully signed out"
}
```

### Profile Management

**Get Profile**
```http
GET /api/v1/profile
Authorization: Bearer <access_token>

Response: 200 OK
{
  "id": "uuid",
  "user_id": "uuid",
  "profile_data": {
    "personal_info": {...},
    "summary": "...",
    "education": [...],
    "experience": [...],
    "projects": [...],
    "skills": [...]
  },
  "created_at": "2025-10-08T...",
  "updated_at": "2025-10-08T..."
}
```

**Create/Update Profile**
```http
POST /api/v1/profile
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "personal_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  },
  "summary": "Experienced software engineer...",
  "education": [...],
  "experience": [...],
  "projects": [...],
  "skills": ["Python", "FastAPI", "Docker"]
}

Response: 200 OK
{
  "id": "uuid",
  "user_id": "uuid",
  "profile_data": {...},
  "created_at": "...",
  "updated_at": "..."
}
```

**Delete Profile**
```http
DELETE /api/v1/profile
Authorization: Bearer <access_token>

Response: 200 OK
{
  "message": "Profile deleted successfully"
}
```

---

## Usage Flow

### New User Flow

1. User signs up → Gets access token
2. User creates profile → Stored in Supabase
3. User generates CV → Uses profile from DB
4. CV generated → Not stored (streamed to user)
5. User updates profile → Updated in DB

### Returning User Flow

1. User signs in → Gets access token
2. User requests CV generation → Profile loaded from DB
3. CV generated → Streamed to user

---

## Security Features

### JWT Tokens
- **Access tokens** expire in 1 hour
- **Refresh tokens** expire in 7 days
- Tokens signed by Supabase (secure secret)

### Row Level Security (RLS)
- Users can only access their own data
- Enforced at database level
- Cannot be bypassed via API

### Password Requirements
- Minimum 8 characters
- Hashed with bcrypt by Supabase
- Never stored in plain text

### HTTPS Only
- Railway enforces HTTPS
- Tokens transmitted securely

---

## Data Model

### User (Managed by Supabase Auth)
```
auth.users
- id: UUID (primary key)
- email: string
- encrypted_password: string
- created_at: timestamp
- updated_at: timestamp
```

### Profile (Your Table)
```
profiles
- id: UUID (primary key)
- user_id: UUID (foreign key → auth.users)
- profile_data: JSONB (entire CV profile)
- created_at: timestamp
- updated_at: timestamp
```

**One profile per user** - Enforced by UNIQUE constraint on user_id

---

## Updating Existing CV Generation Endpoints

### Before (No Auth)
```python
@app.post("/api/cv/generate")
async def generate_cv(request: GenerateCVRequest):
    profile_dict = request.profile.model_dump()
    # ... generate CV
```

### After (With Auth)
```python
@app.post("/api/cv/generate")
async def generate_cv(
    request: GenerateCVRequest,
    current_user: Dict = Depends(get_current_user)
):
    # Load profile from database
    profile = ProfileService.get_profile(current_user["id"])
    
    if not profile:
        raise HTTPException(404, "Profile not found. Create profile first.")
    
    profile_dict = profile["profile_data"]
    # ... generate CV
```

Or keep it flexible:
```python
@app.post("/api/cv/generate")
async def generate_cv(
    job_description: str,
    current_user: Dict = Depends(get_current_user),
    custom_profile: Optional[ProfileData] = None
):
    # Use custom profile if provided, otherwise load from DB
    if custom_profile:
        profile_dict = custom_profile.model_dump()
    else:
        profile = ProfileService.get_profile(current_user["id"])
        if not profile:
            raise HTTPException(404, "No profile found")
        profile_dict = profile["profile_data"]
    
    # ... generate CV
```

---

## Testing

### Manual Testing

1. Sign up a user
2. Create profile
3. Get profile
4. Update profile
5. Generate CV (using profile from DB)
6. Delete profile
7. Sign out

### cURL Examples

```bash
# Sign up
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Save the access_token from response

# Create profile
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d @profile.json

# Get profile
curl http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Cost Estimation

### Supabase Free Tier
- **500MB database** - Enough for ~5,000 profiles
- **50,000 monthly active users**
- **2GB bandwidth**
- **Unlimited API requests**
- **Email auth included**

**Free for small-scale production!**

### Paid Tier ($25/month)
- **8GB database** - ~80,000 profiles
- **100,000 monthly active users**
- **250GB bandwidth**
- **Automatic backups**
- **Priority support**

---

## Migration Path

### Phase 1: Add Backend (This Week)
- ✅ Set up Supabase project
- ✅ Create profiles table
- ✅ Add authentication endpoints
- ✅ Add profile CRUD endpoints

### Phase 2: Integrate with CV Generation (Next Week)
- Update CV generation to load from DB
- Keep backward compatibility (optional profile in request)
- Test end-to-end flow

### Phase 3: Optional Features (Later)
- Email verification
- Password reset
- Profile versioning (keep history)
- Multiple profiles per user

---

## Troubleshooting

### "Invalid authentication token"
- Token expired (1 hour lifetime)
- Use refresh token to get new access token
- Re-authenticate user

### "Failed to create profile"
- Check if profile already exists (one per user)
- Use PUT or POST (upsert) instead

### "Profile not found"
- User hasn't created profile yet
- Prompt user to create profile first

### Database connection issues
- Check SUPABASE_URL and SUPABASE_KEY in .env
- Verify Supabase project is active
- Check internet connection

---

## Next Steps

1. **Set up Supabase project** (10 minutes)
2. **Create profiles table** (5 minutes)
3. **Add backend routes to app** (5 minutes)
4. **Test authentication** (10 minutes)
5. **Test profile CRUD** (10 minutes)
6. **Update CV generation** (20 minutes)

**Total: ~1 hour to production-ready backend!**

---

## Support

- Supabase Docs: https://supabase.com/docs
- Supabase Auth: https://supabase.com/docs/guides/auth
- Supabase Python: https://supabase.com/docs/reference/python

---

**Ready to implement? Start with Supabase project creation!** 🚀
