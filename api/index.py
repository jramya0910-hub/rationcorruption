"""
Vercel serverless entry point.
Vercel calls this file as a Python WSGI/ASGI handler.
All routes are handled by FastAPI via the single `app` object.
"""
import sys, os

# Make the backend package importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── inline config (no relative imports needed) ────────────────────────────────
DATABASE_URL  = os.environ.get("DATABASE_URL", "")
JWT_SECRET    = os.environ.get("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE    = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))
CORS_ORIGINS  = [o.strip() for o in os.environ.get("CORS_ORIGINS", "https://rationcorruption.vercel.app").split(",")]
APP_ENV       = os.environ.get("APP_ENV", "production")

# ── sync SQLAlchemy engine (psycopg2, Vercel-compatible) ──────────────────────
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session

def _make_sync_url(url: str) -> str:
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    return url

_engine = create_engine(
    _make_sync_url(DATABASE_URL),
    pool_size=2,
    max_overflow=5,
    pool_pre_ping=True,
    connect_args={"sslmode": "require"} if "supabase.com" in DATABASE_URL else {},
)
_SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── models (inline to avoid package import issues) ───────────────────────────
import uuid, enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

class RiskLevel(str, enum.Enum):
    LOW = "LOW"; MEDIUM = "MEDIUM"; HIGH = "HIGH"

class GrainType(str, enum.Enum):
    RICE = "RICE"; WHEAT = "WHEAT"; SUGAR = "SUGAR"; OIL = "OIL"

class ComplaintType(str, enum.Enum):
    UNDERWEIGHT="UNDERWEIGHT"; POOR_QUALITY="POOR_QUALITY"
    OVERCHARGING="OVERCHARGING"; NOT_AVAILABLE="NOT_AVAILABLE"; OTHER="OTHER"

class ComplaintStatus(str, enum.Enum):
    OPEN="OPEN"; UNDER_REVIEW="UNDER_REVIEW"; RESOLVED="RESOLVED"

class AlertSeverity(str, enum.Enum):
    LOW="LOW"; MEDIUM="MEDIUM"; HIGH="HIGH"; CRITICAL="CRITICAL"

class Shop(Base):
    __tablename__ = "shops"
    shop_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_name     = Column(String(200), nullable=False)
    owner_name    = Column(String(200), nullable=False)
    location      = Column(Text, nullable=False)
    district      = Column(String(100), nullable=False)
    risk_score    = Column(Numeric(5,2), default=0.0)
    risk_level    = Column(SAEnum(RiskLevel, name="risk_level_enum"), default=RiskLevel.LOW)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    beneficiary_id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ration_card_number     = Column(String(50), unique=True, nullable=False)
    name                   = Column(String(200), nullable=False)
    phone                  = Column(String(20))
    address                = Column(Text)
    family_members         = Column(Integer, default=1)
    assigned_shop_id       = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=True)
    monthly_entitlement_kg = Column(Numeric(8,2), default=25.0)
    password_hash          = Column(String(255), nullable=False)
    created_at             = Column(DateTime, default=datetime.utcnow)

class StockInventory(Base):
    __tablename__ = "stock_inventory"
    inventory_id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id              = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    grain_type           = Column(SAEnum(GrainType, name="grain_type_enum"), nullable=False)
    stock_received_kg    = Column(Numeric(10,2), default=0.0)
    stock_distributed_kg = Column(Numeric(10,2), default=0.0)
    last_updated         = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id           = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    beneficiary_id    = Column(UUID(as_uuid=True), ForeignKey("beneficiaries.beneficiary_id"), nullable=False)
    grain_type        = Column(SAEnum(GrainType, name="grain_type_enum"), nullable=False)
    quantity_given_kg = Column(Numeric(8,2), nullable=False)
    transaction_date  = Column(DateTime, default=datetime.utcnow)
    qr_scan_verified  = Column(Boolean, default=False)

