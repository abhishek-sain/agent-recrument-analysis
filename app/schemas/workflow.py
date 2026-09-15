from datetime import date, datetime

from pydantic import BaseModel

from app.models.user import OnboardingStatus, UserType


class ReviewRequest(BaseModel):
    """
    next_status must be the immediate next stage in the pipeline
    (see app.routers.workflow.PIPELINE_ORDER) - e.g. from UNDER_REVIEW
    you may only move to UNDER_TRAINING, REJECTED, or SEND_BACK; no
    skipping stages. REJECTED/SEND_BACK are only legal while the record
    is at UNDER_REVIEW (the eligibility-check stage).
    """

    next_status: OnboardingStatus
    reviewed_by: str


class ReviewResponse(BaseModel):
    status: OnboardingStatus
    new_onboarding_url: str | None = None  # populated on SEND_BACK
    message: str


class OnboardingListItem(BaseModel):
    id: str
    name: str
    number: str
    user_type: UserType
    status: OnboardingStatus
    onboarding_link: str
    raised_by: str
    reviewed_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConvertToPosRequest(BaseModel):
    converted_by: str


class ConvertToPosResponse(BaseModel):
    id: str
    user_type: UserType
    joining_date: date | None
    pos_conversion_date: date | None
    ageing_days: int | None
    message: str
