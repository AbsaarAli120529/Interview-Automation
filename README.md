# AI Interview Automation Platform

Full-stack interview automation platform with AI-powered question generation, real-time transcription, and multi-modal identity verification.

## 🏗️ Architecture

- **Frontend**: Next.js 16 with TypeScript, React, and Tailwind CSS
- **Backend**: FastAPI with PostgreSQL, SQLAlchemy, and Alembic
- **AI Services**: Azure OpenAI (GPT-4o), Azure Speech-to-Text, Azure Face API
- **Real-time**: WebSocket for live transcription and proctoring

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** 18+ and npm
- **Python** 3.10+
- **PostgreSQL** 15+
- **Git**

---

## 🗄️ Database Setup

### 1. Install and Start PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**Windows:**
Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)

### 2. Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE interview_db;

# Create user (optional, or use default postgres user)
CREATE USER interview_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE interview_db TO interview_user;

# Exit psql
\q
```

### 3. Database Connection String

Note your database connection details:
- **Host**: `localhost` (default)
- **Port**: `5432` (default)
- **Database**: `interview_db`
- **User**: `postgres` (or your custom user)
- **Password**: Your PostgreSQL password

> **Important**: If your password contains special characters like `@`, encode them:
> - `@` → `%40`
> - `#` → `%23`
> - `%` → `%25`

---

## 🔧 Backend Setup

### 1. Navigate to Backend Directory

```bash
cd mock_backend
```

### 2. Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the `mock_backend/` directory:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/interview_db

# Security
SECRET_KEY=your-super-secret-key-change-me-in-production
ALGORITHM=HS256

# Azure OpenAI (for question generation and answer evaluation)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Azure Speech-to-Text (for live transcription)
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=eastus

# Azure Face API (for face verification)
AZURE_FACE_API_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_FACE_API_KEY=your_azure_face_key

# Azure Speech Service (for voice verification)
AZURE_SPEECH_API_KEY=your_azure_speech_key
```

> **Note**: If Azure credentials are not provided, the system will use mock mode for AI services.

### 5. Run Database Migrations

```bash
# Run all migrations
alembic upgrade head

# If you encounter migration errors, you can also run the quick fix script:
python fix_database_schema.py
```

### 6. Seed Initial Data

```bash
# Seed admin user, templates, and question bank
python -m seeds.run_seeds
```

This creates:
- **Admin user**: `admin` / `admin`
- Default interview templates
- Question bank with various categories

### 7. Start Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```

The backend will be available at:
- **API Server**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`

---

## 🎨 Frontend Setup

### 1. Navigate to Frontend Directory

```bash
cd frontend
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```env
# Backend API URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Azure Speech (for Text-to-Speech - optional)
NEXT_PUBLIC_AZURE_SPEECH_KEY=your_azure_speech_key
NEXT_PUBLIC_AZURE_SPEECH_REGION=eastus
```

### 4. Start Frontend Development Server

```bash
npm run dev
```

The frontend will be available at:
- **Frontend**: `http://localhost:3000` (or `http://localhost:3001` if 3000 is in use)

---

## 🚀 Running the Complete Application

### Terminal 1: Backend Server
```bash
cd mock_backend
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### Terminal 2: Frontend Server
```bash
cd frontend
npm run dev
```

### Access the Application

1. **Admin Dashboard**: `http://localhost:3000/admin`
   - Login: `admin` / `admin`
   - Register candidates, schedule interviews, view dashboard

2. **Candidate Dashboard**: `http://localhost:3000/candidate`
   - Login with candidate credentials (provided when admin registers candidate)
   - Upload face/voice samples, start interviews

---

## 🔐 Default Credentials

- **Admin**: 
  - Username: `admin`
  - Password: `admin`

- **Candidate**: 
  - Credentials are generated when admin registers a candidate
  - Check terminal output when registering a candidate

---

## 📊 Database Management

### Run Migrations

```bash
cd mock_backend
alembic upgrade head
```

### Create New Migration

```bash
alembic revision --autogenerate -m "description of changes"
alembic upgrade head
```

### Rollback Migration

```bash
alembic downgrade -1  # Rollback one migration
```

### Quick Database Fixes

If you encounter schema issues, run:

```bash
cd mock_backend
python fix_database_schema.py
```

---

