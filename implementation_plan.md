# Implementation Plan - ReSource: Predictive Circular Resource Intelligence Network

ReSource is a software-only circular economy platform designed to reduce resource waste by predicting surplus and unmet demand, intelligently matching compatible supply-demand pairs, optimizing multi-point allocations under real-world constraints, and measuring defensible sustainability impact. 

The initial MVP focuses on **Food Surplus** from commercial suppliers (restaurants, hotels, events, institutions) to verified receivers (NGOs, food banks, community shelters), built with an extensible architecture to support additional resource categories (e.g., electronics, textiles, medical supplies) in future iterations.

---

## Technical Stack Architecture

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React + Vite, Tailwind CSS / Vanilla CSS, Leaflet, Recharts | Dynamic interactive UI, live allocation map, natural language input, impact dashboard |
| **Backend** | Python 3.12, FastAPI, Pydantic v2 | High-performance RESTful API, asynchronous task handling, domain service orchestration |
| **Database** | PostgreSQL (with SQLite zero-config dev fallback), SQLAlchemy 2.0 | Entity relation storage, historical metrics, geospatial coordinates |
| **AI / NLP** | Python (`spacy` / `transformers` / regex rule pipeline with LLM abstraction) | Converts raw natural language notes into structured resource specs |
| **ML Engine** | Python (`scikit-learn`, `pandas`) | Forecasts future surplus generation and demand spikes based on historical patterns |
| **Optimization** | Google OR-Tools (`ortools.linear_solver`) | Solves multi-facility supply-demand matching optimization under distance & perishability constraints |
| **Impact Engine** | Python custom environmental model | Calculates food rescued (kg), meal equivalents, $\text{CO}_2\text{e}$ avoided, and water saved |

---

## User Review Required

> [!IMPORTANT]
> **Extensible Domain Model**: The schema uses abstract category interfaces with food-specific metadata attributes, allowing seamless future expansion to non-food resource categories without changing core optimization APIs.

> [!NOTE]
> **AI/ML Technical Integrity**: The AI component combines a deterministic NLP fallback parser (works out-of-the-box offline without API keys) with an extensible LLM provider wrapper, ensuring a genuine technical component for students to run, test, and demonstrate seamlessly.

---

## Folder Structure

```
ReSource HG/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py
│   │   │       │   ├── suppliers.py
│   │   │       │   ├── receivers.py
│   │   │       │   ├── surplus.py
│   │   │       │   ├── demand.py
│   │   │       │   ├── matching.py
│   │   │       │   ├── optimization.py
│   │   │       │   ├── prediction.py
│   │   │       │   └── impact.py
│   │   │       └── router.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/           # SQLAlchemy DB Models
│   │   │   ├── organization.py
│   │   │   ├── category.py
│   │   │   ├── surplus.py
│   │   │   ├── demand.py
│   │   │   ├── allocation.py
│   │   │   └── impact.py
│   │   ├── schemas/          # Pydantic Schemas
│   │   │   ├── surplus.py
│   │   │   ├── demand.py
│   │   │   ├── match.py
│   │   │   └── allocation.py
│   │   ├── ai/               # NLP Natural Language Extraction
│   │   │   ├── nlp_parser.py
│   │   │   └── llm_provider.py
│   │   ├── ml/               # Machine Learning Predictors
│   │   │   ├── surplus_predictor.py
│   │   │   └── demand_predictor.py
│   │   ├── optimization/     # Google OR-Tools Allocation Solver
│   │   │   ├── allocation_solver.py
│   │   │   └── distance.py
│   │   └── impact/           # Sustainability Metrics Calculator
│   │       └── impact_calculator.py
│   ├── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/       # Navbar, Status Badges, Cards
│   │   │   ├── map/          # Leaflet Allocation & Proximity Map
│   │   │   ├── dashboard/    # Impact Widgets & Prediction Charts
│   │   │   └── forms/        # NLP Intake Forms
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── SurplusListings.jsx
│   │   │   ├── DemandListings.jsx
│   │   │   ├── MatchOptimization.jsx
│   │   │   └── AnalyticsImpact.jsx
│   │   ├── services/
│   │   │   └── api.js        # Axios API Client
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── data/
│   ├── sample_food_surplus.json
│   ├── sample_ngo_demands.json
│   └── generate_mock_data.py
└── README.md
```

---

## Proposed Database Entities (PostgreSQL Schema)

