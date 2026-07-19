from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class RiskScore(BaseModel):
    id: Optional[int] = None
    borrower_id: int = Field(..., description="FK Borrower")
    liquidity_score: float = Field(..., ge=0.0, le=20.0)
    profitability_score: float = Field(..., ge=0.0, le=15.0)
    leverage_score: float = Field(..., ge=0.0, le=15.0)
    banking_score: float = Field(..., ge=0.0, le=20.0)
    cashflow_score: float = Field(..., ge=0.0, le=10.0)
    gst_score: float = Field(..., ge=0.0, le=10.0)
    cibil_score: float = Field(..., ge=0.0, le=10.0)
    total_score: float = Field(..., ge=0.0, le=100.0)
    risk_tier: str = Field(..., description="Low Risk, Moderate, High Risk, or Reject")
    scored_at: datetime = Field(default_factory=datetime.now)
