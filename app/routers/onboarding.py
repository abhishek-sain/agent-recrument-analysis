from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UsersData, OnboardingStatus
from app.routers.deps import get_record_by_token
from app.schemas.onboarding import (
    OnboardingFormUpdate,
    OnboardingRecordResponse,
    SubmitResponse,
    TermsAndConditionsUpdate,
)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])


@router.get("/{token}", response_model=OnboardingRecordResponse)
def get_onboarding_record(record: UsersData = Depends(get_record_by_token)):
    return record


@router.put("/{token}/form", response_model=OnboardingRecordResponse)
def save_form(
    payload: OnboardingFormUpdate,
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    if record.status in (OnboardingStatus.UNDER_REVIEW, OnboardingStatus.APPROVED, OnboardingStatus.ACTIVE):
        raise HTTPException(status_code=403, detail="Form is locked while under review or already approved")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    record.status = OnboardingStatus.FORM_IN_PROGRESS
    db.commit()
    db.refresh(record)
    return record


@router.put("/{token}/terms-and-conditions", response_model=OnboardingRecordResponse)
def update_terms_and_conditions(
    payload: TermsAndConditionsUpdate,
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    """
    Edits ONLY terms_and_conditions, independent of the general form-save
    endpoint. terms_and_conditions is set to a fixed value at record
    creation - this is the sole way to change it afterward.
    """
    if record.status in (OnboardingStatus.UNDER_REVIEW, OnboardingStatus.APPROVED, OnboardingStatus.ACTIVE):
        raise HTTPException(status_code=403, detail="Record is locked while under review or already approved")

    record.terms_and_conditions = payload.terms_and_conditions
    db.commit()
    db.refresh(record)
    return record


REQUIRED_DOCS = ["pan_card", "aadhaar", "photograph"]


def _missing_fields(record: UsersData) -> list[str]:
    missing = []
    if not record.name or not record.number:
        missing.append("name/number")
    if record.consent is None:
        missing.append("consent")

    for doc in REQUIRED_DOCS:
        if not getattr(record, doc):
            missing.append(doc)
    return missing


@router.post("/{token}/submit", response_model=SubmitResponse)
def submit_form(
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    """
    Final "Review & Submit" step. Runs basic form/document validation and
    a duplicate check, then moves the record into the approval workflow
    (UNDER_REVIEW), matching the "System Processing" stage in the flow.
    """
    missing = _missing_fields(record)
    if missing:
        raise HTTPException(status_code=422, detail={"message": "Incomplete submission", "missing": missing})

    duplicate = (
        db.query(UsersData)
        .filter(
            UsersData.number == record.number,
            UsersData.id != record.id,
            UsersData.status.in_([OnboardingStatus.UNDER_REVIEW, OnboardingStatus.APPROVED, OnboardingStatus.ACTIVE]),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="A POS/Referral with this mobile number is already onboarded or in review")

    record.status = OnboardingStatus.UNDER_REVIEW
    db.commit()

    return SubmitResponse(status=record.status, message="Submitted for operations review")
