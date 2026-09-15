import enum
from datetime import date, datetime

from sqlalchemy import String, Date, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentType(str, enum.Enum):
    """Which users_data file column an uploaded file is stored against."""

    PAN_CARD = "PAN_CARD"
    AADHAAR_FRONT = "AADHAAR_FRONT"
    AADHAAR_BACK = "AADHAAR_BACK"
    EDUCATIONAL_QUALIFICATION = "EDUCATIONAL_QUALIFICATION"
    PHOTOGRAPH = "PHOTOGRAPH"
    CANCELLED_CHEQUE = "CANCELLED_CHEQUE"
    PASSBOOK = "PASSBOOK"


class DocumentDetails(Base):
    """
    Table-2: structured fields extracted from the uploaded PAN card and
    Aadhaar card (e.g. by an OCR step, or entered manually), plus basic
    demographic and bank details. One row per users_data record.
    """

    __tablename__ = "document_details"

    # e.g. DOC-12-09-2026-143059-4 - built by app.services.id_generator
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    users_data_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users_data.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- PAN fields ---
    pan_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    pan_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pan_father_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pan_dob: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- Aadhaar fields ---
    aadhaar_number: Mapped[str | None] = mapped_column(String(12), nullable=True)
    aadhaar_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    aadhaar_dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    aadhaar_gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    aadhaar_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    aadhaar_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aadhaar_district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aadhaar_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aadhaar_pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # --- Bank fields ---
    account_holder_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    account_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    ifsc_code: Mapped[str | None] = mapped_column(String(11), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
