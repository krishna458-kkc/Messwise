# MessWise

**AI Food-Operations Intelligence for Institutional Kitchens**

> **Predict • Plan • Cook • Measure • Learn • Save**  
> Prevent surplus before it is cooked — prove the savings with real kitchen data.

---

## 📌 Project Overview & Purpose

Hostel messes, university canteens, hospital kitchens, and bulk caterers prepare hundreds of meals daily without accurate headcount estimates or measured leftover tracking. Because running short creates immediate friction while wasting food is silent, institutional kitchens consistently overproduce by habit.

**MessWise** closes this operational gap through a feedback loop:
1. **Predict**: Meal-wise headcount forecasting with conformal uncertainty bands.
2. **Plan**: Dish quantities planned at manager-controlled service levels using Newsvendor optimization.
3. **Cook**: Kitchen staff cook to plan or log human overrides with clear reasons.
4. **Measure**: Leftovers and run-outs recorded in seconds (form, voice, calibrated bin photo, or smart scale).
5. **Learn**: Shortage-aware (Kaplan–Meier) appetite rates update models meal-by-meal.

---

## 🚀 Development Status: Step 8 Complete (Voice Logging C5, CO₂e H1, Meals-Eq H2, Green-Campus PDF H4)

Per the master build-ladder in [`PLAN.md`](PLAN.md), the system implements **Step 8**, extending the closed-loop workflow:
$$\text{PREDICT} \longrightarrow \text{PLAN} \longrightarrow \text{COOK} \longrightarrow \text{MEASURE} \longrightarrow \text{LEARN}$$

### 1. Multilingual Voice Logging (Module C: C5)
- **Speech Capture & Transcription**: Practical speech-recognition adapter (`SpeechRecognition` with local audio processing or Google Speech API).
- **Rule-Based Slot Parsing**: Reusable parser extracting dish name, cooked quantity, unit, leftover quantity, and ran-out cues across English, Hindi, and Telugu transliteration (`annam 40 kilolu vandamu, 6 kilolu migilindi`).
- **Privacy & Pre-Commit Review**: Temporary audio disposal; raw audio is never permanently stored. Measurements require explicit human review and confirmation before database persistence.

### 2. Environmental & Social Impact Intelligence (Module H: H1, H2, H4)
- **H1. CO₂e Impact Estimation**: Peer-reviewed greenhouse-gas emissions mitigation calculated on verified food avoided using lifecycle uncertainty bands (Low 2.2, Central 2.5, High 3.4 kg CO₂e / kg food waste; *Sustainability 2021*, *Energies 2021*).
- **H2. Meals-Equivalent Impact**: Translates avoided food into illustrative student meal equivalents using learned per-head consumption rates (~0.35 kg/meal).
- **H4. Green-Campus PDF Report**: One-click, in-memory downloadable PDF report ([`messwise/pdf_report.py`](messwise/pdf_report.py)) incorporating executive summary tables, GHG emission bands, meals-equivalent metrics, and Zero-Hunger shortage safeguards.

### 3. Data Honesty & Synthetic Separation
- **Strict Isolation**: Zero real pilot records produce an honest *Data Collection in Progress* state rather than fabricating zero or positive savings.
- **Prominent Labelling**: All synthetic demonstration dashboards and PDF reports carry prominent warnings: `[!] SYNTHETIC DEMONSTRATION -- NOT REAL-WORLD IMPACT`.

---

## 🛠️ Technology Stack

- **Language & Runtime**: Python 3.11+
- **Data & Forecasting**: pandas, NumPy, scikit-learn / pure NumPy regularized Ridge
- **Database & ORM**: SQLite, SQLAlchemy 2.0+
- **Web API**: FastAPI, Pydantic v2, Uvicorn
- **User Interface**: Streamlit, Plotly
- **Testing**: pytest, HTTPX

---

## 📁 Project Structure

