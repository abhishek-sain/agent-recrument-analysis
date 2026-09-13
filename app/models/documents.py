import enum
from datetime import date

from sqlalchemy import String, Date, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DocumentType(str, enum.Enum):
    """Which users_data file column an uploaded file is stored against."""

    PAN_CARD = "PAN_CARD"
    AADHAAR = "AADHAAR"
    EDUCATIONAL_QUALIFICATION = "EDUCATIONAL_QUALIFICATION"
    PHOTOGRAPH = "PHOTOGRAPH"
    CANCELLED_CHEQUE = "CANCELLED_CHEQUE"


class DocumentDetails(Base):
    """
    Table-2: structured fields extracted from the uploaded PAN card,
    Aadhaar card, and educational certificate (e.g. by an OCR step, or
    entered manually). One row per users_data record.
    """

    __tablename__ = "document_details"

    # e.g. DOC-12-09-2026-143059-4 - built by app.services.id_generator
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    users_data_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("users_data.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # --- PAN fields ---
    pan_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    pan_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pan_father_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pan_dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    pan_gender: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # --- Aadhaar fields ---
    aadhaar_number: Mapped[str | None] = mapped_column(String(12), nullable=True)
    aadhaar_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    aadhaar_dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    aadhaar_yob: Mapped[str | None] = mapped_column(String(4), nullable=True)
    aadhaar_gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    aadhaar_address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    aadhaar_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aadhaar_district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aadhaar_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    aadhaar_pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # --- Educational certificate fields ---
    education_student_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    education_father_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    education_mother_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    qualification: Mapped[str | None] = mapped_column(String(150), nullable=True)
    course_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    specialization: Mapped[str | None] = mapped_column(String(150), nullable=True)
    institution_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    university_board: Mapped[str | None] = mapped_column(String(200), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    roll_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    examination_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    passing_year: Mapped[str | None] = mapped_column(String(4), nullable=True)
    semester_year: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_marks: Mapped[str | None] = mapped_column(Numeric(10, 2), nullable=True)
    maximum_marks: Mapped[str | None] = mapped_column(Numeric(10, 2), nullable=True)
    percentage: Mapped[str | None] = mapped_column(Numeric(5, 2), nullable=True)
    cgpa: Mapped[str | None] = mapped_column(Numeric(4, 2), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    certificate_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    certificate_issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
