from typing import Optional
from pydantic import BaseModel, Field

class FinancialStatement(BaseModel):
    id: Optional[int] = None
    borrower_id: int = Field(..., description="Foreign key linking to Borrower")
    financial_year: str = Field(..., pattern=r"^FY[0-9]{2}$", description="FY format e.g. FY24")
    sales: float = Field(default=0.0, description="Annual audited turnover")
    pat: float = Field(default=0.0, description="Profit After Tax")
    depreciation: float = Field(default=0.0, description="Annual depreciation")
    interest_paid: float = Field(default=0.0, description="Interest expenses paid on facilities")
    reserves: float = Field(default=0.0, description="Reserves and surplus accumulated")
    net_worth: float = Field(default=0.0, description="Tangible Net Worth")
    current_assets: float = Field(default=0.0, description="Total current assets")
    current_liabilities: float = Field(default=0.0, description="Total current liabilities")
    secured_loans: float = Field(default=0.0, description="Long term secured loans")
    unsecured_loans: float = Field(default=0.0, description="Unsecured borrowings")
    working_capital_limits: float = Field(default=0.0, description="Sanctioned Cash Credit / OD limits")
    purchases: float = Field(default=0.0, description="Annual Cost of Goods Sold / Purchases")
    direct_expenses: float = Field(default=0.0, description="Direct operating expenses")
    debtors: float = Field(default=0.0, description="Accounts receivables balance")
    creditors: float = Field(default=0.0, description="Accounts payables balance")
    inventory: float = Field(default=0.0, description="Ending stock inventory value")
