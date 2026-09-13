from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import OnboardingStatus, UsersData
from app.routers.deps import get_record_by_id
from app.schemas.workflow import OnboardingListItem, ReviewAction, ReviewRequest, ReviewResponse
from app.services.token_service import build_onboarding_url, generate_token

router = APIRouter(prefix="/api/v1/admin/onboarding", tags=["admin"])

# NOTE: these endpoints assume they sit behind your existing SM/Ops
# authentication & role-based access middleware - no auth is implemented
# here per your instructions.


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
    if record.status != OnboardingStatus.UNDER_REVIEW:
        raise HTTPException(status_code=409, detail=f"Record is in status {record.status}, not eligible for review")

    new_onboarding_url = None

    if payload.action == ReviewAction.APPROVE:
        record.status = OnboardingStatus.ACTIVE  # activation is immediate once approved

    elif payload.action == ReviewAction.REJECT:
        record.status = OnboardingStatus.REJECTED

    elif payload.action == ReviewAction.SEND_BACK:
        record.status = OnboardingStatus.SEND_BACK
        # issue a fresh link so the POS/Referral can update and resubmit
        new_onboarding_url = build_onboarding_url(record.user_type, generate_token())
        record.onboarding_link = new_onboarding_url

    record.reviewed_by = payload.reviewed_by
    record.updated_by = payload.reviewed_by
    db.commit()

    message = {
        ReviewAction.APPROVE: "Approved and activated",
        ReviewAction.REJECT: "Rejected",
        ReviewAction.SEND_BACK: "Sent back for corrections, new link issued",
    }[payload.action]

    return ReviewResponse(
        status=record.status,
        new_onboarding_url=new_onboarding_url,
        message=message,
    )
