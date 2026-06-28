import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class AlertSeverity(str, enum.Enum):
    LOW      = "LOW"
    MEDIUM   = "MEDIUM"
    HIGH     = "HIGH"
    CRITICAL = "CRITICAL"


class FraudAlert(Base):
    __tablename__ = "fraud_alerts"

    alert_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id     = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    alert_type  = Column(String(100), nullable=False)
    description = Column(Text)
    severity    = Column(SAEnum(AlertSeverity, name="severity_enum"), default=AlertSeverity.LOW)
    is_reviewed = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)

    shop = relationship("Shop", back_populates="fraud_alerts")


class Officer(Base):
    __tablename__ = "officers"

    officer_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String(200), nullable=False)
    email         = Column(String(200), unique=True, nullable=False)
    district      = Column(String(100))
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)
