# ReSource: Predictive Circular Resource Intelligence Network

> **Tagline:** Predict. Match. Redistribute. Sustain.

ReSource is a software-only startup platform designed to reduce resource waste by predicting surplus and unmet demand, intelligently matching compatible resource pairs, optimizing multi-facility allocation under real-world constraints, and measuring defensible sustainability impact.

The initial MVP focuses on **Food Surplus** from commercial suppliers (hotels, restaurants, event venues) to verified demand from NGOs, food banks, and community shelters. The system architecture is built to be abstract and extensible to future resource categories (e.g., electronics, textiles, medical supplies).

---

## 🏗️ Project Architecture & Folder Structure

```
ReSource HG/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # RESTful FastAPI Endpoints (Health, Surplus, Demand, Orgs)
│   │   ├── core/            # Configuration & Database Engine (SQLite Dev Fallback / Postgres Ready)
│   │   ├── models/          # SQLAlchemy Database Models (Organization, SurplusListing, DemandListing, Allocation, ImpactLog, Prediction)
│   │   ├── schemas/         # Pydantic Schemas for Request/Response Validation
│   │   ├── ai/              # AI/NLP Natural Language Parsing Module (Interface Stub)
│   │   ├── ml/              # Machine Learning Surplus & Demand Forecasting Module (Interface Stub)
│   │   ├── optimization/    # Google OR-Tools Multi-Point Allocation Solver (Interface Stub)
│   │   └── impact/          # Sustainability Impact Calculator (Direct Recovery Metrics)
│   ├── main.py              # FastAPI Application Entrypoint
│   └── requirements.txt     # Python Dependencies (FastAPI, SQLAlchemy, OR-Tools, Scikit-learn, Pandas, Geopy)
├── frontend/                # React + Vite Application
│   ├── src/
│   │   ├── components/      # UI Navigation, Glassmorphic Cards, Badges
│   │   ├── services/        # Axios API Client (`api.js`)
│   │   ├── App.jsx          # Main Dashboard
│   │   └── index.css        # Modern Dark Glassmorphic Design System
│   └── package.json
├── data/
│   ├── generate_mock_data.py # Mock Data Seeding Script (is_simulated = true)
│   ├── sample_food_surplus.json
│   └── sample_ngo_demands.json
└── README.md
```

---

## 🚀 Quick Start Guide

### 1. Backend Setup & Run

1. Navigate to `backend/` and use the virtual environment:
   ```bash
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   ```
2. Run database migration / seeding script:
   ```bash
   python ..\data\generate_mock_data.py
   ```
3. Launch FastAPI backend dev server:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```
4. Access API Interactive Documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

### 2. Frontend Setup & Run

1. Navigate to `frontend/`:
   ```bash
   cd frontend
   npm install
   ```
2. Start Vite development server:
   ```bash
   npm run dev
   ```
3. Open browser at [http://localhost:5173](http://localhost:5173).

---

## 🔒 Data Transparency & Phase 1 Scope

- **Simulated Data**: All benchmark food surplus and NGO demand records are explicitly tagged with `is_simulated = true`. No claim to live real-world data is made.
- **Defensible Impact Metrics**: Direct food rescued (kg) and meal equivalents are calculated. CO2e emissions avoided and water savings claims are intentionally deferred to Phase 5 after defensible conversion factors are formally established.
- **Model Selection**: Machine learning prediction model selection is deferred to Phase 3 after dataset feature analysis.

---

## 🛠️ Technology Stack
- **Frontend**: React 19, Vite, Lucide Icons, Axios, Leaflet
- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2
- **Optimization**: Google OR-Tools 9.15
- **Data & ML**: Scikit-Learn, Pandas, NumPy, Geopy
- **Database**: SQLite (Zero-config development fallback) / PostgreSQL
