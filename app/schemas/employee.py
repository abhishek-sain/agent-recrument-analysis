from pydantic import BaseModel, Field


class EmployeeOnboardRequest(BaseModel):
    """
    BQP Employee onboarding has no link-generation step - the employee
    (or whoever is raising it on their behalf) fills this directly.
    user_type is always EMPLOYEE; there's nothing to choose here.
    """

    name: str = Field(..., max_length=150)
    number: str = Field(..., max_length=15)
    email: str | None = Field(default=None, max_length=150)
    raised_by: str = Field(..., max_length=50, description="Employee code of whoever is raising this request")


class EmployeeOnboardResponse(BaseModel):
    """
    No onboarding_url here - there's no link to share. token is the same
    handle used everywhere else (PUT .../onboarding/{token}/form,
    POST .../onboarding/{token}/documents, etc.) - the employee's own
    client just holds onto it directly instead of receiving it via URL.
    """

    id: str
    token: str