## 🧪 Testing the Setup

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "message": "Backend is healthy"}
```

### 2. Check Database Connection

The backend will log database connection status on startup. Look for:
- ✅ Successful connection messages
- ❌ Connection errors (check DATABASE_URL in .env)

### 3. Test Frontend-Backend Connection

1. Open browser console (F12)
2. Navigate to `http://localhost:3000/admin`
3. Check for any connection errors
4. Try logging in with admin credentials

---

## 🐛 Troubleshooting

### Backend Issues

**Error: Database connection failed**
- Verify PostgreSQL is running: `pg_isready` or `psql -U postgres`
- Check DATABASE_URL in `.env` file
- Ensure database exists: `psql -U postgres -l` (list databases)
- Verify password encoding (special characters)

**Error: Module not found**
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**Error: Migration errors**
- Run quick fix: `python fix_database_schema.py`
- Check Alembic version: `alembic current`
- Review migration files in `alembic/versions/`

**Error: Port 8000 already in use**
- Change port: `uvicorn app.main:app --reload --port 8001`
- Update `NEXT_PUBLIC_API_BASE_URL` in frontend `.env.local`

### Frontend Issues

**Error: Cannot connect to backend**
- Verify backend is running on `http://localhost:8000`
- Check `NEXT_PUBLIC_API_BASE_URL` in `.env.local`
- Check browser console for CORS errors
- Ensure backend CORS allows `http://localhost:3000`

**Error: Module not found**
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again

**Error: Port 3000 already in use**
- Next.js will automatically use port 3001
- Update `NEXT_PUBLIC_API_BASE_URL` if needed

### Database Issues

**Error: Table does not exist**
- Run migrations: `alembic upgrade head`
- Run quick fix: `python fix_database_schema.py`

**Error: Column does not exist**
- Check if migration was applied: `alembic current`
- Run specific migration or quick fix script

---

## 📁 Project Structure

```
interview_automation/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js app router pages
│   │   ├── components/      # React components
│   │   ├── lib/             # Utilities and API clients
│   │   └── store/           # Zustand state management
│   └── package.json
│
├── mock_backend/            # FastAPI backend application
│   ├── app/
│   │   ├── api/             # API routes
│   │   ├── services/        # Business logic
│   │   ├── db/              # Database models and repositories
│   │   └── main.py          # FastAPI application entry point
│   ├── alembic/             # Database migrations
│   ├── seeds/               # Database seeding scripts
│   └── requirements.txt
│
└── README.md                # This file
```

---

## 🔑 Environment Variables Summary

### Backend (.env in `mock_backend/`)
- `DATABASE_URL` - PostgreSQL connection string (required)
- `SECRET_KEY` - JWT secret key (required)
- `AZURE_OPENAI_*` - Azure OpenAI credentials (optional, for AI features)
- `AZURE_SPEECH_KEY` - Azure Speech key (optional, for transcription)
- `AZURE_FACE_*` - Azure Face API credentials (optional, for verification)

### Frontend (.env.local in `frontend/`)
- `NEXT_PUBLIC_API_BASE_URL` - Backend API URL (required)
- `NEXT_PUBLIC_AZURE_SPEECH_*` - Azure Speech for TTS (optional)

---

## 📚 Additional Resources

- **Backend API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Backend README**: See `mock_backend/README.md` for detailed backend documentation
- **Frontend README**: See `frontend/README.md` for frontend-specific details

---

## 🎯 Quick Start Checklist

- [ ] PostgreSQL installed and running
- [ ] Database `interview_db` created
- [ ] Backend virtual environment created and activated
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend `.env` file configured with DATABASE_URL
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Database seeded (`python -m seeds.run_seeds`)
- [ ] Backend server running (`uvicorn app.main:app --reload`)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Frontend `.env.local` configured with API_BASE_URL
- [ ] Frontend server running (`npm run dev`)
- [ ] Access admin dashboard at `http://localhost:3000/admin`

---

## 💡 Tips

1. **Keep both servers running**: Backend and frontend need to run simultaneously
2. **Check logs**: Backend logs show connection status and errors
3. **Browser console**: Frontend errors appear in browser DevTools console
4. **API testing**: Use Swagger UI at `http://localhost:8000/docs` to test endpoints
5. **Database inspection**: Use `psql` or pgAdmin to inspect database tables

---

## 🆘 Need Help?

- Check the troubleshooting section above
- Review backend logs for detailed error messages
- Check browser console for frontend errors
- Verify all environment variables are set correctly
- Ensure PostgreSQL is running and accessible
