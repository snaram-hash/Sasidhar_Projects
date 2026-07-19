import pytest
import os
import pypdf
from unittest.mock import MagicMock
from models.borrower import Borrower
from services.borrower_service import borrower_service
from services.document_service import document_service
from services.extraction_service import extraction_service
from services.validation_service import validation_service

# Mock PDF Page text extraction helper
class MockPage:
    def __init__(self, text):
        self.text = text
    def extract_text(self):
        return self.text

def test_full_reconciliation_workflow_passed(temp_db, temp_dir, monkeypatch):
    # 1. Setup mock texts for different files
    # Audited sales = 100,000
    # GST sales = 101,000 (1% variance, within 10%)
    # Bank credit = 105,000 (5% variance, within 15%)
    # ITR income = 99,000 (1% variance, within 5%)
    
    fin_text = "Revenue from operations 100000.00\nProfit for the tax 10000.00\nDepreciation 5000.00\nFinance costs 2000.00\nReserves 20000.00\nTangible Net Worth 50000.00\nTotal current assets 30000.00\nTotal current liabilities 20000.00\n"
    gst_text = "GSTIN 37ABZPV8982E1ZS\nFiling Period April, 2024\nOutward taxable supplies 101000.00\n"
    bank_text = "AU SMALL FINANCE BANK\nAccount No. 123456\n2024-04-01 START BALANCE 0.0 0.0\n2024-04-05 CLIENT PAYMENT 105000.00 105000.00\n"
    itr_text = "Assessment Year 2025\nGross Total Income 99000.00\nTotal Tax Paid 1000.00\n"
    
    mock_pdf_pages = {
        "fin.pdf": [MockPage(fin_text)],
        "gst.pdf": [MockPage(gst_text)],
        "bank.pdf": [MockPage(bank_text)],
        "itr.pdf": [MockPage(itr_text)]
    }
    
    # Custom monkeypatch for PdfReader to select pages based on filename
    def mock_pdf_reader(path):
        key = os.path.basename(path)
        reader = MagicMock()
        reader.pages = mock_pdf_pages.get(key, [MockPage("")])
        return reader
        
    monkeypatch.setattr(pypdf, "PdfReader", mock_pdf_reader)
    
    # 2. Onboard borrower
    b = Borrower(
        company_name="HARIKA SHIPPING",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Shipping",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    # 3. Create dummy physical files
    files = {
        "AuditedFinancials": "fin.pdf",
        "GST_Returns": "gst.pdf",
        "BankStatement": "bank.pdf",
        "ITR": "itr.pdf"
    }
    
    for doc_type, name in files.items():
        path = os.path.join(temp_dir, name)
        with open(path, "w") as f:
            f.write(f"DUMMY CONTENT FOR {doc_type}")
        doc_id = document_service.ingest_document(b_id, path, doc_type, "FY24" if doc_type != "GST_Returns" else None)
        extraction_service.extract_and_store(b_id, doc_id)
        
    # 4. Trigger reconciliation
    report = validation_service.validate_borrower_data(b_id, "FY24")
    
    assert report["status"] == "PASSED"
    assert report["checks"]["gst_reconciliation"]["status"] == "PASSED"
    assert report["checks"]["bank_reconciliation"]["status"] == "PASSED"
    assert report["checks"]["itr_reconciliation"]["status"] == "PASSED"
    assert report["checks"]["negative_values"]["status"] == "PASSED"

def test_full_reconciliation_workflow_failed(temp_db, temp_dir, monkeypatch):
    # Audited sales = 100,000
    # GST sales = 120,000 (20% variance, fails 10%)
    # Bank credit = 130,000 (30% variance, fails 15% warning)
    # ITR income = 80,000 (20% variance, fails 5%)
    # Net worth is negative (-50000) -> warning
    
    fin_text = "Revenue from operations 100000.00\nProfit for the tax 10000.00\nDepreciation 5000.00\nFinance costs 2000.00\nReserves 20000.00\nTangible Net Worth -50000.00\nTotal current assets 30000.00\nTotal current liabilities 20000.00\n"
    gst_text = "GSTIN 37ABZPV8982E1ZS\nFiling Period April, 2024\nOutward taxable supplies 120000.00\n"
    bank_text = "AU SMALL FINANCE BANK\nAccount No. 123456\n2024-04-01 START BALANCE 0.0 0.0\n2024-04-05 CLIENT PAYMENT 130000.00 130000.00\n"
    itr_text = "Assessment Year 2025\nGross Total Income 80000.00\nTotal Tax Paid 1000.00\n"
    
    mock_pdf_pages = {
        "fin.pdf": [MockPage(fin_text)],
        "gst.pdf": [MockPage(gst_text)],
        "bank.pdf": [MockPage(bank_text)],
        "itr.pdf": [MockPage(itr_text)]
    }
    
    def mock_pdf_reader(path):
        key = os.path.basename(path)
        reader = MagicMock()
        reader.pages = mock_pdf_pages.get(key, [MockPage("")])
        return reader
        
    monkeypatch.setattr(pypdf, "PdfReader", mock_pdf_reader)
    
    b = Borrower(
        company_name="HARIKA SHIPPING",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Shipping",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    files = {
        "AuditedFinancials": "fin.pdf",
        "GST_Returns": "gst.pdf",
        "BankStatement": "bank.pdf",
        "ITR": "itr.pdf"
    }
    
    for doc_type, name in files.items():
        path = os.path.join(temp_dir, name)
        with open(path, "w") as f:
            f.write(f"DUMMY CONTENT FOR {doc_type}")
        doc_id = document_service.ingest_document(b_id, path, doc_type, "FY24" if doc_type != "GST_Returns" else None)
        extraction_service.extract_and_store(b_id, doc_id)
        
    report = validation_service.validate_borrower_data(b_id, "FY24")
    
    assert report["status"] == "FAILED"
    assert report["checks"]["gst_reconciliation"]["status"] == "FAILED"
    assert report["checks"]["bank_reconciliation"]["status"] == "WARNING"
    assert report["checks"]["itr_reconciliation"]["status"] == "FAILED"
    assert report["checks"]["negative_values"]["status"] == "WARNING"
