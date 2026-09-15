from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import OnboardingStatus, UsersData, UserType
from app.routers.deps import get_record_by_id
from app.schemas.workflow import (
    ConvertToPosRequest,
    ConvertToPosResponse,
    OnboardingListItem,
    ReviewRequest,
    ReviewResponse,
)
from app.services.token_service import build_onboarding_url, generate_token

router = APIRouter(prefix="/api/v1/admin/onboarding", tags=["admin"])

# NOTE: these endpoints assume they sit behind your existing SM/Ops
# authentication & role-based access middleware - no auth is implemented
# here per your instructions.

# The forward path every record walks once OPS starts working it. Same
# pipeline for POS / POS Referral / Employee.
PIPELINE_ORDER = [
    OnboardingStatus.SUBMITTED,
    OnboardingStatus.UNDER_REVIEW,
    OnboardingStatus.UNDER_TRAINING,
    OnboardingStatus.ONBOARDED,
    OnboardingStatus.AGREEMENT,
    OnboardingStatus.WELCOME_MESSAGE,
]

# REJECTED/SEND_BACK are only legal exits from the eligibility-check
# stage (UNDER_REVIEW) - matches the original approve/reject/send-back
# behaviour, just generalized past a single review step.
EXIT_STATUSES = {OnboardingStatus.REJECTED, OnboardingStatus.SEND_BACK}
EXIT_ALLOWED_FROM = OnboardingStatus.UNDER_REVIEW


@router.get("", response_model=list[OnboardingListItem])
def list_onboarding(
    status: OnboardingStatus | None = Query(default=None),
    db: Session = Depends(get_db),
):
    q = db.query(UsersData)
    if status:
        q = q.filter(UsersData.status == status)
    return q.order_by(UsersData.created_at.desc()).all()


@router.post("/{record_id}/review", response_model=ReviewResponse)
def review_onboarding(
    payload: ReviewRequest,
    record: UsersData = Depends(get_record_by_id),
    db: Session = Depends(get_db),
):
    """
    Moves a record one step through the OPS pipeline:
    SUBMITTED -> UNDER_REVIEW -> UNDER_TRAINING -> ONBOARDED -> AGREEMENT
    -> WELCOME_MESSAGE, no skipping. REJECTED/SEND_BACK are only legal
    while at UNDER_REVIEW (eligibility check).
    """
    next_status = payload.next_status

    if next_status in EXIT_STATUSES:
        if record.status != EXIT_ALLOWED_FROM:
            raise HTTPException(
                status_code=409,
                detail=f"{next_status.value} is only allowed from {EXIT_ALLOWED_FROM.value}, record is {record.status.value}",
            )
    else:
        if record.status not in PIPELINE_ORDER or next_status not in PIPELINE_ORDER:
            raise HTTPException(status_code=409, detail=f"Cannot move from {record.status.value} to {next_status.value}")
        current_index = PIPELINE_ORDER.index(record.status)
        target_index = PIPELINE_ORDER.index(next_status)
        if target_index != current_index + 1:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot skip stages: from {record.status.value} the only valid next status is "
                f"{PIPELINE_ORDER[current_index + 1].value if current_index + 1 < len(PIPELINE_ORDER) else 'none'}",
            )

    new_onboarding_url = None
    message = f"Moved to {next_status.value}"

    if next_status == OnboardingStatus.ONBOARDED and record.joining_date is None:
        record.joining_date = date.today()

    if next_status == OnboardingStatus.SEND_BACK:
        # issue a fresh link/token so the POS/Referral/Employee can
        # update and resubmit; also re-opens the form (see
        # onboarding.LOCKED_STATUSES, which excludes SEND_BACK).
        new_onboarding_url = build_onboarding_url(record.user_type, generate_token())
        record.onboarding_link = new_onboarding_url
        message = "Sent back for corrections, new link/token issued"
    elif next_status == OnboardingStatus.REJECTED:
        message = "Rejected"

    record.status = next_status
    record.reviewed_by = payload.reviewed_by
    record.updated_by = payload.reviewed_by
    db.commit()

    return ReviewResponse(
        status=record.status,
        new_onboarding_url=new_onboarding_url,
        message=message,
    )


@router.post("/{record_id}/convert-to-pos", response_model=ConvertToPosResponse)
def convert_to_pos(
    payload: ConvertToPosRequest,
    record: UsersData = Depends(get_record_by_id),
    db: Session = Depends(get_db),
):
    """
    Manually promotes an onboarded POS Referral to a full POS. Feeds the
    Ageing Report: joining_date (set on first reaching ONBOARDED) and
    pos_conversion_date (set here) together give the "how long were they
    a referral" duration.
    """
    if record.user_type != UserType.POS_REFERRAL:
        raise HTTPException(status_code=409, detail="Only a POS_REFERRAL record can be converted to POS")
    if record.status != OnboardingStatus.ONBOARDED:
        raise HTTPException(status_code=409, detail=f"Record is in status {record.status.value}, must be ONBOARDED to convert")

    record.user_type = UserType.POS
    record.pos_conversion_date = date.today()
    record.updated_by = payload.converted_by
    db.commit()

    ageing_days = (record.pos_conversion_date - record.joining_date).days if record.joining_date else None

    return ConvertToPosResponse(
        id=record.id,
        user_type=record.user_type,
        joining_date=record.joining_date,
        pos_conversion_date=record.pos_conversion_date,
        ageing_days=ageing_days,
        message="Converted from POS Referral to POS",
    )
