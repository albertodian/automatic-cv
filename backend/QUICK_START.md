# 🚀 Quick Start: What to Do Now

## Your Current Status

✅ Backend skeleton created  
✅ App.py updated with authentication support  
✅ Flexible solution implemented (works with/without auth)  

---

## 🎯 Follow These Steps in Order

### Step 1: Set Up Supabase (15 min) ⭐ START HERE

**1.1 Create Project**
- Go to https://supabase.com and sign up
- Click "New Project"
- Name: `cv-generator`
- Create strong database password and SAVE IT
- Choose region close to you
- Wait 2-3 minutes for setup

**1.2 Create Database Table**
- In Supabase, click "SQL Editor" (left sidebar)
- Click "New query"
- Copy this entire SQL code:

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

CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own profile"
    ON profiles FOR DELETE
    USING (auth.uid() = user_id);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);
```

- Click "Run"
- Should say "Success"

**1.3 Get API Keys**
- Click "Project Settings" (gear icon, bottom left)
- Click "API"
- Copy these TWO values:
  - **Project URL**: `https://xxxxx.supabase.co`
  - **anon public key**: Long string starting with `eyJ...`

---

### Step 2: Install Supabase (2 min)

Open terminal in your project folder:

```bash
# Add to requirements.txt
echo "supabase==2.3.0" >> requirements.txt

# Install
pip install supabase
```

---

### Step 3: Configure Environment (3 min)

**3.1 Local Development**

Open (or create) `.env` file in project root and add:

```env
# Your existing token
REPLICATE_API_TOKEN=your_existing_token

# New Supabase credentials (replace with YOUR values from Step 1.3)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**3.2 Railway (Production)**

1. Go to your Railway project dashboard
2. Click on your service
3. Click "Variables" tab
4. Add these:
   - Variable name: `SUPABASE_URL`, Value: `https://xxxxx.supabase.co`
   - Variable name: `SUPABASE_KEY`, Value: `eyJ...`
5. Save (Railway auto-deploys)

---

### Step 4: Test Locally (10 min)

**4.1 Start Server**

```bash
cd app
python app.py
```

Server starts on http://localhost:8000

**4.2 Test Sign Up**

Open new terminal:

```bash
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

You should get:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": "...",
    "email": "test@example.com"
  }
}
```

**SAVE THE access_token** - you'll need it!

**4.3 Test Profile Creation**

Replace `YOUR_TOKEN` with the access_token from above:

```bash
curl -X POST http://localhost:8000/api/v1/profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "personal_info": {
      "name": "John Doe",
      "email": "john@example.com",
      "phone": "+1234567890"
    },
    "summary": "Experienced software engineer",
    "education": [{
      "degree": "BSc Computer Science",
      "institution": "Tech University",
      "location": "San Francisco",
      "year": "2015-2019"
    }],
    "experience": [{
      "title": "Software Engineer",
      "company": "Tech Corp",
      "location": "Remote",
      "years": "2019-2024"
    }],
    "projects": [{
      "name": "Cool Project",
      "role": "Lead Developer",
      "year": "2023",
      "description": "Built an awesome thing"
    }],
    "skills": ["Python", "FastAPI", "Docker", "Machine Learning"]
  }'
```

Should return your profile with an ID!

**4.4 Test CV Generation (Authenticated)**

```bash
curl -X POST http://localhost:8000/api/cv/generate-authenticated \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "job_description": "Looking for a Software Engineer with Python and FastAPI experience. Must know Docker and have ML background.",
    "template": "tech",
    "model_name": "openai/gpt-4.1-mini"
  }'
```

This will:
1. Load your profile from database automatically
2. Generate optimized CV using RAG
3. Return the optimized CV JSON

**4.5 Verify in Supabase**

1. Go back to Supabase dashboard
2. Click "Table Editor"
3. Click "profiles" table
4. You should see your profile data!

---

### Step 5: Check Interactive Docs (2 min)

Visit http://localhost:8000/docs

