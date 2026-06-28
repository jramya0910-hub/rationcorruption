import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, Numeric, Boolean, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base
from .shop import GrainType


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id    = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id           = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    beneficiary_id    = Column(UUID(as_uuid=True), ForeignKey("beneficiaries.beneficiary_id", ondelete="CASCADE"), nullable=False)
    grain_type        = Column(SAEnum(GrainType, name="grain_type_enum"), nullable=False)
    quantity_given_kg = Column(Numeric(8, 2), nullable=False)
    transaction_date  = Column(DateTime, default=datetime.utcnow)
    qr_scan_verified  = Column(Boolean, default=False)

    shop        = relationship("Shop", back_populates="transactions")
    beneficiary = relationship("Beneficiary", back_populates="transactions")


class StockInventory(Base):
    __tablename__ = "stock_inventory"

    inventory_id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id              = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    grain_type           = Column(SAEnum(GrainType, name="grain_type_enum"), nullable=False)
    stock_received_kg    = Column(Numeric(10, 2), default=0.0)
    stock_distributed_kg = Column(Numeric(10, 2), default=0.0)
    last_updated         = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    shop = relationship("Shop", back_populates="inventory")

    @property
    def remaining_stock_kg(self):
        return float(self.stock_received_kg or 0) - float(self.stock_distributed_kg or 0)


class StockPrediction(Base):
    __tablename__ = "stock_predictions"

    prediction_id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shop_id             = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    grain_type          = Column(SAEnum(GrainType, name="grain_type_enum"), nullable=False)
    predicted_demand_kg = Column(Numeric(10, 2))
    prediction_month    = Column(DateTime)
    created_at          = Column(DateTime, default=datetime.utcnow)

    shop = relationship("Shop", back_populates="stock_predictions")
