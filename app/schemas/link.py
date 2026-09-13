from pydantic import BaseModel, Field

from app.models.user import UserType, OnboardingStatus


class GenerateLinkRequest(BaseModel):
    name: str = Field(..., max_length=150)
    number: str = Field(..., max_length=15)
    user_type: UserType
    raised_by: str = Field(..., max_length=50, description="SM employee code")


class ShareLinks(BaseModel):
    copy_link: str
    whatsapp: str
    sms: str


class GenerateLinkResponse(BaseModel):
    id: str
    token: str
    onboarding_url: str
    share: ShareLinks


class LinkPrefillResponse(BaseModel):
    id: str
    name: str
    number: str
    user_type: UserType
    status: OnboardingStatus
