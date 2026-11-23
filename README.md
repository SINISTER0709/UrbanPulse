# UrbanPulse AI 🏙️⚡
> **A Multi-Modal, Explainable Civic Grievance Triage, Geospatial Deduplication, and Municipal Decision-Support Platform**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.3+-646CFF?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)
[![PostGIS](https://img.shields.io/badge/PostGIS-3.4+-336791?style=flat&logo=postgresql&logoColor=white)](https://postgis.net)
[![Pytest](https://img.shields.io/badge/Tests-23%20Passed%20(100%25)-brightgreen?style=flat&logo=pytest&logoColor=white)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 Abstract & Overview

**UrbanPulse AI** is an intelligent, transparent civic grievance triage and decision-support web platform engineered to resolve systemic operational bottlenecks in municipal governance.

Municipal bodies receive large volumes of informal, free-text citizen complaints across diverse civic sectors (hazardous road potholes, garbage accumulation, malfunctioning streetlights, water leakages, and flooding). Traditional civic grievance portals suffer from:
1. **Unprioritized Backlogs:** Minor complaints take precedence over critical safety hazards.
2. **Duplicate Load Inflation:** Multiple citizens independently reporting the same issue artificially overstate distinct problem counts.
3. **Black-Box AI Skepticism:** Unexplainable machine-learning scores that municipal officers cannot defend or audit.
4. **Ingestion Outages:** Submission portals freezing when downstream AI models experience high inference latency.

UrbanPulse AI resolves these challenges through a modular, decoupled architecture rooted in a **Day-0 Configuration Freeze** of 6 locked civic categories, asynchronous task processing, explainable multi-factor priority scoring, and human-in-the-loop review controls.

---

## 🚀 Key Features

* **Sub-Second, Fault-Tolerant Ingestion (< 100ms):** Immediate `201 Created` HTTP acknowledgment with `report_id` (`rpt_...`) and persistent DB storage before triggering downstream AI models.
* **DPDP Act 2023 Compliance:** Minimal data collection policy with mandatory explicit consent enforcement.
* **Track A — Few-Shot LLM Classification:** Llama 3 8B Instruct classifier mapping free-text complaints to locked Day-0 categories and departments with automatic JSON validation and fallback.
* **Track B — Independent ML Severity Prediction:** N-gram TF-IDF vectorizer + Linear SVM classifier (Low, Medium, High, Critical) with zero image leakage.
* **Track C — Optional YOLOv8 Vision Verification:** Corroborates attached citizen photos as visual evidence with a **strict 0% weight** in priority and severity scoring.
* **Track D — Responsive Dual-Portal Frontend:** 
  * *Citizen Portal:* Sub-45 second reporting flow, OpenStreetMap pin placement, photo upload, and live 4-stage resolution stepper.
  * *Admin Operations Center:* 5 primary metric cards, high-priority feed, interactive Leaflet GIS map, and separate active vs. resolved triage queue.
* **Track E — Async Backend & Audit Architecture (Stages E1 & E2):** FastAPI application with PostgreSQL + PostGIS, JWT stateless RBAC, BackgroundTasks orchestration, and comprehensive `admin_reviews` audit logging.
* **Track F — Geospatial Deduplication, Priority & RAG:**
  * *Spatial & Semantic Deduplication:* PostGIS 100m radius (`ST_DWithin`) combined with Sentence Transformers (`all-MiniLM-L6-v2`) cosine similarity ($\ge 0.82$).
  * *Explainable 5-Factor Priority Formula:*
    $$\mathbf{P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E}$$
    with automatic **Urgent Review Flagging** for high-risk hazards (school/hospital proximity).
  * *Hotspot Density Clustering:* DBSCAN spatial clustering identifying systemic infrastructure failure zones.
  * *RAG SOP Action Briefs:* ChromaDB vector store retrieving municipal Standard Operating Procedures (SOPs) for administrative guidance.

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph Clients["Presentation Layer (React 18 + Vite)"]
        CP[Citizen Portal - Mobile Web]
        AD[Admin Operations Center]
        GIS[Leaflet GIS Map & Analytics]
    end

    subgraph Gateway["Gateway & Security Tier (FastAPI)"]
        AUTH[JWT RBAC & Password Hashing]
        INGEST[Multipart Ingestion Endpoint]
        SYNC_DB[(PostGIS / SQLite DB)]
    end

    subgraph AsyncWorker["Asynchronous Orchestration Tier"]
        BG[FastAPI BackgroundTasks Orchestrator]
        A[Track A: Llama 3 LLM Classifier]
        B[Track B: TF-IDF + SVM Severity Model]
        C[Track C: YOLOv8 Image Verification]
        F1[Track F: S-BERT Duplicate Matcher]
        F2[Track F: 5-Factor Priority Engine]
        F3[Track F: DBSCAN Hotspots]
        F4[Track F: ChromaDB RAG SOP Briefs]
    end

    CP -->|1. Submit Complaint (GPS, text, photo, consent)| INGEST
    INGEST -->|2. Instant Persistent Store| SYNC_DB
    INGEST -->|3. Synchronous 201 Created ACK| CP
    INGEST -->|4. Trigger Async Pipeline| BG
    
    BG --> A & B & C & F1
    A & B & F1 --> F2
    F2 -->|Update Incident & Audit Record| SYNC_DB
    F4 -->|Fetch Municipal SOP Context| AD
    SYNC_DB --> AD & GIS
```

---

## 📁 Repository Structure

```text
URBANPULSE/
├── Backend/                 # FastAPI REST API & Pipeline Services
│   ├── app/
│   │   ├── api/            # API Routers (auth, complaints, incidents, analytics)
│   │   ├── models/         # SQLAlchemy ORM Models (Report, Incident, User, etc.)
│   │   ├── schemas/        # Pydantic Schemas for Requests and Responses
│   │   ├── services/       # Pipeline Orchestration, LLM client, ML pipelines
│   │   ├── config.py       # Pydantic Settings & Day-0 Freeze Config
│   │   └── main.py         # FastAPI App Entrypoint & Static Uploads Mount
│   ├── tests/              # 23 Automated Pytest Integration & Unit Tests
│   ├── Dockerfile          # Containerized backend packaging
│   ├── docker-compose.yml  # Docker multi-service stack with PostgreSQL/PostGIS
│   └── requirements.txt    # Python dependencies
├── frontend/                # React 18 + Vite + Tailwind Citizen & Admin App
│   ├── src/
│   │   ├── components/     # Shell, Navigation, Actions Modals, Leaflet MapView
│   │   ├── pages/          # Overview, Queue, Detail, Report, Track, Login
│   │   ├── api/            # Typed Client API wrappers
│   │   └── types/          # Shared TypeScript Interfaces & Day-0 Enums
│   └── vite.config.ts      # Proxy routing for /api and /uploads
├── other_tracks/            # Component development trees for Tracks A, C, D, F
├── PDF/                     # Official Capstone Evaluation Deliverables Report
│   └── UrbanPulse_AI_Evaluation_Deliverables.pdf
├── build_deliverables_pdf.py# Automated ReportLab PDF generator script
├── .gitignore               # Strict exclusion of .venv, node_modules, .env, *.gguf
└── README.md                # Project documentation
```

---

## ⚡ Quick Start & Installation

### 1. Prerequisites
* **Python:** 3.11 or higher
* **Node.js:** v18 or higher (with npm)
* **Git**

### 2. Backend Setup
```bash
# Navigate to the backend directory
cd Backend

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Initialize database tables and seed test accounts
python init_database.py
python seed_users.py

# Launch the FastAPI application server
uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```
* Interactive API Documentation will be accessible at: `http://127.0.0.1:8080/docs`

### 3. Frontend Setup
```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install npm packages
npm install

# Start Vite development server
npm run dev
```
* Citizen Portal: `http://localhost:5173/`
* Citizen Complaint Tracker: `http://localhost:5173/track`
* Administrator Dashboard: `http://localhost:5173/admin`

---

## 🧪 Testing & Verification

The test suite covers full-stack integration, auth RBAC, fault-tolerant ingestion, ML classification, spatial deduplication, priority mathematics, and administrative override lifecycles.

```bash
# Run the complete test suite
pytest Backend/tests -v
```

**Results:**
```text
======================= 23 passed in 125.35s =======================
```

---

## 👥 Academic & Team Information

* **Institution:** School of Computer Science Engineering and Technology, **Bennett University (The Times Group)**
* **Course:** CSET400C — Capstone Project (Session: 2026-27)
* **Faculty Mentor:** **Dr. Indrajeet Gupta**
* **Project Team Members:**
  * **Kapil Kumar Bhitoria** — `E23CSEU1552`
  * **Ayush Mishra** — `E23CSEU1559`
  * **Animay Jha** — `E23CSEU1517`

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
