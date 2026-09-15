from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserType, UsersData, OnboardingStatus
from app.routers.deps import get_record_by_token
from app.schemas.onboarding import (
    OnboardingFormUpdate,
    OnboardingRecordResponse,
    SubmitResponse,
    TermsAndConditionsUpdate,
)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

# Once a record leaves FORM_IN_PROGRESS (i.e. is submitted or further
# along OPS's pipeline), the form/T&C are locked. SEND_BACK is
# deliberately excluded - that's what re-opens editing after OPS kicks
# it back during the eligibility check.
LOCKED_STATUSES = {
    OnboardingStatus.SUBMITTED,
    OnboardingStatus.UNDER_REVIEW,
    OnboardingStatus.UNDER_TRAINING,
    OnboardingStatus.ONBOARDED,
    OnboardingStatus.AGREEMENT,
    OnboardingStatus.WELCOME_MESSAGE,
}

# Same set, used to block a second in-flight record for the same number.
IN_PROGRESS_OR_DONE_STATUSES = LOCKED_STATUSES


@router.get("/{token}", response_model=OnboardingRecordResponse)
def get_onboarding_record(record: UsersData = Depends(get_record_by_token)):
    return record


@router.put("/{token}/form", response_model=OnboardingRecordResponse)
def save_form(
    payload: OnboardingFormUpdate,
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    if record.status in LOCKED_STATUSES:
        raise HTTPException(status_code=403, detail=f"Form is locked while status is {record.status.value}")

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
    if record.status in LOCKED_STATUSES:
        raise HTTPException(status_code=403, detail=f"Record is locked while status is {record.status.value}")

    record.terms_and_conditions = payload.terms_and_conditions
    db.commit()
    db.refresh(record)
    return record


# POS / POS Referral fill these on the form before submitting - not
# required for EMPLOYEE, whose flow (per spec) is name/number/email +
# documents only.
REQUIRED_FORM_FIELDS = ["dob", "city", "state", "pincode"]
REQUIRED_DOCS = ["pan_card", "educational_qualification", "aadhaar", "photograph", "cancelled_cheque"]


def _missing_fields(record: UsersData) -> list[str]:
    missing = []
    if not record.name or not record.number:
        missing.append("name/number")
    if record.consent is None:
        missing.append("consent")

    if record.user_type != UserType.EMPLOYEE:
        for field in REQUIRED_FORM_FIELDS:
            if not getattr(record, field):
                missing.append(field)

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
    Final "Review & Submit" step, same for POS/Referral/Employee. Runs
    basic form/document validation and a duplicate-number check, then
    moves the record to SUBMITTED - OPS explicitly starts the
    eligibility check from there (POST .../admin/onboarding/{id}/review
    with next_status=UNDER_REVIEW).
    """
    missing = _missing_fields(record)
    if missing:
        raise HTTPException(status_code=422, detail={"message": "Incomplete submission", "missing": missing})

    duplicate = (
        db.query(UsersData)
        .filter(
            UsersData.number == record.number,
            UsersData.id != record.id,
            UsersData.status.in_(IN_PROGRESS_OR_DONE_STATUSES),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="A record with this mobile number is already submitted/onboarded")

    record.status = OnboardingStatus.SUBMITTED
    db.commit()

    return SubmitResponse(status=record.status, message="Submitted - pending operations review")
