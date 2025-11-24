# Supabase Authentication Setup Guide

## What Changed

Authentication has been migrated from custom JWT/bcrypt to **Supabase Auth** - a managed authentication service.

### Benefits:
- ✅ **No password storage** - Supabase handles all credential management
- ✅ **Built-in features**: Email verification, password reset, magic links
- ✅ **Social OAuth**: Google, GitHub, etc. (configurable)
- ✅ **Security**: Auto-updates, breach detection, 2FA support
- ✅ **Free tier**: 50,000 monthly active users

---

## Setup Instructions

### 1. Create Supabase Project

1. Go to [https://supabase.com](https://supabase.com)
2. Sign up / Log in
3. Click **"New Project"**
4. Fill in:
   - **Name**: `portfolio-optimizer`
   - **Database Password**: (generate secure password)
   - **Region**: Choose closest to you
5. Wait 2 minutes for project creation

### 2. Get Your API Keys

1. In Supabase dashboard, go to **Settings** → **API**
2. Copy these values:
   - **Project URL**: `https://xxxxx.supabase.co`
   - **anon public key**: `eyJhbGc...` (long JWT token)
3. Go to **Settings** → **API** → **JWT Settings**
   - Copy **JWT Secret**: Used to verify tokens

### 3. Update `.env` File

Replace the placeholder values in `backend/.env`:

```env
# Supabase Authentication
SUPABASE_URL=https://your-actual-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc...your-actual-anon-key
SUPABASE_JWT_SECRET=your-actual-jwt-secret-from-settings
```

### 4. Enable Email Auth (Optional)

By default, Supabase requires email confirmation. To disable for development:

1. Go to **Authentication** → **Providers** → **Email**
2. **Disable** "Confirm email" 
3. Save

---

## API Changes

### Registration

**Before** (Custom):
```bash
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "Test123Pass"
}
# Returns: User object
```

**After** (Supabase):
```bash
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "Test123Pass"
}
# Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

### Login

**Before**:
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "Test123Pass"
}
# Returns: {"access_token": "custom-jwt", "token_type": "bearer"}
```

**After** (Supabase):
```bash
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "Test123Pass"
}
# Returns: {"access_token": "supabase-jwt", "token_type": "bearer"}
```

### Protected Routes

**No change** - still use Bearer token:
```bash
GET /api/auth/me
Headers: Authorization: Bearer eyJ...
```

---

## Frontend Integration

### React/Next.js

```bash
npm install @supabase/supabase-js
```

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_KEY!
)

// components/LoginForm.tsx
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password123'
})

// Use data.session.access_token for API calls
```

---

## Code Changes Summary

### Files Modified:

1. **`backend/utils/security.py`**
   - Removed: `get_password_hash()`, `verify_password()`, `create_access_token()`
   - Added: `verify_supabase_token()`, `extract_user_id()`

2. **`backend/api/auth.py`**
   - Replaced custom auth logic with Supabase client
   - Registration/login now call `supabase.auth.*` methods
   - Local database syncs user records from Supabase

3. **`backend/config.py`** & **`backend/.env`**
   - Added: `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_JWT_SECRET`

4. **`backend/requirements.txt`**
   - Removed: `bcrypt>=4.2.0`
   - Added: `supabase>=2.0.0`

---

## Testing

```bash
# Start server
cd backend
python main.py

# Register (returns token immediately)
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123Pass"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123Pass"}'

# Get current user
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

---

## Rollback (If Needed)

To revert to custom auth:

```bash
git revert HEAD
pip install bcrypt>=4.2.0
pip uninstall supabase
```

---

## Additional Features (Available Now)

Once Supabase is configured, you get these for free:

1. **Password Reset**
   ```typescript
   await supabase.auth.resetPasswordForEmail('user@example.com')
   ```

2. **Email Verification**
   - Automatic confirmation emails
   - Configurable templates

3. **Magic Links** (passwordless login)
   ```typescript
   await supabase.auth.signInWithOtp({ email: 'user@example.com' })
   ```

4. **Social OAuth**
   - Enable in Supabase dashboard: Authentication → Providers
   - Supports: Google, GitHub, GitLab, Bitbucket, etc.

5. **Row Level Security (RLS)**
   - Automatic user-based data isolation in PostgreSQL
   - No custom middleware needed

---

## Support

- **Supabase Docs**: https://supabase.com/docs/guides/auth
- **Python Client**: https://supabase.com/docs/reference/python/introduction
- **Community**: https://github.com/supabase/supabase/discussions
