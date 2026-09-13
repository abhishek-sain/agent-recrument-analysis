from datetime import date

from pydantic import BaseModel


class AgeingReportItem(BaseModel):
    """
    One row of the Ageing Report: how long a POS Referral has been (or
    was) a referral before converting to a POS.

    conversion_status:
      - "CONVERTED": already promoted to POS - ageing_days is final.
      - "PENDING": still an active POS Referral - ageing_days counts up
        to today, and within_90_days tells you if the 90-day target has
        already been missed.
    """

    id: str
    name: str
    number: str
    raised_by: str
    date_of_joining: date | None
    pos_conversion_date: date | None
    ageing_days: int | None
    conversion_status: str  # CONVERTED | PENDING
    within_90_days: bool | None

    model_config = {"from_attributes": True}