You should see:
- **Backend** section with auth endpoints
- **CV Generation (Authenticated)** section with new endpoints
- All your existing endpoints still working

---

## 📊 What You Have Now

### ✅ New Authenticated Endpoints

**Authentication:**
- `POST /api/v1/auth/signup` - Create account
- `POST /api/v1/auth/signin` - Login
- `POST /api/v1/auth/signout` - Logout

**Profile Management:**
- `GET /api/v1/profile` - Get user's profile
- `POST /api/v1/profile` - Create/update profile
- `DELETE /api/v1/profile` - Delete profile

**CV Generation (Authenticated - Uses DB Profile):**
- `POST /api/cv/generate-authenticated` - Generate CV with job description
- `POST /api/cv/generate-authenticated-from-url` - Generate CV from job URL

### ✅ Existing Endpoints Still Work (Backward Compatible)

All your original endpoints work without authentication:
- `/api/cv/generate` - With profile in request body
- `/api/cv/generate-from-url` - With profile in request body
- `/api/cv/generate-json` - With profile in request body
- etc.

---

## 🎯 How to Use It

### Option 1: With Authentication (Recommended)

**First Time:**
```
1. User signs up → POST /api/v1/auth/signup
2. User creates profile → POST /api/v1/profile
3. User generates CV → POST /api/cv/generate-authenticated
   (profile loaded from DB automatically!)
```

**Returning User:**
```
1. User signs in → POST /api/v1/auth/signin
2. User generates CV → POST /api/cv/generate-authenticated
   (profile still in DB!)
```

### Option 2: Without Authentication (Backward Compatible)

```
User generates CV → POST /api/cv/generate
(sends profile in request body, nothing saved)
```

---

## 🔧 Common Issues

### "Module 'supabase' not found"
```bash
pip install supabase
```

### "SUPABASE_URL not set"
Check your `.env` file has the correct values from Step 1.3

### "Invalid authentication token"
- Token expired (1 hour lifetime)
- User needs to sign in again
- Or use refresh token to get new access token

### "Profile not found"
- User hasn't created profile yet
- They need to call `POST /api/v1/profile` first

### Server doesn't start
- Make sure you're in the `app` directory
- Check all dependencies installed: `pip install -r requirements.txt`

---

## 📱 Frontend Integration Example

If you have a React/Vue/etc frontend:

```javascript
// Sign up
const signUp = async (email, password) => {
  const res = await fetch('http://localhost:8000/api/v1/auth/signup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  const { access_token } = await res.json();
  localStorage.setItem('token', access_token);
};

// Create profile
const createProfile = async (profileData) => {
  await fetch('http://localhost:8000/api/v1/profile', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify(profileData)
  });
};

// Generate CV
const generateCV = async (jobDescription) => {
  const res = await fetch('http://localhost:8000/api/cv/generate-authenticated', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({
      job_description: jobDescription,
      template: 'tech'
    })
  });
  return await res.json();
};
```

---

## 🎉 You're Done!

Once you complete Steps 1-5, you have:
- ✅ User authentication working
- ✅ Profile storage in Supabase
- ✅ CV generation using stored profiles
- ✅ Backward compatibility maintained
- ✅ Production-ready security

**Time to complete: ~30 minutes**

---

## 📚 Next Steps

### After Everything Works:

1. **Deploy to Railway**
   - Push your code to GitHub
   - Railway auto-deploys
   - Make sure environment variables are set

2. **Add Email Verification** (Optional)
   - Configure in Supabase Auth settings
   - Update email templates

3. **Build Frontend** (Optional)
   - React/Vue/Next.js app
   - Use the authentication flow above

4. **Add More Features** (Optional)
   - Password reset
   - Profile versioning
   - CV history

---

## 📞 Need Help?

- Check `IMPLEMENTATION_GUIDE.md` for detailed explanations
- Check `SETUP.md` for technical details
- Visit http://localhost:8000/docs for API testing
- Check Supabase logs in dashboard

---

**Start with Step 1 now! 🚀**
