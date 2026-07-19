from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class BankTransaction(BaseModel):
    id: Optional[int] = None
    borrower_id: int = Field(..., description="FK Borrower")
    document_id: int = Field(..., description="FK Document source")
    tx_date: datetime = Field(..., description="Transaction timestamp")
    narration: str = Field(..., description="Transaction bank ledger statement narration line")
    credit: float = Field(default=0.0, description="Inward transaction deposit")
    debit: float = Field(default=0.0, description="Outward transaction withdrawal")
    balance: float = Field(..., description="Resulting account ledger balance")
    instrument_id: Optional[str] = Field(None, description="Cheque, UPI reference, or transaction ID")
