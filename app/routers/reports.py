from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import UserType, UsersData
from app.schemas.reports import AgeingReportItem

router = APIRouter(prefix="/api/v1/admin/reports", tags=["reports"])

CONVERSION_TARGET_DAYS = 90


@router.get("/ageing", response_model=list[AgeingReportItem])
def ageing_report(db: Session = Depends(get_db)):
    """
    Date of Joining -> POS Referral -> POS Conversion Date.

    Includes every record that either currently is a POS Referral
    (pending conversion) or was converted from one (pos_conversion_date
    is set) - a plain POS that was never a referral has neither and is
    excluded.
    """
    records = (
        db.query(UsersData)
        .filter(
            UsersData.joining_date.isnot(None),
            or_(UsersData.user_type == UserType.POS_REFERRAL, UsersData.pos_conversion_date.isnot(None)),
        )
        .order_by(UsersData.joining_date.asc())
        .all()
    )

    today = date.today()
    items = []
    for r in records:
        if r.pos_conversion_date:
            ageing_days = (r.pos_conversion_date - r.joining_date).days
            conversion_status = "CONVERTED"
            within_90_days = ageing_days <= CONVERSION_TARGET_DAYS
        else:
            ageing_days = (today - r.joining_date).days
            conversion_status = "PENDING"
            within_90_days = ageing_days <= CONVERSION_TARGET_DAYS

        items.append(
            AgeingReportItem(
                id=r.id,
                name=r.name,
                number=r.number,
                raised_by=r.raised_by,
                date_of_joining=r.joining_date,
                pos_conversion_date=r.pos_conversion_date,
                ageing_days=ageing_days,
                conversion_status=conversion_status,
                within_90_days=within_90_days,
            )
        )
    return items
