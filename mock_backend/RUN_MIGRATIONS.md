# Database Migration Instructions

## Problem
The database is missing columns that the SQLAlchemy models expect, causing errors like:
```
column candidate_profiles.role_name does not exist
```

## Solution
Run the Alembic migrations to sync the database schema with the models.

## Steps

1. **Navigate to the mock_backend directory:**
   ```bash
   cd mock_backend
   ```

2. **Activate your virtual environment (if using one):**
   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   .\venv\Scripts\activate  # On Windows
   ```

3. **Run the migrations:**
   ```bash
   alembic upgrade head
   ```

   This will apply all pending migrations and add the missing columns:
   - `role_name`
   - `resume_filename`
   - `resume_path`
   - `resume_json`
   - `jd_json`
   - `match_score`
   - `parse_status`
   - `parsed_at`
   - `resume_text`

4. **Verify the migration:**
   ```bash
   alembic current
   ```
   
   Should show the latest revision: `fix_missing_columns`

5. **Restart your backend server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## If Migration Fails

If you get errors about migration conflicts, you can:

1. **Check current migration status:**
   ```bash
   alembic current
   ```

2. **Check migration history:**
   ```bash
   alembic history
   ```

3. **If needed, manually mark the database as up-to-date:**
   ```bash
   alembic stamp head
   ```
   (Only use this if you're sure the schema matches)

## Alternative: Manual SQL Fix

If migrations don't work, you can manually add the missing columns:

```sql
ALTER TABLE candidate_profiles 
ADD COLUMN IF NOT EXISTS role_name VARCHAR,
ADD COLUMN IF NOT EXISTS resume_filename VARCHAR,
ADD COLUMN IF NOT EXISTS resume_path VARCHAR,
ADD COLUMN IF NOT EXISTS resume_json JSONB,
ADD COLUMN IF NOT EXISTS jd_json JSONB,
ADD COLUMN IF NOT EXISTS match_score DOUBLE PRECISION,
ADD COLUMN IF NOT EXISTS parse_status VARCHAR DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS parsed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS resume_text TEXT;

CREATE INDEX IF NOT EXISTS ix_candidate_profiles_role_name ON candidate_profiles(role_name);
```
