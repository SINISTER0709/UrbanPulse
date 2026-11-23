# UrbanPulse AI Complaint Analysis Platform - Backend (Track E / Stage E1)

UrbanPulse is an AI-powered municipal complaint analysis, spatial clustering, and triage engine.

---

## Stage E1: Core Foundation Features

1. **Locked Day-0 Categories**:
   - `road_damage`
   - `garbage_sanitation`
   - `streetlight_electrical`
   - `water_supply`
   - `drainage_flooding`
   - `other`

2. **Fault-Tolerant Ingestion**:
   - Every citizen submission is immediately written to PostgreSQL/PostGIS.
   - Status defaults to `received_pending_ai`.
   - Data source defaults to `user_submitted`.
   - Returns **201 Created** immediately with:
     ```json
     {
       "report_id": "<uuid>",
       "status": "received_pending_ai",
       "created_at": "<iso-timestamp>",
       "data_source": "user_submitted"
     }
     ```
   - Downstream AI classification, severity scoring, and duplicate detection run asynchronously in decoupled background workers; downtime or errors in downstream workers never drop or fail citizen submissions.

3. **Privacy & RBAC**:
   - Explicit consent enforcement (`consent=true` required).
   - Minimal personal data storage policy.
   - Role-Based Access Control (`Citizen`, `Admin`, `Department`).

4. **Spatial Indexing**:
   - Coordinates stored in PostGIS `Geometry(POINT, 4326)` with GIST spatial indexing.
   - Points of Interest (`pois`) table for proximity escalation.

---

## Directory Layout

```
backend/
├── app/
│   ├── api/
│   │   ├── auth.py              # Register, login, profile endpoints
│   │   ├── complaints.py        # Fault-tolerant POST /api/complaints endpoint
│   │   └── deps.py              # Dependency injection & RBAC role guards
│   ├── core/
│   │   ├── security.py          # Bcrypt hashing & JWT creation/verification
│   │   └── rbac.py              # Role enforcement (Citizen, Admin, Department)
│   ├── db/
│   │   ├── session.py           # SQLAlchemy sessionmaker & engine
│   │   └── init_db.py           # Schema creation & PostGIS check
│   ├── models/
│   │   ├── base.py              # DeclarativeBase & PostGIS SpatialPoint type
│   │   ├── enums.py             # Day0Category, UserRole, ReportStatus
│   │   ├── user.py              # User account & auth model
│   │   ├── report.py            # Citizen complaint reports with PostGIS Point & GIST
│   │   ├── incident.py          # Clustered incident master & report associations
│   │   ├── ai.py                # AI predictions, embeddings, & duplicates
│   │   ├── evidence.py          # Photo & image attachments
│   │   ├── audit.py             # Priority & status audit trails
│   │   ├── assignment.py        # Municipal department assignments
│   │   ├── review.py            # Admin human-in-the-loop review decisions
│   │   ├── action_brief.py      # Field crew dispatch briefs & safety checklists
│   │   ├── poi.py               # Points of Interest (infrastructure / GIST index)
│   │   └── config_model.py      # Dynamic configuration & thresholds
│   ├── schemas/
│   │   ├── auth.py              # Pydantic auth schemas
│   │   └── report.py            # Ingestion & report schemas
│   ├── config.py                # Pydantic BaseSettings (.env loading)
│   └── main.py                  # FastAPI app & healthcheck
├── tests/
│   ├── conftest.py              # Test client, mock fixtures, in-memory DB
│   ├── test_auth.py             # Auth & RBAC test suite
│   └── test_complaints.py       # Fault-tolerant ingestion & consent tests
├── uploads/                     # Upload directory for photo evidence
├── docker-compose.yml           # PostgreSQL 15 + PostGIS 3.4
├── requirements.txt             # Python dependencies
├── .env.example                 # Sample configuration
└── .env                         # Active configuration
```

---

## Quickstart & Verification Commands

### 1. Activate Environment and Run Automated Tests
```powershell
# From C:\vs\URBANPULSE\backend
& .\.venv\Scripts\pytest -v
```

### 2. Run Database Container (Docker)
If Docker Desktop is installed:
```powershell
docker compose up -d
```

### 3. Start the FastAPI Development Server
```powershell
& .\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Interactive API documentation will be available at: `http://127.0.0.1:8080/docs`
