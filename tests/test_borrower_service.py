import pytest
from models.borrower import Borrower
from services.borrower_service import borrower_service
from utils.exceptions import DocumentValidationError

def test_onboard_borrower_success(temp_db):
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    assert b_id == 1
    
    # Retrieve
    retrieved = borrower_service.get_borrower(b_id)
    assert retrieved is not None
    assert retrieved.company_name == b.company_name
    assert retrieved.pan == b.pan

def test_onboard_borrower_duplicate_pan(temp_db):
    b1 = Borrower(
        company_name="Company A",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    borrower_service.onboard_borrower(b1)
    
    # Duplicate PAN
    b2 = Borrower(
        company_name="Company B",
        pan="ABZPV8982E",
        gstin="38ABZPV8982E1ZS",
        industry="Retail",
        constitution="Partnership"
    )
    with pytest.raises(DocumentValidationError):
        borrower_service.onboard_borrower(b2)
