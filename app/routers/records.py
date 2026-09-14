from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.documents import DocumentDetails
from app.models.user import UsersData
from app.routers.deps import get_document_details_by_id, get_record_by_id
from app.schemas.documents import DocumentDetailsResponse
from app.schemas.onboarding import OnboardingRecordResponse

router = APIRouter(prefix="/api/v1/admin", tags=["admin-records"])

# NOTE: these endpoints assume they sit behind your existing Ops
# authentication & role-based access middleware - no auth is implemented
# here per your instructions.


@router.get("/users-data", response_model=list[OnboardingRecordResponse])
def list_users_data(db: Session = Depends(get_db)):
    return db.query(UsersData).order_by(UsersData.created_at.desc()).all()


@router.get("/users-data/{record_id}", response_model=OnboardingRecordResponse)
def get_users_data(record: UsersData = Depends(get_record_by_id)):
    return record


@router.get("/document-details", response_model=list[DocumentDetailsResponse])
def list_document_details(db: Session = Depends(get_db)):
    return db.query(DocumentDetails).all()


@router.get("/document-details/{document_id}", response_model=DocumentDetailsResponse)
def get_document_details(record: DocumentDetails = Depends(get_document_details_by_id)):
    return record
