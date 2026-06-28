import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from .shop import RiskLevel


class Beneficiary(Base):
    __tablename__ = "beneficiaries"

    beneficiary_id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ration_card_number     = Column(String(50), unique=True, nullable=False)
    name                   = Column(String(200), nullable=False)
    phone                  = Column(String(20))
    address                = Column(Text)
    family_members         = Column(Integer, default=1)
    assigned_shop_id       = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="SET NULL"), nullable=True)
    monthly_entitlement_kg = Column(Numeric(8, 2), default=25.0)
    password_hash          = Column(String(255), nullable=False)
    created_at             = Column(DateTime, default=datetime.utcnow)

    assigned_shop = relationship("Shop", back_populates="beneficiaries")
    transactions  = relationship("Transaction", back_populates="beneficiary")
    complaints    = relationship("Complaint", back_populates="beneficiary")
