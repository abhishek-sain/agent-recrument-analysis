from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UsersData
from app.routers.deps import get_record_by_token
from app.schemas.link import GenerateLinkRequest, GenerateLinkResponse, LinkPrefillResponse, ShareLinks
from app.services.id_generator import SEQ_USERS_DATA, generate_id
from app.services.token_service import build_onboarding_url, build_share_links, generate_token

router = APIRouter(prefix="/api/v1/links", tags=["links"])


@router.post("/generate", response_model=GenerateLinkResponse)
def generate_link(payload: GenerateLinkRequest, db: Session = Depends(get_db)):
    """
    Called by the SM (Sales Manager) app after the SM logs in and enters
    the POS / Referral name + mobile number. Creates the onboarding
    record and returns a token + shareable URL - nothing is rendered by
    this backend; the URL points at a route the frontend team owns.
    """
    token = generate_token()
    record_id = generate_id(db, "TKT", SEQ_USERS_DATA)
    onboarding_url = build_onboarding_url(payload.user_type, token)

    record = UsersData(
        id=record_id,
        name=payload.name,
        number=payload.number,
        email=payload.email,
        user_type=payload.user_type,
        onboarding_link=onboarding_url,
        raised_by=payload.raised_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    share = build_share_links(record.name, record.number, onboarding_url)

    return GenerateLinkResponse(
        id=record.id,
        token=token,
        onboarding_url=onboarding_url,
        share=ShareLinks(**share),
    )


@router.get("/{token}", response_model=LinkPrefillResponse)
def resolve_link(record: UsersData = Depends(get_record_by_token)):
    """
    The frontend's onboarding page calls this on load (using the :token
    from its own route) to validate the link and get the prefill data
    (name, number, user_type, current status) needed to render the
    correct form/step. This is how the shared link "renders" on the
    frontend - the backend never serves HTML, it only backs the route.
    """
    return LinkPrefillResponse(
        id=record.id,
        name=record.name,
        number=record.number,
        user_type=record.user_type,
        status=record.status,
    )
