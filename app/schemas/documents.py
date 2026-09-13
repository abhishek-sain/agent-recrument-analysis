from datetime import date

from pydantic import BaseModel

from app.models.documents import DocumentType


class DocumentUploadResponse(BaseModel):
    doc_type: DocumentType
    url: str


class PanDetailsUpdate(BaseModel):
    pan_number: str | None = None
    pan_name: str | None = None
    pan_father_name: str | None = None
    pan_dob: date | None = None
    pan_gender: str | None = None


class AadhaarDetailsUpdate(BaseModel):
    aadhaar_number: str | None = None
    aadhaar_name: str | None = None
    aadhaar_dob: date | None = None
    aadhaar_yob: str | None = None
    aadhaar_gender: str | None = None
    aadhaar_address: str | None = None
    aadhaar_city: str | None = None
    aadhaar_district: str | None = None
    aadhaar_state: str | None = None
    aadhaar_pincode: str | None = None


class EducationDetailsUpdate(BaseModel):
    education_student_name: str | None = None
    education_father_name: str | None = None
    education_mother_name: str | None = None
    qualification: str | None = None
    course_name: str | None = None
    specialization: str | None = None
    institution_name: str | None = None
    university_board: str | None = None
    registration_number: str | None = None
    roll_number: str | None = None
    examination_name: str | None = None
    passing_year: str | None = None
    semester_year: str | None = None
    total_marks: float | None = None
    maximum_marks: float | None = None
    percentage: float | None = None
    cgpa: float | None = None
    grade: str | None = None
    result: str | None = None
    certificate_number: str | None = None
    certificate_issue_date: date | None = None
