# 🎯 START HERE - Your Action Plan

## Where You Are Now ✅

- ✅ Backend skeleton created in `/backend/` folder
- ✅ `app.py` updated with authentication support
- ✅ Documentation ready
- ⏳ Need to set up Supabase and test

---

## What to Do RIGHT NOW 🚀

### Step 1: Install Supabase (30 seconds)

Open terminal in your project folder:

```bash
pip install supabase
```

### Step 2: Create Supabase Account (2 minutes)

1. Go to https://supabase.com
2. Click "Start your project"
3. Sign up with GitHub or email

### Step 3: Create Project (3 minutes)

1. Click "New Project"
2. Fill in:
   - Name: `cv-generator`
   - Database Password: (generate and SAVE IT!)
   - Region: (choose closest to you)
3. Click "Create new project"
4. Wait 2 minutes for setup

### Step 4: Create Database Table (2 minutes)

1. In Supabase dashboard, click "SQL Editor" (left sidebar)
2. Click "New query"
3. Copy ALL of this:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL UNIQUE,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own profile" ON profiles FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can insert own profile" ON profiles FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own profile" ON profiles FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own profile" ON profiles FOR DELETE USING (auth.uid() = user_id);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);
```

4. Click "Run" button
5. Should say "Success"

### Step 5: Get API Keys (1 minute)

1. Click "Project Settings" (gear icon, bottom left)
2. Click "API" in menu
3. Copy BOTH:
   - **URL**: `https://xxxxx.supabase.co`
   - **anon public key**: Long string starting with `eyJ`

### Step 6: Add to .env File (1 minute)

Open `.env` file in project root and add:

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUz...
```

(Replace with YOUR values from Step 5)

### Step 7: Test It! (5 minutes)

Start server:
```bash
cd app
python app.py
```

Open browser: http://localhost:8000/docs

You should see new sections:
- **Backend** (auth endpoints)
- **CV Generation (Authenticated)**

### Step 8: Test Sign Up

In terminal:
```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

Should return:
```json
{
  "access_token": "eyJ...",
  "user": {...}
}
```

---

## ✅ Done! What Now?

You have a working authentication system!

### Next Actions:

1. **Test profile creation** - See QUICK_START.md Step 4.3
2. **Test CV generation** - See QUICK_START.md Step 4.4
3. **Deploy to Railway** - Add env vars to Railway
4. **Build frontend** (optional) - Use authentication flow

---

## 📚 Documentation Guide

**Choose based on what you need:**

| File | When to Use |
|------|-------------|
| **README.md** (this file) | Right now - follow steps above |
| **QUICK_START.md** | Detailed testing guide |
| **IMPLEMENTATION_GUIDE.md** | Complete explanation |
| **CHANGES.md** | See what changed |
| **SETUP.md** | Technical reference |

---

## 🆘 Quick Troubleshooting

**"Module supabase not found"**
```bash
pip install supabase
```

**"SUPABASE_URL not set"**
- Check `.env` file exists
- Check values copied correctly from Supabase

**Server won't start**
```bash
cd app
pip install -r ../requirements.txt
python app.py
```

**Need help?**
- Check QUICK_START.md
- Check http://localhost:8000/docs
- Check Supabase dashboard logs

---

## ⚡ Quick Test Commands

After starting server:

```bash
# Sign up
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test1234"}'

# Save the access_token from response!

# Create profile (replace YOUR_TOKEN)
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "personal_info": {"name": "Test", "email": "test@test.com", "phone": "123"},
    "summary": "Test",
    "education": [{"degree": "BSc", "institution": "Uni", "location": "City", "year": "2020"}],
    "experience": [{"title": "Dev", "company": "Co", "location": "City", "years": "2020"}],
    "projects": [{"name": "Proj", "role": "Dev", "year": "2020", "description": "Test"}],
    "skills": ["Python"]
  }'

# Get profile
curl http://localhost:8000/api/v1/profile \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 Summary

**Total time to working system: ~15 minutes**

1. Install Supabase → 30 seconds
2. Create project → 3 minutes  
3. Create table → 2 minutes
4. Get keys → 1 minute
5. Update .env → 1 minute
6. Test → 5 minutes

**You're ready! Start with Step 1 above.** 🚀
