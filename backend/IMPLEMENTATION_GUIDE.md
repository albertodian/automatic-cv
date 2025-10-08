# Step-by-Step Implementation Guide

## 🎯 Goal
Integrate Supabase authentication and profile storage with your existing CV generation API while maintaining backward compatibility.

---

## ✅ Step 1: Set Up Supabase (15 minutes)

### 1.1 Create Supabase Project

1. Go to https://supabase.com
2. Click **"New Project"**
3. Fill in:
   - **Name**: `cv-generator`
   - **Database Password**: (Generate strong password and SAVE IT!)
   - **Region**: Choose closest to your location
4. Click **"Create new project"**
5. Wait 2-3 minutes for provisioning

### 1.2 Create Database Table

1. In Supabase dashboard, click **"SQL Editor"** (left sidebar)
2. Click **"New query"**
3. Copy and paste this SQL:

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

4. Click **"Run"** (bottom right)
5. You should see "Success. No rows returned"

### 1.3 Get API Credentials

1. Click **"Project Settings"** (gear icon, bottom left)
2. Click **"API"** in the left menu
3. Copy these values (you'll need them soon):
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGc...` (long string)

### 1.4 Enable Email Authentication

1. Click **"Authentication"** in left sidebar
2. Click **"Providers"**
3. Make sure **"Email"** is enabled (should be by default)
4. (Optional) Configure email templates under "Email Templates"

**✅ Checkpoint**: You now have a Supabase project with a profiles table!

---

## ✅ Step 2: Install Dependencies (2 minutes)

### 2.1 Add to requirements.txt

Open `requirements.txt` and add:

```txt
supabase==2.3.0
```

### 2.2 Install

```bash
pip install supabase
```

**✅ Checkpoint**: Supabase Python client installed!

---

## ✅ Step 3: Configure Environment (2 minutes)

### 3.1 Update .env file

Open (or create) `.env` in your project root and add:

```env
# Existing variables
REPLICATE_API_TOKEN=your_existing_token

# New Supabase variables
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGc...your_anon_key...
```

Replace with the values you copied from Step 1.3

### 3.2 Verify .env is in .gitignore

Make sure `.env` is listed in `.gitignore` (it should be already)

**✅ Checkpoint**: Environment configured!

---

## ✅ Step 4: Update Railway Environment (2 minutes)

Since you deploy on Railway:

1. Go to your Railway project
2. Click on your service
3. Click **"Variables"** tab
4. Add these two variables:
   - `SUPABASE_URL`: `https://xxxxx.supabase.co`
   - `SUPABASE_KEY`: `eyJhbGc...`
5. Click **"Deploy"** (Railway will redeploy automatically)

**✅ Checkpoint**: Production environment configured!

---

## ✅ Step 5: Integrate Backend Routes (5 minutes)

The modified app.py (see below) already includes:
- Backend routes integration
- Flexible authentication (optional user)
- Profile loading from database

Just replace your `app/app.py` with the updated version.

**✅ Checkpoint**: Backend integrated!

---

## ✅ Step 6: Test the Integration (10 minutes)

### 6.1 Start your server

```bash
cd app
python app.py
```

Server should start on http://localhost:8000

### 6.2 Test Authentication

**Sign Up**:
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

You should get back:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": "uuid",
    "email": "test@example.com",
    ...
  }
}
```

**Save the access_token** - you'll need it!

### 6.3 Test Profile Creation

```bash
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "personal_info": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890"
    },
    "summary": "Experienced software engineer",
    "education": [{
      "degree": "BSc Computer Science",
      "institution": "University",
      "location": "City",
      "year": "2020"
    }],
    "experience": [{
      "title": "Software Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "years": "2020-2024"
    }],
    "projects": [{
      "name": "Cool Project",
      "role": "Developer",
      "year": "2023",
      "description": "Built something cool"
    }],
    "skills": ["Python", "FastAPI", "Docker"]
  }'
```

You should get back the created profile with ID.

### 6.4 Test Profile Retrieval

```bash
curl http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
```

You should get back your profile.

### 6.5 Test CV Generation (Authenticated)

```bash
curl -X POST http://localhost:8000/api/cv/generate-authenticated \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -d '{
    "job_description": "Software Engineer position requiring Python and FastAPI",
    "template": "tech",
    "model_name": "openai/gpt-4.1-mini"
  }'
