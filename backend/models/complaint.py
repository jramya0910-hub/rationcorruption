import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..database import Base


class ComplaintType(str, enum.Enum):
    UNDERWEIGHT    = "UNDERWEIGHT"
    POOR_QUALITY   = "POOR_QUALITY"
    OVERCHARGING   = "OVERCHARGING"
    NOT_AVAILABLE  = "NOT_AVAILABLE"
    OTHER          = "OTHER"


class ComplaintStatus(str, enum.Enum):
    OPEN         = "OPEN"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED     = "RESOLVED"


class Complaint(Base):
    __tablename__ = "complaints"

    complaint_id   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    beneficiary_id = Column(UUID(as_uuid=True), ForeignKey("beneficiaries.beneficiary_id", ondelete="CASCADE"), nullable=False)
    shop_id        = Column(UUID(as_uuid=True), ForeignKey("shops.shop_id", ondelete="CASCADE"), nullable=False)
    complaint_type = Column(SAEnum(ComplaintType, name="complaint_type_enum"), nullable=False)
    description    = Column(Text)
    status         = Column(SAEnum(ComplaintStatus, name="complaint_status_enum"), default=ComplaintStatus.OPEN)
    ai_category    = Column(String(100))
    created_at     = Column(DateTime, default=datetime.utcnow)
    resolved_at    = Column(DateTime, nullable=True)

    beneficiary = relationship("Beneficiary", back_populates="complaints")
    shop        = relationship("Shop", back_populates="complaints")
