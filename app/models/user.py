import enum
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserType(str, enum.Enum):
    POS = "POS"
    POS_REFERRAL = "POS_REFERRAL"
    EMPLOYEE = "EMPLOYEE"  # BQP employee - no link-generation step, see app.routers.employees


class OnboardingStatus(str, enum.Enum):
    """
    Pipeline (POS / POS Referral / BQP Employee all share it once a
    record exists):

      LINK_GENERATED (POS/Referral only - set at link creation, an
      Employee record starts at FORM_IN_PROGRESS since there's no link)
        -> FORM_IN_PROGRESS (first form save)
        -> SUBMITTED (user submits)
        -> UNDER_REVIEW (OPS starts the eligibility check)
        -> UNDER_TRAINING
        -> ONBOARDED (joining_date is stamped here - see UsersData.joining_date)
        -> AGREEMENT
        -> WELCOME_MESSAGE

    REJECTED / SEND_BACK are the only exits, and only from UNDER_REVIEW
    (eligibility check failed). SEND_BACK rotates the token and unlocks
    the form for corrections; REJECTED is terminal.

    OPS drives every UNDER_REVIEW -> ... -> WELCOME_MESSAGE transition
    explicitly via POST /api/v1/admin/onboarding/{id}/review - see
    app.routers.workflow.PIPELINE_ORDER.
    """

    LINK_GENERATED = "LINK_GENERATED"
    FORM_IN_PROGRESS = "FORM_IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    UNDER_TRAINING = "UNDER_TRAINING"
    ONBOARDED = "ONBOARDED"
    AGREEMENT = "AGREEMENT"
    WELCOME_MESSAGE = "WELCOME_MESSAGE"
    SEND_BACK = "SEND_BACK"
    REJECTED = "REJECTED"


class ConsentStatus(str, enum.Enum):
    AGREE = "AGREE"
    DISAGREE = "DISAGREE"


DEFAULT_TERMS_AND_CONDITIONS = "we can use your data for onboarding you"


class UsersData(Base):
    """Table-1: users_data - exactly the columns from the spec."""

    __tablename__ = "users_data"

    # e.g. TKT-12-09-2026-143059-7 - built by app.services.id_generator
    id: Mapped[str] = mapped_column(String(50), primary_key=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    number: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    user_type: Mapped[UserType] = mapped_column(SAEnum(UserType, name="user_type_enum"), nullable=False)

    # Full shareable onboarding URL, e.g.
    # http://localhost:3000/onboard/pos/nO5Z-N3WFXRNlU2pPv3Zd57-...
    # The record's access handle is the token in its last path segment -
    # see app.routers.deps.get_record_by_token for how it's matched.
    onboarding_link: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)

    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(10), nullable=True)

    pan_card: Mapped[str | None] = mapped_column(String, nullable=True)
    educational_qualification: Mapped[str | None] = mapped_column(String, nullable=True)
    aadhaar: Mapped[str | None] = mapped_column(String, nullable=True)
    photograph: Mapped[str | None] = mapped_column(String, nullable=True)
    cancelled_cheque: Mapped[str | None] = mapped_column(String, nullable=True)
    passbook: Mapped[str | None] = mapped_column(String(500), nullable=True)

    terms_and_conditions: Mapped[str | None] = mapped_column(
        String, nullable=True, default=DEFAULT_TERMS_AND_CONDITIONS, server_default=DEFAULT_TERMS_AND_CONDITIONS
    )
    consent: Mapped[ConsentStatus | None] = mapped_column(SAEnum(ConsentStatus, name="consent_enum"), nullable=True)

    raised_by: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[OnboardingStatus] = mapped_column(
        SAEnum(OnboardingStatus, name="onboarding_status_enum"),
        nullable=False,
        default=OnboardingStatus.LINK_GENERATED,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    updated_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # --- Ageing Report support ---
    # Date the record was onboarded (set once, when status first becomes
    # ONBOARDED). This is "Date of Joining" for the Ageing Report.
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Set only when a POS_REFERRAL is manually converted to POS. Its
    # presence is what marks a record as "converted" in the Ageing Report -
    # user_type itself flips to POS on conversion, so this is the only
    # record of the fact that it used to be a referral.
    pos_conversion_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # One document_details row per users_data record (see
    # app.models.documents.DocumentDetails.users_data_id, unique FK).
    document_details: Mapped["DocumentDetails | None"] = relationship(
        "DocumentDetails", uselist=False, viewonly=True
    )
