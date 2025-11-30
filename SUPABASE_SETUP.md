# Supabase Setup Guide

## 1. Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/login
2. Click "New Project"
3. Set project name and database password
4. Click "Create new project"

## 2. Get Credentials

Once created, go to Project Settings → API:
- **URL**: `https://[your-project-ref].supabase.co`
- **anon/public key**: For client-side auth
- **service_role key**: Admin access (keep secret!)

Database (Settings → Database):
- **Connection String**: `postgresql://postgres:[password]@db.[your-project-ref].supabase.co:5432/postgres`

## 3. Create `.env` File

```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres:your-password@db.your-project-ref.supabase.co:5432/postgres
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
ENVIRONMENT=development
```

## 4. Enable Email Auth

1. Authentication → Providers → Enable "Email"
2. Disable "Confirm email" for development

## 5. Create Database Tables

**Option A: Supabase Table Editor (Recommended)**
1. Go to Supabase Dashboard → Table Editor
2. Create tables manually or use SQL Editor with this schema:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE portfolios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    ticker VARCHAR(10) NOT NULL,
    quantity NUMERIC(20, 8) NOT NULL CHECK (quantity > 0),
    average_cost NUMERIC(20, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(portfolio_id, ticker)
);

CREATE TABLE portfolio_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    calculation_date DATE NOT NULL,
    total_value NUMERIC(20, 2),
    daily_return NUMERIC(10, 6),
    volatility NUMERIC(10, 6),
    sharpe_ratio NUMERIC(10, 6),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(portfolio_id, calculation_date)
);

CREATE TABLE optimization_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    portfolio_id UUID REFERENCES portfolios(id) ON DELETE CASCADE,
    strategy VARCHAR(50) NOT NULL,
    optimized_weights JSONB NOT NULL,
    expected_return NUMERIC(10, 6),
    expected_volatility NUMERIC(10, 6),
    sharpe_ratio NUMERIC(10, 6),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Option B: Use SQLAlchemy to create tables**
```python
# In Python console
from database import engine, Base
from models import user, portfolio, holding, portfolio_analytics, optimization_result
Base.metadata.create_all(bind=engine)
```

## 6. Test

```bash
python -m uvicorn main:app --reload
```

Test registration:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'
```

## What Supabase Provides

✅ User auth (registration, login, JWT tokens)  
✅ Password hashing  
✅ Rate limiting (300 req/hour)  
✅ Managed PostgreSQL  
✅ Automatic backups  
✅ SSL/TLS encryption

