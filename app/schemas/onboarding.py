from datetime import date, datetime

from pydantic import BaseModel

from app.models.user import UserType, OnboardingStatus, ConsentStatus
from app.schemas.documents import DocumentDetailsResponse


class OnboardingFormUpdate(BaseModel):
    """
    Partial/upsert payload for the fields the user fills in themselves.
    name/number/email/user_type are set at link-generation (or, for a
    BQP Employee, at POST /api/v1/employees/onboard) and are NOT
    editable here - pre-filled and locked per spec. terms_and_conditions
    is also NOT editable here - fixed at creation, editable only via
    PUT .../terms-and-conditions.
    """

    dob: date | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    consent: ConsentStatus | None = None


class TermsAndConditionsUpdate(BaseModel):
    terms_and_conditions: str


class OnboardingRecordResponse(BaseModel):
    id: str
    name: str
    number: str
    user_type: UserType
    status: OnboardingStatus
    raised_by: str

    dob: date | None = None
    email: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None

    pan_card: str | None = None
    educational_qualification: str | None = None
    aadhar_front: str | None = None
    aadhar_back: str | None = None
    photograph: str | None = None
    cancelled_cheque: str | None = None
    passbook: str | None = None

    terms_and_conditions: str | None = None
    consent: ConsentStatus | None = None

    created_at: datetime
    updated_at: datetime
    updated_by: str | None = None
    reviewed_by: str | None = None

    model_config = {"from_attributes": True}


class UsersDataWithDocumentDetails(OnboardingRecordResponse):
    """users_data + its document_details row, joined on users_data_id.
    document_details is null if that record hasn't saved any PAN/Aadhaar/
    bank details yet."""

    document_details: DocumentDetailsResponse | None = None


class SubmitResponse(BaseModel):
    status: OnboardingStatus
    message: str
