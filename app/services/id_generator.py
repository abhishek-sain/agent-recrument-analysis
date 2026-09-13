from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

SEQ_USERS_DATA = "seq_users_data"
SEQ_DOCUMENT_DETAILS = "seq_document_details"


def generate_id(db: Session, prefix: str, sequence_name: str) -> str:
    """
    Builds an id like TKT-12-09-2026-143059-7.

    The trailing number comes from a native SQL Server SEQUENCE (atomic,
    gap-safe under concurrent requests) rather than counting rows, so two
    requests in the same second never collide.
    """
    seq_value = db.execute(text(f"SELECT NEXT VALUE FOR {sequence_name}")).scalar()
    now = datetime.now()
    return f"{prefix}-{now:%d-%m-%Y}-{now:%H%M%S}-{seq_value}"
