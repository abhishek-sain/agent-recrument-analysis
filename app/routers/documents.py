from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.documents import DocumentDetails, DocumentType
from app.models.user import UsersData
from app.routers.deps import get_record_by_token
from app.schemas.documents import (
    AadhaarDetailsUpdate,
    BankDetailsUpdate,
    DocumentUploadResponse,
    PanDetailsUpdate,
)
from app.services.id_generator import SEQ_DOCUMENT_DETAILS, generate_id
from app.services.storage import get_storage

router = APIRouter(prefix="/api/v1/onboarding", tags=["documents"])

DOC_FIELD_MAP = {
    DocumentType.PAN_CARD: "pan_card",
    DocumentType.AADHAAR: "aadhaar",
    DocumentType.EDUCATIONAL_QUALIFICATION: "educational_qualification",
    DocumentType.PHOTOGRAPH: "photograph",
    DocumentType.CANCELLED_CHEQUE: "cancelled_cheque",
    DocumentType.PASSBOOK: "passbook",
}


@router.post("/{token}/documents", response_model=DocumentUploadResponse)
def upload_document(
    doc_type: DocumentType,
    file: UploadFile = File(...),
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    storage = get_storage()
    url = storage.save(file, folder=str(record.id))

    field = DOC_FIELD_MAP[doc_type]
    setattr(record, field, url)
    db.commit()

    return DocumentUploadResponse(doc_type=doc_type, url=url)


def _get_or_create_details(db: Session, record_id: str) -> DocumentDetails:
    obj = db.query(DocumentDetails).filter(DocumentDetails.users_data_id == record_id).first()
    if not obj:
        obj = DocumentDetails(id=generate_id(db, "DOC", SEQ_DOCUMENT_DETAILS), users_data_id=record_id)
        db.add(obj)
    return obj


@router.put("/{token}/documents/pan-details")
def save_pan_details(
    payload: PanDetailsUpdate,
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    obj = _get_or_create_details(db, record.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    return {"message": "PAN details saved"}


@router.put("/{token}/documents/aadhaar-details")
def save_aadhaar_details(
    payload: AadhaarDetailsUpdate,
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    obj = _get_or_create_details(db, record.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    return {"message": "Aadhaar details saved"}


@router.put("/{token}/documents/bank-details")
def save_bank_details(
    payload: BankDetailsUpdate,
    record: UsersData = Depends(get_record_by_token),
    db: Session = Depends(get_db),
):
    obj = _get_or_create_details(db, record.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(obj, field, value)
    db.commit()
    return {"message": "Bank details saved"}