1. **`organizations`**: ID, Name, Type (RESTAURANT, HOTEL, NGO, SHELTER), Address, Latitude, Longitude, Contact, Is_Verified.
2. **`categories`**: ID, Name ("Food Surplus", "Produce", "Cooked"), Unit (KG, PORTIONS), CO2_Factor_Per_Unit.
3. **`surplus_listings`**: ID, Supplier_ID, Category_ID, Title, Raw_NLP_Text, Quantity, Storage_Condition (AMBIENT, REFRIGERATED, FROZEN), Perishability_Hours, Expires_At, Status, Is_Simulated.
4. **`demand_listings`**: ID, Receiver_ID, Category_ID, Title, Raw_NLP_Text, Requested_Quantity, Fulfilled_Quantity, Urgency_Level (LOW, MEDIUM, HIGH, CRITICAL), Required_By, Status, Is_Simulated.
5. **`allocations`**: ID, Surplus_ID, Demand_ID, Allocated_Quantity, Match_Score, Distance_KM, Status, Created_At.
6. **`impact_logs`**: ID, Allocation_ID, Food_Rescued_KG, Meals_Provided, CO2_Avoided_KG, Water_Saved_Liters, Calculated_At.
7. **`predictions`**: ID, Organization_ID, Prediction_Type, Target_Date, Predicted_Quantity, Confidence_Score.

---

## Core Module Communication Flow

```
[ Frontend (React) ]
       │  API REST requests
       ▼
[ FastAPI Backend Router ]
       │
       ├─► AI/NLP Module ───────► Natural Language Entity Parsing (Text -> Structured Listing)
       ├─► ML Engine ───────────► Time-Series Surplus & Demand Forecasting (Historical -> Predictions)
       ├─► Matching Engine ─────► Pairwise Compatibility Scoring (Perishability, Urgency, Distance)
       ├─► OR-Tools Solver ─────► Multi-Point Constraint Allocation Optimization (MILP Solver)
       └─► Impact Engine ───────► Defensible Sustainability Metric Calculations (Rescued kg -> CO2e / Meals)
```

---

## Development Phases

### Phase 1: Architecture & Foundation Setup
- Setup repository root structure (`backend/`, `frontend/`, `data/`).
- Initialize Python environment with dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `ortools`, `scikit-learn`, `pandas`, `geopy`).
- Create database configuration & initial SQLite/PostgreSQL schema models.
- Scaffold React + Vite application with modern glassmorphism design system & navigation.
- Implement mock data generator (`generate_mock_data.py`) with simulated suppliers, receivers, surplus items, and demands (labeled `is_simulated: true`).

### Phase 2: AI/NLP Parser & Core Listing APIs
- Implement Python NLP parser (`nlp_parser.py`) extracting quantity, unit, perishability hours, and storage needs from unstructured text.
- Build REST APIs for Organizations, Surplus Listings, and Demand Listings.
- Create Frontend intake forms featuring live natural language input parsing.

### Phase 3: ML Prediction & Compatibility Matching Engine
- Implement ML predictor (`surplus_predictor.py`) using scikit-learn regression models for predicting future surplus generation based on day of week and event size.
- Build transparent pairwise matching service (`matching.py`) generating dynamic match scores based on distance, time-to-expiry, dietary category, and quantity.
- Build Frontend Match Explorer with score breakdown details.

### Phase 4: OR-Tools Multi-Point Optimization Engine
- Implement OR-Tools MILP constraint optimization algorithm (`allocation_solver.py`) optimizing total resource redistribution while respecting expiry, transit distance, and NGO capacity limits.
- Build interactive Allocation Route Map in Frontend using Leaflet.js.

### Phase 5: Defensible Impact Analytics & Verification
- Implement Sustainability Impact Engine (`impact_calculator.py`) calculating food rescued, meals served, $\text{CO}_2\text{e}$ avoided, and water saved.
- Build Executive Impact Dashboard with dynamic visualizations and summary reports.
- Comprehensive end-to-end testing and documentation.

---

## Verification Plan

### Automated Verification
- **Backend API Tests**: Run `pytest` to test FastAPI endpoint response codes, NLP parsing accuracy, and OR-Tools optimization constraint satisfaction.
- **Frontend Build Verification**: Run `npm run build` to verify clean JSX compilation and asset bundling.

### Manual Verification
- Test natural language entry parsing with varied user text strings.
- Verify OR-Tools solver produces feasible allocations with 0 constraint violations.
- Verify Leaflet map renders supply/demand pins and allocation connections properly.
