from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CAMRecord(BaseModel):
    id: Optional[int] = None
    borrower_id: int = Field(..., description="FK Borrower")
    cam_path: str = Field(..., description="Path to generated spreadsheet")
    generated_at: datetime = Field(default_factory=datetime.now)
    status: str = Field("Draft", description="Draft, Under Review, Approved, or Rejected")
    underwriter_notes: Optional[str] = Field(None, description="Observations and recommendation memo notes")