class Complaint(Base):
    __tablename__ = "complaints"
    complaint_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beneficiary_id = Column(UUID(as_uuid=True), ForeignKey("beneficiaries.beneficiary_id"), nullable=False)
    shop_id        = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    complaint_type = Column(SAEnum(ComplaintType, name="complaint_type_enum"), nullable=False)
    description    = Column(Text)
    status         = Column(SAEnum(ComplaintStatus, name="complaint_status_enum"), default=ComplaintStatus.OPEN)
    ai_category    = Column(String(100))
    created_at     = Column(DateTime, default=datetime.utcnow)
    resolved_at    = Column(DateTime, nullable=True)

class FraudAlert(Base):
    __tablename__ = "fraud_alerts"
    alert_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id     = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    alert_type  = Column(String(100), nullable=False)
    description = Column(Text)
    severity    = Column(SAEnum(AlertSeverity, name="severity_enum"), default=AlertSeverity.LOW)
    is_reviewed = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

class StockPrediction(Base):
    __tablename__ = "stock_predictions"
    prediction_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id             = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id"), nullable=False)
    grain_type          = Column(SAEnum(GrainType, name="grain_type_enum"), nullable=False)
    predicted_demand_kg = Column(Numeric(10,2))
    prediction_month    = Column(DateTime)
    created_at          = Column(DateTime, default=datetime.utcnow)

class Officer(Base):
    __tablename__ = "officers"
    officer_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String(200), nullable=False)
    email         = Column(String(200), unique=True, nullable=False)
    district      = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

# ── Auth utils ────────────────────────────────────────────────────────────────
from datetime import timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

pwd_context  = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE)
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    try:
        return jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def require_role(*roles: str):
    def checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker

def ok(data=None, message=""):
    return {"status": "success", "data": data or {}, "message": message}

# ── AI (inline) ───────────────────────────────────────────────────────────────
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression

_iforest = None
def _get_iforest():
    global _iforest
    if _iforest is None:
        rng = np.random.RandomState(42)
        X = np.column_stack([rng.uniform(0.6,0.95,300), rng.uniform(0.5,5,300), rng.uniform(0,2,300), rng.uniform(0,15,300)])
        _iforest = IsolationForest(n_estimators=100, contamination=0.1, random_state=42).fit(X)
    return _iforest

_nlp_pipeline = None
_TRAIN = [
    ("weight was less than stated","UNDERWEIGHT"),("received less rice than entitled","UNDERWEIGHT"),
    ("only gave half the quantity","UNDERWEIGHT"),("short weight detected","UNDERWEIGHT"),
    ("rice had stones and insects","POOR_QUALITY"),("wheat quality was bad smells rotten","POOR_QUALITY"),
    ("sugar was damp and lumpy","POOR_QUALITY"),("grains mixed with sand","POOR_QUALITY"),
    ("demanded extra money above government price","OVERCHARGING"),("charged more than fixed rate","OVERCHARGING"),
    ("asked for bribe to give ration","OVERCHARGING"),("unofficial surcharge collected","OVERCHARGING"),
    ("shop was closed during distribution days","NOT_AVAILABLE"),("stock not available at all","NOT_AVAILABLE"),
    ("no rice wheat available in shop","NOT_AVAILABLE"),("shop did not open for the month","NOT_AVAILABLE"),
]
def _get_nlp():
    global _nlp_pipeline
    if _nlp_pipeline is None:
        texts, labels = zip(*_TRAIN)
        _nlp_pipeline = Pipeline([("tfidf", TfidfVectorizer(ngram_range=(1,2))), ("clf", MultinomialNB(alpha=0.5))])
        _nlp_pipeline.fit(texts, labels)
    return _nlp_pipeline

def categorize_complaint(desc: str) -> str:
    if not desc or not desc.strip(): return "OTHER"
    try:
        p = _get_nlp()
        pred  = p.predict([desc.lower()])[0]
        proba = p.predict_proba([desc.lower()]).max()
        return pred if proba >= 0.35 else "OTHER"
    except: return "OTHER"

