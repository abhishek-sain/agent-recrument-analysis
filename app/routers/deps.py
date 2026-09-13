from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UsersData


def get_record_by_token(token: str, db: Session = Depends(get_db)) -> UsersData:
    """
    onboarding_link stores the full shareable URL (e.g.
    http://.../onboard/pos/<token>), while the frontend only ever sends
    back the bare token in the path. Match by the trailing characters of
    onboarding_link rather than an exact match - SQL Server's RIGHT()
    avoids LIKE wildcard pitfalls since a token can itself contain "_".
    """
    record = (
        db.query(UsersData)
        .filter(func.right(UsersData.onboarding_link, len(token)) == token)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Invalid onboarding link")
    return record


def get_record_by_id(record_id: str, db: Session = Depends(get_db)) -> UsersData:
    record = db.query(UsersData).filter(UsersData.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Onboarding record not found")
    return record
