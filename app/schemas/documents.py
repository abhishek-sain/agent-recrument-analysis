from datetime import date, datetime

from pydantic import BaseModel

from app.models.documents import DocumentType


class DocumentUploadResponse(BaseModel):
    doc_type: DocumentType
    url: str


class PanDetailsUpdate(BaseModel):
    age: int | None = None
    pan_number: str | None = None
    pan_name: str | None = None
    pan_father_name: str | None = None
    pan_dob: date | None = None
    updated_by: str | None = None


class AadhaarDetailsUpdate(BaseModel):
    aadhaar_number: str | None = None
    aadhaar_name: str | None = None
    aadhaar_dob: date | None = None
    aadhaar_gender: str | None = None
    aadhaar_address: str | None = None
    aadhaar_city: str | None = None
    aadhaar_district: str | None = None
    aadhaar_state: str | None = None
    aadhaar_pincode: str | None = None
    updated_by: str | None = None


class BankDetailsUpdate(BaseModel):
    account_holder_name: str | None = None
    account_number: str | None = None
    ifsc_code: str | None = None
    bank_name: str | None = None
    updated_by: str | None = None


class DocumentDetailsResponse(BaseModel):
    id: str
    users_data_id: str

    age: int | None = None

    pan_number: str | None = None
    pan_name: str | None = None
    pan_father_name: str | None = None
    pan_dob: date | None = None

    aadhaar_number: str | None = None
    aadhaar_name: str | None = None
    aadhaar_dob: date | None = None
    aadhaar_gender: str | None = None
    aadhaar_address: str | None = None
    aadhaar_city: str | None = None
    aadhaar_district: str | None = None
    aadhaar_state: str | None = None
    aadhaar_pincode: str | None = None

    account_holder_name: str | None = None
    account_number: str | None = None
    ifsc_code: str | None = None
    bank_name: str | None = None

    created_at: datetime
    updated_at: datetime
    updated_by: str | None = None

    model_config = {"from_attributes": True}