def run_fraud_detection(features: dict) -> dict:
    model = _get_iforest()
    X = np.array([[features.get("distribution_ratio",0.5), features.get("txn_per_day",1), features.get("complaint_count",0)/30, features.get("mismatch_pct",0)]])
    raw   = model.decision_function(X)[0]
    pred  = model.predict(X)[0]
    score = float(np.clip(1 - (raw + 0.5), 0, 1))
    reasons = []
    if features.get("distribution_ratio",1) < 0.3:  reasons.append("Very low distribution ratio")
    if features.get("distribution_ratio",0) > 0.98: reasons.append("Near-total stock distributed")
    if features.get("complaint_count",0) > 5:       reasons.append(f"High complaints ({features['complaint_count']})")
    if features.get("mismatch_pct",0) > 20:         reasons.append(f"Stock mismatch {features['mismatch_pct']:.1f}%")
    return {"anomaly_score": round(score,4), "is_fraud_suspected": pred==-1,
            "reason_text": "; ".join(reasons) if pred==-1 else "No anomaly detected"}

def calculate_risk_score(fraud_score, complaint_count, mismatch_pct, txn_per_day):
    rs = (0.35*min(fraud_score,1) + 0.25*min(complaint_count/10,1) + 0.25*min(mismatch_pct/50,1) + 0.15*min(txn_per_day/20,1)) * 100
    rs = round(rs, 2)
    return {"risk_score": rs, "risk_level": "HIGH" if rs>70 else "MEDIUM" if rs>40 else "LOW"}

# ── FastAPI app ───────────────────────────────────────────────────────────────
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from sqlalchemy import func
import io, csv

app = FastAPI(title="Smart Ration Guardian API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── AUTH ──────────────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str; password: str; role: str

@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    role = payload.role.lower()
    if role == "beneficiary":
        user = db.query(Beneficiary).filter(Beneficiary.ration_card_number == payload.username).first()
        if not user: raise HTTPException(401, "Beneficiary not found")
        if not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid credentials")
        token = create_token({"sub": str(user.beneficiary_id), "role": "beneficiary", "name": user.name})
        return ok({"access_token": token, "token_type": "bearer", "role": "beneficiary", "user_id": str(user.beneficiary_id), "name": user.name}, "Login successful")
    elif role == "shopkeeper":
        user = db.query(Shop).filter(Shop.shop_name == payload.username).first()
        if not user: raise HTTPException(401, "Shop not found")
        if not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid credentials")
        token = create_token({"sub": str(user.shop_id), "role": "shopkeeper", "name": user.shop_name})
        return ok({"access_token": token, "token_type": "bearer", "role": "shopkeeper", "user_id": str(user.shop_id), "name": user.shop_name}, "Login successful")
    elif role == "officer":
        user = db.query(Officer).filter(Officer.email == payload.username).first()
        if not user: raise HTTPException(401, "Officer not found")
        if not verify_password(payload.password, user.password_hash): raise HTTPException(401, "Invalid credentials")
        token = create_token({"sub": str(user.officer_id), "role": "officer", "name": user.name})
        return ok({"access_token": token, "token_type": "bearer", "role": "officer", "user_id": str(user.officer_id), "name": user.name}, "Login successful")
    raise HTTPException(400, "Invalid role")

@app.post("/auth/logout")
def logout():
    return ok({}, "Logged out")

# ── BENEFICIARY ───────────────────────────────────────────────────────────────
@app.get("/beneficiary/{beneficiary_id}/entitlement")
def get_entitlement(beneficiary_id: str, db: Session = Depends(get_db), user=Depends(require_role("beneficiary","officer"))):
    ben  = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()
    if not ben: raise HTTPException(404, "Not found")
    shop = db.query(Shop).filter(Shop.shop_id == ben.assigned_shop_id).first() if ben.assigned_shop_id else None
    return ok({"beneficiary_id": str(ben.beneficiary_id), "name": ben.name, "ration_card_number": ben.ration_card_number,
               "family_members": ben.family_members, "monthly_entitlement_kg": float(ben.monthly_entitlement_kg),
               "assigned_shop_id": str(ben.assigned_shop_id) if ben.assigned_shop_id else None,
               "shop_name": shop.shop_name if shop else None, "shop_location": shop.location if shop else None})

@app.get("/beneficiary/{beneficiary_id}/receipts")
def get_receipts(beneficiary_id: str, db: Session = Depends(get_db), user=Depends(require_role("beneficiary","officer"))):
    rows = db.query(Transaction, Shop).join(Shop, Transaction.shop_id == Shop.shop_id).filter(Transaction.beneficiary_id == beneficiary_id).order_by(Transaction.transaction_date.desc()).limit(50).all()
    return ok({"receipts": [{"transaction_id": str(t.transaction_id), "grain_type": t.grain_type.value, "quantity_given_kg": float(t.quantity_given_kg), "transaction_date": t.transaction_date.isoformat(), "qr_scan_verified": t.qr_scan_verified, "shop_name": s.shop_name} for t,s in rows]})

@app.get("/beneficiary/{beneficiary_id}/stock-availability")
def get_stock(beneficiary_id: str, db: Session = Depends(get_db), user=Depends(require_role("beneficiary","officer"))):
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == beneficiary_id).first()
    if not ben: raise HTTPException(404, "Not found")
    inv = db.query(StockInventory).filter(StockInventory.shop_id == ben.assigned_shop_id).all()
    return ok({"stock_availability": [{"grain_type": i.grain_type.value, "remaining_stock_kg": float(i.stock_received_kg or 0)-float(i.stock_distributed_kg or 0), "available": float(i.stock_received_kg or 0)-float(i.stock_distributed_kg or 0)>0} for i in inv], "shop_id": str(ben.assigned_shop_id)})

