# 🏗️ Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT/FRONTEND                          │
│              (Browser, Mobile App, API Consumer)                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTP/REST API
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                       FASTAPI SERVER                             │
│                     (app/app.py - Railway)                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          AUTHENTICATION LAYER (Optional)                 │   │
│  │                                                           │   │
│  │  • JWT Token Validation                                  │   │
│  │  • User Identification                                   │   │
│  │  • Authorization Checks                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BACKEND ROUTES                              │   │
│  │                                                           │   │
│  │  • /api/v1/auth/* - Sign up, Sign in, Sign out          │   │
│  │  • /api/v1/profile - Profile CRUD                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         CV GENERATION ENDPOINTS                          │   │
│  │                                                           │   │
│  │  Authenticated (uses DB profile):                        │   │
│  │  • /api/cv/generate-authenticated                        │   │
│  │  • /api/cv/generate-authenticated-from-url               │   │
│  │                                                           │   │
│  │  Unauthenticated (backward compatible):                  │   │
│  │  • /api/cv/generate                                      │   │
│  │  • /api/cv/generate-from-url                             │   │
│  │  • /api/cv/generate-json                                 │   │
│  │  • All existing endpoints...                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              BUSINESS LOGIC                              │   │
│  │                                                           │   │
│  │  • RAG System (ChromaDB + Sentence Transformers)         │   │
│  │  • LLM Agent (Replicate API)                             │   │
│  │  • ATS Optimizer                                         │   │
│  │  • Structure Validator                                   │   │
│  │  • PDF Renderer (WeasyPrint)                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────┬────────────────────────────┬────────────────────┘
                │                            │
                │                            │
        ┌───────▼──────────┐        ┌───────▼──────────┐
        │    SUPABASE      │        │   REPLICATE      │
        │   (Database)     │        │   (LLM API)      │
        │                  │        │                  │
        │ • User Auth      │        │ • GPT-4          │
        │ • Profile Storage│        │ • Text Gen       │
        │ • JWT Tokens     │        └──────────────────┘
        └──────────────────┘
```

---

## Data Flow

### 1. User Sign Up Flow

```
User → POST /api/v1/auth/signup
       ↓
    Supabase Auth
       ↓
    Create User in auth.users
       ↓
    Generate JWT Tokens
       ↓
    Return tokens to user
```

### 2. Profile Creation Flow

```
User → POST /api/v1/profile
       ↓
    Validate JWT Token
       ↓
    Extract user_id from token
       ↓
    Save to Supabase profiles table
       ↓
    Return saved profile
```

### 3. CV Generation Flow (Authenticated)

```
User → POST /api/cv/generate-authenticated
       ↓
    Validate JWT Token
       ↓
    Load profile from Supabase (user_id)
       ↓
    Initialize RAG System
       ↓
    Index profile in ChromaDB
       ↓
    Parse job description
       ↓
    Retrieve relevant content (RAG)
       ↓
    Call Replicate LLM API
       ↓
    Validate structure
       ↓
    Optimize for ATS
       ↓
    Return optimized CV (JSON)
       ↓
    (Optionally) Render to PDF
```

### 4. CV Generation Flow (Unauthenticated - Backward Compatible)

```
User → POST /api/cv/generate
       ↓
    Profile in request body
       ↓
    Initialize RAG System
       ↓
    Index profile in ChromaDB
       ↓
    Parse job description
       ↓
    Retrieve relevant content (RAG)
       ↓
    Call Replicate LLM API
       ↓
    Validate structure
       ↓
    Optimize for ATS
       ↓
    Return optimized CV (JSON)
       ↓
    (Optionally) Render to PDF
```

---

## Database Schema

### Supabase Tables

**auth.users (Managed by Supabase)**
```sql
auth.users
├── id (UUID, primary key)
├── email (text, unique)
├── encrypted_password (text)
├── created_at (timestamp)
├── updated_at (timestamp)
└── ... (other Supabase fields)
```

**profiles (Your Custom Table)**
```sql
profiles
├── id (UUID, primary key)
├── user_id (UUID, foreign key → auth.users.id, UNIQUE)
├── profile_data (JSONB)
│   └── {
│         "personal_info": {...},
│         "summary": "...",
│         "education": [...],
│         "experience": [...],
│         "projects": [...],
│         "skills": [...]
│       }
├── created_at (timestamp)
└── updated_at (timestamp)
```

**Relationship:** One user → One profile (enforced by UNIQUE constraint)

---

## Security Architecture

### JWT Token Flow

```
1. User signs in
   ↓
2. Supabase generates JWT
   ↓
3. JWT contains:
   - user_id
   - email
   - expiration (1 hour)
   - signature (verified by Supabase secret)
   ↓
4. Client stores token (localStorage/cookie)
   ↓
5. Client sends token in header:
   Authorization: Bearer <token>
   ↓
6. Server validates signature & expiration
   ↓
7. Extract user_id from token
   ↓
8. Use user_id to fetch/save data
```

### Row Level Security (RLS)

```
Database Level Security (Cannot be bypassed)

SELECT queries:
├── Check: auth.uid() = user_id
└── Result: User sees only their data

INSERT queries:
├── Check: auth.uid() = user_id
└── Result: User can only create their own records

UPDATE queries:
├── Check: auth.uid() = user_id
└── Result: User can only update their own records

DELETE queries:
├── Check: auth.uid() = user_id
└── Result: User can only delete their own records
```

---

## Component Breakdown

### Backend Components (`/backend/`)

```
backend/
├── database.py          → Supabase client singleton
├── auth.py              → JWT validation, get_current_user()
├── models.py            → Pydantic schemas
├── profile_service.py   → Profile CRUD operations
└── routes.py            → API endpoints
```

### Core Components (`/src/`)

```
src/
├── rag_system.py        → RAG (ChromaDB + embeddings)
├── llm_agent.py         → LLM calls (Replicate)
├── ats_optimizer.py     → ATS scoring & optimization
├── structure_validator.py → CV validation
├── renderer.py          → PDF generation
├── job_parser.py        → Job scraping
└── utils.py             → Helper functions
```

### API Layer (`/app/`)

```
app/
├── app.py               → Main FastAPI app
└── config.py            → Configuration settings
```

---

## Technology Stack

### Backend
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Authentication & Storage
- **Supabase** - Auth + PostgreSQL database
- **JWT** - Token-based authentication

### AI/ML
- **Replicate** - LLM API (GPT-4)
- **ChromaDB** - Vector database
- **Sentence Transformers** - Text embeddings

### PDF Processing
- **WeasyPrint** - PDF generation
- **PyPDF2 / pdfplumber** - PDF parsing
- **Playwright** - Web scraping

### Deployment
- **Railway** - Hosting platform
- **Docker** - Containerization

---

## Request/Response Flow Examples

### Example 1: Sign Up + Create Profile + Generate CV

```
1. POST /api/v1/auth/signup
   Body: { "email": "user@example.com", "password": "pass123" }
   Response: { "access_token": "eyJ...", "user": {...} }

2. POST /api/v1/profile
   Headers: { "Authorization": "Bearer eyJ..." }
   Body: { "personal_info": {...}, "education": [...], ... }
   Response: { "id": "uuid", "user_id": "uuid", "profile_data": {...} }

3. POST /api/cv/generate-authenticated
   Headers: { "Authorization": "Bearer eyJ..." }
   Body: { "job_description": "...", "template": "tech" }
   Response: { "success": true, "profile": {...optimized CV...} }
```

### Example 2: Guest User (No Auth)

```
1. POST /api/cv/generate
   Body: {
     "profile": {...complete profile...},
     "job_description": "...",
     "template": "tech"
   }
   Response: { "success": true, "profile": {...optimized CV...} }
```

---

## Scalability Considerations

### Current Architecture (Free Tier)
- **Railway**: ~500 users/day
- **Supabase**: 50,000 MAU
- **Bottleneck**: LLM API rate limits

### Scaling Up
1. **Horizontal scaling**: Add more Railway instances
2. **Caching**: Cache job descriptions, embeddings
3. **Queue system**: Background job processing
4. **CDN**: Cache PDFs if storing them

---

## Monitoring & Logging

### What to Monitor
- **API response times**
- **Auth success/failure rates**
- **Database query performance**
- **LLM API usage**
- **Error rates by endpoint**

### Available Logs
- **Railway**: Application logs
- **Supabase**: Database logs, auth logs
- **FastAPI**: Built-in logging

---

## Backup & Recovery

### Supabase Automatic Backups
- **Daily backups** (retained 7 days on free tier)
- **Point-in-time recovery** (paid plans)

### Manual Backups
```bash
# Export all profiles
curl http://localhost:8000/api/v1/profiles/export \
  -H "Authorization: Bearer <admin_token>"
```

---

## Performance Metrics

### Expected Response Times
- **Auth endpoints**: 100-300ms
- **Profile CRUD**: 50-200ms
- **CV generation**: 5-15 seconds (depends on LLM)
- **PDF rendering**: 1-3 seconds

### Bottlenecks
1. **LLM API calls** - 3-10 seconds
2. **RAG indexing** - 1-2 seconds
3. **ATS optimization** - 2-5 seconds

---

This architecture provides a solid foundation that can scale from prototype to production! 🚀
