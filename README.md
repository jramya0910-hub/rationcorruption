# Smart Ration Guardian — AI-Powered Public Distribution Monitoring System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)](https://www.postgresql.org/)
[![IBM Cloud](https://img.shields.io/badge/IBM_Cloud-Ready-0062FF)](https://cloud.ibm.com/)

---

## 📌 Overview

**Smart Ration Guardian** monitors India's Public Distribution System (PDS/ration shops), detects fraud using AI, and provides transparency for beneficiaries, shopkeepers, and government officers.

### Key Features
- 🔐 **JWT-based role authentication** — Beneficiary, Shopkeeper, Officer
- 🤖 **AI Fraud Detection** — Isolation Forest anomaly detection
- 📊 **Risk Scoring** — Weighted formula across 4 dimensions
- 📈 **Stock Prediction** — Linear Regression on 6-month history
- 🗣️ **Complaint NLP** — TF-IDF + Naive Bayes auto-categorization
- 📲 **QR Code transactions** — Beneficiary identity verification
- 📉 **Chart.js dashboards** — Bar, Line, Pie charts
- 📤 **PDF/CSV export** — One-click report downloads

---

## 🗂️ Project Structure

```
smart-ration-guardian/
├── frontend/           React + Vite + Chart.js
├── backend/            FastAPI + SQLAlchemy + AI modules
├── database/           init.sql with schema + seed data
└── README.md
```

---

## 🛠️ Prerequisites

| Tool | Version |
|---|---|
| Python | 3.11+ |
| Node.js | 20+ |
| PostgreSQL | 15+ |
| IBM Cloud CLI | latest |

---

## 🚀 Local Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/jramya0910-hub/rationcorruption.git
cd smart-ration-guardian
```

### 2. Database Setup
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE ration_guardian;"

# Run the schema + seed data
psql -U postgres -d ration_guardian -f database/init.sql
```

### 3. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment (copy and edit)
cp .env.example .env
# Edit .env with your DATABASE_URL, JWT_SECRET

# Run the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: **http://localhost:8000/docs**

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Configure API base URL (optional, default uses Vite proxy to :8000)
# Create .env.local:  VITE_API_URL=http://localhost:8000

# Start dev server
npm run dev
```

App available at: **http://localhost:5173**

---

## 🔑 Demo Credentials (Seed Data)

| Role | Username | Password |
|---|---|---|
| Beneficiary | `TN-CHN-001001` | `ben123` |
| Shopkeeper  | `Ravi Ration Shop` | `shop123` |
| Officer     | `officer@tnration.gov.in` | `officer123` |

> **Note:** The seed data uses placeholder bcrypt hashes. To generate real hashes, run:
> ```python
> from passlib.context import CryptContext
> ctx = CryptContext(schemes=["bcrypt"])
> print(ctx.hash("ben123"))
> ```
> Then update the `password_hash` values in `init.sql` and re-run it.

---

## 🤖 AI Modules

### 1. Fraud Detection (`backend/ai/fraud_detection.py`)
- **Algorithm:** Isolation Forest (scikit-learn)
- **Features:** distribution ratio, transactions/day, complaint count, stock mismatch %
- **Output:** anomaly_score (0-1), is_fraud_suspected, reason_text

### 2. Risk Score Calculator (`backend/ai/risk_score.py`)
```
risk_score = (0.35 × fraud_score + 0.25 × complaint_rate + 0.25 × mismatch + 0.15 × velocity) × 100
```
- 0–40 → LOW | 41–70 → MEDIUM | 71–100 → HIGH

### 3. Stock Prediction (`backend/ai/stock_prediction.py`)
- **Algorithm:** Linear Regression on last 6 months of transactions
- **Extra features:** festival month boost (+15%), beneficiary count floor

### 4. Complaint Categorizer (`backend/ai/complaint_nlp.py`)
- **Algorithm:** TF-IDF (bigrams) + Multinomial Naive Bayes
- **Categories:** UNDERWEIGHT, POOR_QUALITY, OVERCHARGING, NOT_AVAILABLE, OTHER

---

## 🌐 API Endpoints

```
POST /auth/login              → JWT token (role-based)
POST /auth/logout

GET  /beneficiary/{id}/entitlement
GET  /beneficiary/{id}/receipts
GET  /beneficiary/{id}/stock-availability
POST /beneficiary/complaint
GET  /beneficiary/{id}/complaints

POST /shop/stock/update
POST /shop/transaction/scan
GET  /shop/{id}/inventory
GET  /shop/{id}/transactions

GET  /officer/dashboard
GET  /officer/alerts
GET  /officer/shops/risk
GET  /officer/complaints
GET  /officer/predictions
GET  /officer/report/export?format=csv|pdf
POST /officer/complaints/resolve

POST /ai/fraud-detection/run
GET  /ai/risk-score/{shop_id}
POST /ai/predict-stock
POST /ai/categorize-complaint
```

---

## ☁️ IBM Cloud Deployment

### Option A: IBM Cloud Code Engine

#### 1. Login and set target
```bash
ibmcloud login --sso
ibmcloud target -r us-south -g Default
ibmcloud ce project create --name ration-guardian
ibmcloud ce project select  --name ration-guardian
```

#### 2. Build & Push Backend (Docker)
```bash
# Create Dockerfile for backend
cat > backend/Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Build using Code Engine
ibmcloud ce build create \
  --name ration-backend-build \
  --source https://github.com/jramya0910-hub/rationcorruption.git \
  --context-dir smart-ration-guardian/backend \
  --strategy dockerfile \
  --image us.icr.io/<namespace>/ration-backend:latest

ibmcloud ce build run --name ration-backend-build
```

#### 3. Deploy Backend Application
```bash
ibmcloud ce app create \
  --name ration-backend \
  --image us.icr.io/<namespace>/ration-backend:latest \
  --port 8000 \
  --env DATABASE_URL="postgresql://user:pass@<ibm-pg-host>:5432/ration_guardian" \
  --env JWT_SECRET="your-production-secret" \
  --env CORS_ORIGINS="https://ration-frontend.<region>.codeengine.appdomain.cloud" \
  --min-scale 1 --max-scale 5

# Get the URL
ibmcloud ce app get --name ration-backend | grep URL
```

#### 4. Build & Deploy Frontend
```bash
# Build frontend
cd frontend && npm run build

# Serve via Code Engine (nginx)
cat > frontend/Dockerfile <<'EOF'
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
EOF

ibmcloud ce app create \
  --name ration-frontend \
  --image us.icr.io/<namespace>/ration-frontend:latest \
  --port 80 \
  --min-scale 1
```

---

### Option B: IBM Cloud Foundry

```bash
# Backend manifest.yml
cat > backend/manifest.yml <<'EOF'
applications:
  - name: ration-guardian-api
    command: uvicorn main:app --host 0.0.0.0 --port $PORT
    buildpacks:
      - python_buildpack
    memory: 512M
    env:
      DATABASE_URL: "postgresql://..."
      JWT_SECRET: "change-me"
EOF

cd backend
ibmcloud cf push

# Frontend — static buildpack
cat > frontend/manifest.yml <<'EOF'
applications:
  - name: ration-guardian-ui
    buildpacks:
      - staticfile_buildpack
    path: dist
    memory: 64M
EOF

cd frontend && npm run build
ibmcloud cf push
```

---

### IBM Databases for PostgreSQL

```bash
# Provision managed PostgreSQL on IBM Cloud
ibmcloud resource service-instance-create ration-pg \
  databases-for-postgresql standard us-south

# Get credentials
ibmcloud resource service-key-create ration-pg-key Editor \
  --instance-name ration-pg

# Connect and run init.sql
ibmcloud cdb deployment-connections ration-pg
psql "<connection-string>" -f database/init.sql
```

---

## 🔧 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/ration_guardian` |
| `JWT_SECRET` | Secret key for JWT signing | (required) |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token expiry | `480` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |
| `APP_ENV` | `development` or `production` | `development` |

---

## 📋 Database Schema Summary

| Table | Description |
|---|---|
| `beneficiaries` | PDS card holders with entitlement data |
| `shops` | Ration shops with risk scores |
| `stock_inventory` | Per-shop grain stock tracking |
| `transactions` | Distribution records (QR verified) |
| `complaints` | Beneficiary grievances with AI category |
| `fraud_alerts` | AI-generated fraud flags |
| `stock_predictions` | ML demand forecast per shop/grain |
| `officers` | Government monitoring officers |

---

## 📜 License

MIT License — © 2024 Smart Ration Guardian Project
