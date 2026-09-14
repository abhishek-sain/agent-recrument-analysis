from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.documents import DocumentDetails
from app.models.user import UsersData
from app.routers.deps import get_document_details_by_id, get_record_by_id
from app.schemas.documents import DocumentDetailsResponse
from app.schemas.onboarding import UsersDataWithDocumentDetails

router = APIRouter(prefix="/api/v1/admin", tags=["admin-records"])

# NOTE: these endpoints assume they sit behind your existing Ops
# authentication & role-based access middleware - no auth is implemented
# here per your instructions. They return full PII (PAN/Aadhaar/bank
# details), so that gateway MUST restrict them to authorized Ops callers.

MAX_PAGE_SIZE = 200


@router.get("/users-data", response_model=list[UsersDataWithDocumentDetails])
def list_users_data(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(UsersData)
        .options(joinedload(UsersData.document_details))
        .order_by(UsersData.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


@router.get("/users-data/{record_id}", response_model=UsersDataWithDocumentDetails)
def get_users_data(record: UsersData = Depends(get_record_by_id)):
    return record


@router.get("/document-details", response_model=list[DocumentDetailsResponse])
def list_document_details(
    limit: int = Query(default=50, ge=1, le=MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(DocumentDetails)
        .order_by(DocumentDetails.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


@router.get("/document-details/{document_id}", response_model=DocumentDetailsResponse)
def get_document_details(record: DocumentDetails = Depends(get_document_details_by_id)):
    return record
