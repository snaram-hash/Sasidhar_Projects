from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class Borrower(BaseModel):
    id: Optional[int] = Field(None, description="Primary key auto-incremented by DB")
    company_name: str = Field(..., min_length=2, description="Legal trade name of the borrower")
    pan: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", description="10-character Indian PAN format")
    gstin: str = Field(..., pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$", description="15-character Indian GSTIN format")
    industry: str = Field(..., description="Industry segment / business line")
    constitution: str = Field(..., description="Business structure (e.g., Proprietorship, Partnership, Private Limited)")
    created_at: datetime = Field(default_factory=datetime.now)