```

This will:
1. Load your profile from database
2. Generate optimized CV
3. Return the result

### 6.6 Test CV Generation (Unauthenticated - Backward Compatible)

```bash
curl -X POST http://localhost:8000/api/cv/generate \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "personal_info": {...},
      "summary": "...",
      ...
    },
    "job_description": "...",
    "template": "tech"
  }'
```

This still works without authentication (backward compatible)!

**✅ Checkpoint**: Everything works!

---

## ✅ Step 7: Check Supabase Dashboard (2 minutes)

1. Go back to Supabase dashboard
2. Click **"Table Editor"** (left sidebar)
3. Click **"profiles"** table
4. You should see your test profile with all data in `profile_data` column

**✅ Checkpoint**: Data is being saved!

---

## 📊 What You Now Have

### New Authenticated Endpoints

1. **POST /api/v1/auth/signup** - Create account
2. **POST /api/v1/auth/signin** - Login
3. **POST /api/v1/auth/signout** - Logout
4. **GET /api/v1/profile** - Get user profile
5. **POST /api/v1/profile** - Create/update profile
6. **DELETE /api/v1/profile** - Delete profile

### Enhanced CV Generation Endpoints

1. **POST /api/cv/generate-authenticated** - Generate CV using profile from DB
2. **POST /api/cv/generate-from-file-authenticated** - Generate CV from file (for users)
3. All original endpoints still work (backward compatible)

### How It Works

**For Authenticated Users**:
```
1. User signs up/in → Gets JWT token
2. User creates profile → Saved to Supabase
3. User generates CV → Profile loaded from DB automatically
4. CV generated → Returned as JSON or PDF
```

**For Unauthenticated Users** (backward compatible):
```
1. User calls /api/cv/generate with profile in request body
2. CV generated → Returned as JSON or PDF
3. Nothing saved
```

---

## 🎯 Next Steps - Frontend Integration

### If you have a frontend:

**Sign Up**:
```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/signup', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { access_token } = await response.json();
localStorage.setItem('token', access_token);
```

**Create Profile**:
```javascript
await fetch('http://localhost:8000/api/v1/profile', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({
    personal_info: { name: 'John Doe', ... },
    summary: '...',
    ...
  })
});
```

**Generate CV**:
```javascript
const response = await fetch('http://localhost:8000/api/cv/generate-authenticated', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({
    job_description: '...',
    template: 'tech'
  })
});

const result = await response.json();
console.log(result.profile); // Optimized CV
```

---

## 🔧 Troubleshooting

### "Module not found: supabase"
```bash
pip install supabase
```

### "SUPABASE_URL not set"
Check your `.env` file has the correct values

### "Invalid authentication token"
Token expired (1 hour). User needs to sign in again.

### "Profile not found"
User hasn't created profile yet. They need to call POST /api/v1/profile first.

### Railway deployment fails
Make sure you added SUPABASE_URL and SUPABASE_KEY to Railway environment variables.

---

## 📈 Usage Patterns

### Pattern 1: SaaS Product (Recommended)
- Users sign up
- Users create profile once
- Users generate CVs multiple times (profile from DB)
- No need to send profile every time

### Pattern 2: API Service (Backward Compatible)
- No authentication required
- Users send profile with each request
- No data persistence
- Good for testing or one-off uses

### Pattern 3: Hybrid (Flexible)
- Authenticated users: profile from DB
- Guest users: profile in request
- Best of both worlds

---

## 🎉 You're Done!

You now have:
- ✅ User authentication
- ✅ Profile storage in Supabase
- ✅ Flexible CV generation (with/without auth)
- ✅ Backward compatibility
- ✅ Production-ready security
- ✅ Free tier hosting (Supabase + Railway)

**Total setup time: ~30 minutes**

Visit http://localhost:8000/docs to see all endpoints in interactive documentation!

---

## 📚 Additional Resources

- Supabase Docs: https://supabase.com/docs
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- Your API Docs: http://localhost:8000/docs

---

**Questions? Check the troubleshooting section or review the code comments!**
