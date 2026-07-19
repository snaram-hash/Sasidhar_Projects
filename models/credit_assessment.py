from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class CreditAssessment(BaseModel):
    id: Optional[int] = None
    borrower_id: int = Field(..., description="FK Borrower")
    current_ratio: float
    quick_ratio: float
    debt_equity: float
    dscr: float
    receivable_days: float
    inventory_days: float
    payable_days: float
    working_capital_cycle: float
    assessment_date: datetime = Field(default_factory=datetime.now)
