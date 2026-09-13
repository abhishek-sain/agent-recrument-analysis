import enum
from datetime import datetime

from pydantic import BaseModel

from app.models.user import OnboardingStatus, UserType


class ReviewAction(str, enum.Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    SEND_BACK = "SEND_BACK"


class ReviewRequest(BaseModel):
    action: ReviewAction
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
    raised_by: str
    reviewed_by: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
