from pydantic import BaseModel, Field

from app.models.user import UserType, OnboardingStatus


class GenerateLinkRequest(BaseModel):
    name: str = Field(..., max_length=150)
    number: str = Field(..., max_length=15)
    email: str | None = Field(default=None, max_length=150)
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
    """
    What the frontend pre-fills, non-editable, when the POS/Referral
    opens their link - name/number/email/user_type are locked in at
    link-generation time; everything else is filled in by the user.
    """

    id: str
    name: str
    number: str
    email: str | None = None
    user_type: UserType
    status: OnboardingStatus
