from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import OnboardingStatus, UserType, UsersData
from app.schemas.employee import EmployeeOnboardRequest, EmployeeOnboardResponse
from app.services.id_generator import SEQ_USERS_DATA, generate_id
from app.services.token_service import build_onboarding_url, generate_token

router = APIRouter(prefix="/api/v1/employees", tags=["employees"])


@router.post("/onboard", response_model=EmployeeOnboardResponse)
def onboard_employee(payload: EmployeeOnboardRequest, db: Session = Depends(get_db)):
    """
    BQP Employee onboarding - no SM, no link generation. The employee
    (or whoever raises it) submits name/number/email directly; user_type
    is forced to EMPLOYEE and the record starts at FORM_IN_PROGRESS
    (there's no LINK_GENERATED stage since no link exists). The
    returned token drives the same onboarding/document endpoints as the
    POS/Referral flow - PUT .../onboarding/{token}/form,
    POST .../onboarding/{token}/documents, POST .../onboarding/{token}/submit.

    Document data extraction (PAN/Aadhaar/bank details into
    document_details) is done by a separate document-processing service
    calling the existing PUT .../documents/{pan,aadhaar,bank}-details
    endpoints - nothing extra needed here for that.
    """
    token = generate_token()
    record_id = generate_id(db, "TKT", SEQ_USERS_DATA)
    onboarding_url = build_onboarding_url(UserType.EMPLOYEE, token)

    record = UsersData(
        id=record_id,
        name=payload.name,
        number=payload.number,
        email=payload.email,
        user_type=UserType.EMPLOYEE,
        onboarding_link=onboarding_url,
        raised_by=payload.raised_by,
        status=OnboardingStatus.FORM_IN_PROGRESS,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return EmployeeOnboardResponse(id=record.id, token=token)