```text
Messwise/
├── api/
│   ├── __init__.py
│   └── main.py                     # FastAPI service (/health, /forecast, /plan, /prediction-log, /meals)
├── app/
│   ├── Home.py                     # Streamlit application entry point
│   └── pages/
│       ├── Kitchen.py              # Functional kitchen measurement entry
│       ├── Forecast_Lab.py         # [Step 2] Operational forecasting intelligence
│       ├── Planner.py              # [Step 3] Cooking quantity planner & optimiser
│       ├── Simulator.py            # [Phase 4 Placeholder] Counterfactual savings replay
│       ├── Waste_Intelligence.py   # [Phase 4 Placeholder] Waste analytics & root-cause
│       ├── Impact.py               # [Phase 4 Placeholder] Measured savings & CO2e bands
│       └── Reports.py              # Live audit log & institutional governance
├── data/
│   ├── raw/                        # Reserved strictly for verified kitchen pilot data
│   ├── interim/                    # Processed / staged data
│   └── synthetic/                  # Synthetic development datasets (is_synthetic = 1)
├── messwise/
│   ├── __init__.py
│   ├── db.py                       # SQLAlchemy models, SQLite connection, prediction linking, plan persistence
│   ├── forecast.py                 # Core forecasting engine, baselines, conformal intervals
│   ├── planner.py                  # [Step 3] Quantity planner, consumption learning, service-level math
│   └── validation.py               # Shared Pydantic models & validation rules
├── scripts/
│   └── synth_data.py               # Synthetic development data generator
├── tests/
│   ├── test_api.py                 # FastAPI endpoint tests (including /plan)
│   ├── test_db.py                  # Database schema & synthetic flag tests
│   ├── test_forecast.py            # Forecasting engine tests (A1–A6 & E1)
│   ├── test_planner.py             # 18 comprehensive tests for B1–B3 planning engine
│   └── test_validation.py          # Data validation rule tests
├── requirements.txt                # Project dependencies
├── PLAN.md                         # Master 40-page project documentation
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Prerequisites
Ensure Python 3.11+ is installed.

### 2. Virtual Environment Setup
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Populate Development Data (Optional)
Generate 14 days of realistic synthetic test records:
```bash
python scripts/synth_data.py --days 14 --db
```

---

## 🏃 How to Run

### 1. Start the React 19 / Vite Frontend (New Dedicated Application)
```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 3000
```
- **Product Landing Page & Operational Workspace**: [http://localhost:3000](http://localhost:3000)
- Proxies `/api` requests directly to FastAPI at `http://127.0.0.1:8000`.
- Built with React 19, TypeScript, Vite, Tailwind CSS v4, and Framer Motion.
- Complete documentation: [`docs/FRONTEND_DESIGN_SYSTEM.md`](docs/FRONTEND_DESIGN_SYSTEM.md) and [`docs/FRONTEND_PARITY_AUDIT.md`](docs/FRONTEND_PARITY_AUDIT.md).

### 2. Start the FastAPI Service
```bash
python -m uvicorn api.main:app --reload --port 8000
```
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **Forecast API**: `GET /forecast?date=2026-10-15&days=1&hostel_strength=500&is_synthetic=1`
- **Waste Intelligence**: `GET /intelligence/summary?is_synthetic=1`
- **Environment Summary**: `GET /environment/summary`

### 3. Start the Preserved Streamlit Application (Functional Fallback)
```bash
python -m streamlit run app/Home.py --server.port 8501
```
- **Streamlit Workspace**: [http://localhost:8501](http://localhost:8501)
- Preserved as a functional fallback sharing the exact same SQLite database (`data/messwise.db`).

### 4. Run Automated Tests
```bash
# Python backend & integrity test suite (248 passing tests)
pytest tests/ -v

# React frontend build & typecheck
cd frontend && npm run build
```

---

## 🌐 Production Deployment (Vercel + Render)

MessWise is configured for cloud production deployment:
- **Frontend (Vercel):** React + Vite SPA. Set Root Directory to `frontend`, output to `dist`, and define `VITE_API_URL`.
- **Backend (Render):** FastAPI service. Auto-configured via [`render.yaml`](render.yaml) with `/health` check and CORS regex.
- **Database:** Fully supports both PostgreSQL (via `DATABASE_URL`) and persistent SQLite (via `MESSWISE_DB_PATH`). Includes safe non-destructive migration utility [`scripts/migrate_to_postgres.py`](scripts/migrate_to_postgres.py).

See the complete step-by-step instructions in [`DEPLOYMENT.md`](DEPLOYMENT.md).