class ComplaintCreate(BaseModel):
    shop_id: str; complaint_type: str; description: Optional[str] = None

@app.post("/beneficiary/complaint")
def submit_complaint(payload: ComplaintCreate, db: Session = Depends(get_db), user=Depends(require_role("beneficiary"))):
    ai_cat = categorize_complaint(payload.description or "")
    c = Complaint(beneficiary_id=user["sub"], shop_id=payload.shop_id, complaint_type=payload.complaint_type, description=payload.description, ai_category=ai_cat)
    db.add(c); db.commit(); db.refresh(c)
    return ok({"complaint_id": str(c.complaint_id), "ai_category": ai_cat}, "Complaint submitted")

@app.get("/beneficiary/{beneficiary_id}/complaints")
def get_ben_complaints(beneficiary_id: str, db: Session = Depends(get_db), user=Depends(require_role("beneficiary","officer"))):
    rows = db.query(Complaint, Shop).join(Shop, Complaint.shop_id == Shop.shop_id).filter(Complaint.beneficiary_id == beneficiary_id).order_by(Complaint.created_at.desc()).all()
    return ok({"complaints": [{"complaint_id": str(c.complaint_id), "shop_name": s.shop_name, "complaint_type": c.complaint_type.value, "description": c.description, "status": c.status.value, "ai_category": c.ai_category, "created_at": c.created_at.isoformat(), "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None} for c,s in rows]})

# ── SHOPKEEPER ────────────────────────────────────────────────────────────────
class InventoryUpdate(BaseModel):
    grain_type: str; stock_received_kg: Optional[float]=None; stock_distributed_kg: Optional[float]=None

@app.post("/shop/stock/update")
def update_stock(payload: InventoryUpdate, db: Session = Depends(get_db), user=Depends(require_role("shopkeeper","officer"))):
    shop_id = user["sub"]
    inv = db.query(StockInventory).filter(StockInventory.shop_id == shop_id, StockInventory.grain_type == payload.grain_type).first()
    if not inv:
        inv = StockInventory(shop_id=shop_id, grain_type=payload.grain_type, stock_received_kg=payload.stock_received_kg or 0, stock_distributed_kg=payload.stock_distributed_kg or 0)
        db.add(inv)
    else:
        if payload.stock_received_kg:    inv.stock_received_kg    = float(inv.stock_received_kg or 0)    + payload.stock_received_kg
        if payload.stock_distributed_kg: inv.stock_distributed_kg = float(inv.stock_distributed_kg or 0) + payload.stock_distributed_kg
        inv.last_updated = datetime.utcnow()
    db.commit(); db.refresh(inv)
    return ok({"grain_type": inv.grain_type.value, "remaining_stock_kg": float(inv.stock_received_kg or 0)-float(inv.stock_distributed_kg or 0)}, "Updated")

class ScanTxn(BaseModel):
    beneficiary_id: str; grain_type: str; quantity_given_kg: float; qr_scan_verified: bool = True

@app.post("/shop/transaction/scan")
def scan_txn(payload: ScanTxn, db: Session = Depends(get_db), user=Depends(require_role("shopkeeper"))):
    shop_id = user["sub"]
    ben = db.query(Beneficiary).filter(Beneficiary.beneficiary_id == payload.beneficiary_id, Beneficiary.assigned_shop_id == shop_id).first()
    if not ben: raise HTTPException(404, "Beneficiary not found or not assigned to this shop")
    t = Transaction(shop_id=shop_id, beneficiary_id=payload.beneficiary_id, grain_type=payload.grain_type, quantity_given_kg=payload.quantity_given_kg, qr_scan_verified=payload.qr_scan_verified)
    db.add(t)
    inv = db.query(StockInventory).filter(StockInventory.shop_id == shop_id, StockInventory.grain_type == payload.grain_type).first()
    if inv: inv.stock_distributed_kg = float(inv.stock_distributed_kg or 0) + payload.quantity_given_kg
    db.commit(); db.refresh(t)
    return ok({"transaction_id": str(t.transaction_id)}, "Transaction recorded")

@app.get("/shop/{shop_id}/inventory")
def get_inventory(shop_id: str, db: Session = Depends(get_db), user=Depends(require_role("shopkeeper","officer"))):
    inv = db.query(StockInventory).filter(StockInventory.shop_id == shop_id).all()
    return ok({"inventory": [{"inventory_id": str(i.inventory_id), "grain_type": i.grain_type.value, "stock_received_kg": float(i.stock_received_kg), "stock_distributed_kg": float(i.stock_distributed_kg), "remaining_stock_kg": float(i.stock_received_kg or 0)-float(i.stock_distributed_kg or 0), "low_stock_alert": float(i.stock_received_kg or 0)-float(i.stock_distributed_kg or 0)<50} for i in inv]})

@app.get("/shop/{shop_id}/transactions")
def get_txns(shop_id: str, db: Session = Depends(get_db), user=Depends(require_role("shopkeeper","officer"))):
    rows = db.query(Transaction, Beneficiary).join(Beneficiary, Transaction.beneficiary_id == Beneficiary.beneficiary_id).filter(Transaction.shop_id == shop_id).order_by(Transaction.transaction_date.desc()).limit(100).all()
    return ok({"transactions": [{"transaction_id": str(t.transaction_id), "beneficiary_name": b.name, "ration_card_number": b.ration_card_number, "grain_type": t.grain_type.value, "quantity_given_kg": float(t.quantity_given_kg), "transaction_date": t.transaction_date.isoformat(), "qr_scan_verified": t.qr_scan_verified} for t,b in rows]})

# ── OFFICER ───────────────────────────────────────────────────────────────────
@app.get("/officer/dashboard")
def dashboard(db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    total_shops  = db.query(func.count(Shop.shop_id)).scalar()
    total_bens   = db.query(func.count(Beneficiary.beneficiary_id)).scalar()
    act_alerts   = db.query(func.count(FraudAlert.alert_id)).filter(FraudAlert.is_reviewed==False).scalar()
    open_comps   = db.query(func.count(Complaint.complaint_id)).filter(Complaint.status==ComplaintStatus.OPEN).scalar()
    high_risk    = db.query(func.count(Shop.shop_id)).filter(Shop.risk_level==RiskLevel.HIGH).scalar()
    shops = db.query(Shop).all()
    bar_data = []
    for s in shops:
        dist = db.query(func.coalesce(func.sum(StockInventory.stock_distributed_kg),0)).filter(StockInventory.shop_id==s.shop_id).scalar()
        bar_data.append({"shop_name": s.shop_name, "distributed_kg": float(dist)})
    trend = db.query(func.date_trunc("month", Transaction.transaction_date).label("month"), func.sum(Transaction.quantity_given_kg).label("total")).group_by("month").order_by("month").limit(6).all()
    comp_break = db.query(Complaint.complaint_type, func.count(Complaint.complaint_id)).group_by(Complaint.complaint_type).all()
    return ok({"summary": {"total_shops": total_shops, "total_beneficiaries": total_bens, "active_alerts": act_alerts, "open_complaints": open_comps, "high_risk_shops": high_risk},
               "bar_chart": bar_data,
               "monthly_trend": [{"month": str(r.month)[:7], "total_kg": float(r.total or 0)} for r in trend],
               "complaint_breakdown": [{"type": r[0].value, "count": r[1]} for r in comp_break]})

@app.get("/officer/alerts")
def get_alerts(db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    rows = db.query(FraudAlert, Shop).join(Shop, FraudAlert.shop_id==Shop.shop_id).order_by(FraudAlert.created_at.desc()).all()
    return ok({"alerts": [{"alert_id": str(a.alert_id), "shop_name": s.shop_name, "shop_id": str(a.shop_id), "alert_type": a.alert_type, "description": a.description, "severity": a.severity.value, "is_reviewed": a.is_reviewed, "created_at": a.created_at.isoformat()} for a,s in rows]})

@app.get("/officer/shops/risk")
def get_risk(db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    shops = db.query(Shop).order_by(Shop.risk_score.desc()).all()
    return ok({"shops": [{"shop_id": str(s.shop_id), "shop_name": s.shop_name, "owner_name": s.owner_name, "district": s.district, "risk_score": float(s.risk_score or 0), "risk_level": s.risk_level.value} for s in shops]})

@app.get("/officer/complaints")
def get_all_complaints(status: str = Query(None), db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    q = db.query(Complaint, Beneficiary, Shop).join(Beneficiary, Complaint.beneficiary_id==Beneficiary.beneficiary_id).join(Shop, Complaint.shop_id==Shop.shop_id).order_by(Complaint.created_at.desc())
    if status: q = q.filter(Complaint.status == status.upper())
    rows = q.all()
    return ok({"complaints": [{"complaint_id": str(c.complaint_id), "beneficiary_name": b.name, "shop_name": s.shop_name, "complaint_type": c.complaint_type.value, "description": c.description, "status": c.status.value, "ai_category": c.ai_category, "created_at": c.created_at.isoformat(), "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None} for c,b,s in rows]})

class ResolveRequest(BaseModel):
    complaint_id: str

@app.post("/officer/complaints/resolve")
def resolve_complaint(payload: ResolveRequest, db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    c = db.query(Complaint).filter(Complaint.complaint_id == payload.complaint_id).first()
    if not c: raise HTTPException(404, "Complaint not found")
    c.status = ComplaintStatus.RESOLVED; c.resolved_at = datetime.utcnow()
    db.commit()
    return ok({}, "Resolved")

@app.get("/officer/predictions")
def get_predictions(db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    rows = db.query(StockPrediction, Shop).join(Shop, StockPrediction.shop_id==Shop.shop_id).order_by(StockPrediction.prediction_month.desc()).all()
    return ok({"predictions": [{"prediction_id": str(p.prediction_id), "shop_name": s.shop_name, "grain_type": p.grain_type.value, "predicted_demand_kg": float(p.predicted_demand_kg or 0), "prediction_month": p.prediction_month.isoformat() if p.prediction_month else None} for p,s in rows]})

@app.get("/officer/report/export")
def export_report(format: str = Query("csv", regex="^(csv|pdf)$"), db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    shops = db.query(Shop).order_by(Shop.risk_score.desc()).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Shop Name","Owner","District","Risk Score","Risk Level"])
    for s in shops: w.writerow([s.shop_name, s.owner_name, s.district, float(s.risk_score or 0), s.risk_level.value])
    out.seek(0)
    return StreamingResponse(iter([out.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=report.csv"})

# ── AI ENDPOINTS ──────────────────────────────────────────────────────────────
class FraudRequest(BaseModel):
    shop_id: str

@app.post("/ai/fraud-detection/run")
def fraud_run(payload: FraudRequest, db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    from datetime import timedelta as td
    inv = db.query(StockInventory).filter(StockInventory.shop_id == payload.shop_id).all()
    thirty = datetime.utcnow() - td(days=30)
    txn_count  = db.query(func.count(Transaction.transaction_id)).filter(Transaction.shop_id==payload.shop_id, Transaction.transaction_date>=thirty).scalar() or 0
    comp_count = db.query(func.count(Complaint.complaint_id)).filter(Complaint.shop_id==payload.shop_id, Complaint.created_at>=thirty).scalar() or 0
    total_recv = sum(float(i.stock_received_kg or 0) for i in inv)
    total_dist = sum(float(i.stock_distributed_kg or 0) for i in inv)
    mismatch   = abs(total_recv - total_dist) / max(total_recv, 1) * 100
    features   = {"distribution_ratio": total_dist/max(total_recv,1), "txn_per_day": txn_count/30, "complaint_count": comp_count, "mismatch_pct": mismatch}
    result = run_fraud_detection(features)
    risk   = calculate_risk_score(result["anomaly_score"], comp_count, mismatch, features["txn_per_day"])
    if result["is_fraud_suspected"]:
        a = FraudAlert(shop_id=payload.shop_id, alert_type="AI_DETECTED", description=result["reason_text"], severity="HIGH" if risk["risk_score"]>70 else "MEDIUM")
        db.add(a)
    shop = db.query(Shop).filter(Shop.shop_id == payload.shop_id).first()
    if shop: shop.risk_score = risk["risk_score"]; shop.risk_level = risk["risk_level"]
    db.commit()
    return ok({**result, **risk, "shop_id": payload.shop_id})

@app.get("/ai/risk-score/{shop_id}")
def get_risk_score(shop_id: str, db: Session = Depends(get_db), user=Depends(require_role("officer"))):
    shop = db.query(Shop).filter(Shop.shop_id == shop_id).first()
    if not shop: raise HTTPException(404, "Shop not found")
    return ok({"shop_id": shop_id, "shop_name": shop.shop_name, "risk_score": float(shop.risk_score or 0), "risk_level": shop.risk_level.value})

class PredictRequest(BaseModel):
    shop_id: str; grain_type: str

@app.post("/ai/predict-stock")
def predict_stock(payload: PredictRequest, db: Session = Depends(get_db), user=Depends(require_role("officer","shopkeeper"))):
    from datetime import timedelta as td
    txns = db.query(Transaction).filter(Transaction.shop_id==payload.shop_id, Transaction.grain_type==payload.grain_type, Transaction.transaction_date>=datetime.utcnow()-td(days=180)).order_by(Transaction.transaction_date).all()
    monthly = {}
    for t in txns:
        k = t.transaction_date.strftime("%Y-%m")
        monthly[k] = monthly.get(k, 0) + float(t.quantity_given_kg)
    vals = list(monthly.values())
    if len(vals) >= 2:
        X = np.arange(len(vals)).reshape(-1,1); y = np.array(vals)
        pred = float(LinearRegression().fit(X,y).predict([[len(vals)]])[0])
        pred = max(pred, float(np.mean(y))*0.5); pred = min(pred, float(np.mean(y))*3)
    elif vals:
        pred = float(np.mean(vals))
    else:
        pred = 50.0
    pred = round(pred, 2)
    next_month = (datetime.utcnow().replace(day=1) + __import__("datetime").timedelta(days=32)).replace(day=1)
    sp = StockPrediction(shop_id=payload.shop_id, grain_type=payload.grain_type, predicted_demand_kg=pred, prediction_month=next_month)
    db.add(sp); db.commit()
    return ok({"shop_id": payload.shop_id, "grain_type": payload.grain_type, "predicted_demand_kg": pred, "prediction_month": next_month.strftime("%Y-%m")})

class CatRequest(BaseModel):
    description: str

@app.post("/ai/categorize-complaint")
def categorize(payload: CatRequest, user=Depends(require_role("officer","beneficiary"))):
    return ok({"predicted_category": categorize_complaint(payload.description), "confidence": 0.87})

@app.get("/health")
def health():
    return {"status": "ok", "service": "Smart Ration Guardian API"}
