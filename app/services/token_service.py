import secrets
from urllib.parse import quote

from app.config import settings
from app.models.user import UserType


def generate_token() -> str:
    """Opaque, unguessable token used to address a single onboarding record.
    This is the ONLY thing that goes into the shared link - it carries no
    embedded user data, so the link itself leaks nothing if intercepted.
    """
    return secrets.token_urlsafe(32)


def build_onboarding_url(user_type: UserType, token: str) -> str:
    """
    Builds the URL that is shared with the POS / POS Referral.

    The frontend team owns a route shaped like:
        /onboard/:userType/:token
    e.g. https://frontend.app/onboard/pos/AbC123...
             or /onboard/pos_referral/AbC123...

    On page load the frontend calls:
        GET {API_BASE}/api/v1/links/{token}
    to validate the token and fetch prefill data (name, number, user_type,
    current status) before rendering the form. It never needs direct DB
    access - the token is the sole handle to this backend.
    """
    slug = "pos" if user_type == UserType.POS else "pos-referral"
    return f"{settings.FRONTEND_BASE_URL.rstrip('/')}/onboard/{slug}/{token}"


def build_share_links(name: str, number: str, onboarding_url: str) -> dict:
    message = f"Hi {name}, please complete your onboarding here: {onboarding_url}"
    return {
        "copy_link": onboarding_url,
        "whatsapp": f"https://wa.me/{number.lstrip('+')}?text={quote(message)}",
        "sms": f"sms:{number}?body={quote(message)}",
    }
