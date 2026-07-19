import pytest
import os
import sqlite3
from unittest.mock import MagicMock
import pypdf

from models.borrower import Borrower
from services.borrower_service import borrower_service
from services.document_service import document_service
from services.extraction_service import extraction_service

# Mock PDF Page text extraction helper
class MockPage:
    def __init__(self, text):
        self.text = text
    def extract_text(self):
        return self.text

def test_bank_statement_parsing_and_storage(temp_db, temp_dir, monkeypatch):
    # Mock pypdf PdfReader
    mock_pdf_text = """
AU SMALL FINANCE BANK
Account No. 192837465012
2024-04-01 START BALANCE 0.0 50000.00
2024-04-05 NEFT TO SUPPLIER 25000.00 25000.00
2024-04-10 INTEREST PAID 500.00 24500.00
2024-04-15 GST REFUND 30000.00 54500.00
"""
    mock_reader = MagicMock()
    mock_reader.pages = [MockPage(mock_pdf_text)]
    monkeypatch.setattr(pypdf, "PdfReader", lambda path: mock_reader)
    
    # 1. Onboard borrower
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    # 2. Setup dummy physical file
    dummy_file = os.path.join(temp_dir, "au_bank_statement.pdf")
    with open(dummy_file, "w") as f:
        f.write("DUMMY DATA")
        
    doc_id = document_service.ingest_document(b_id, dummy_file, "BankStatement", "FY25")
    
    # 3. Extract and verify DB records
    res = extraction_service.extract_and_store(b_id, doc_id)
    assert res["bank_name"] == "AU SMALL FINANCE BANK"
    assert res["account_no"] == "192837465012"
    assert len(res["transactions"]) == 4 # 4 transactions (including START BALANCE)
    
    # Verify database
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM BankTransactions WHERE borrower_id = ?", (b_id,))
    assert cursor.fetchone()[0] == 4
    conn.close()

def test_financials_parsing_and_storage(temp_db, temp_dir, monkeypatch):
    mock_pdf_text = """
Balance Sheet and Profit & Loss Report
Revenue from operations 313348371.15
Profit for the tax 7807738.08
Depreciation and amortization 1200000.00
Finance costs 3400000.00
Reserves and surplus 15000000.00
Tangible Net Worth 46659110.01
Total current assets 85000000.00
Total current liabilities 60000000.00
Purchases 220000000.00
"""
    mock_reader = MagicMock()
    mock_reader.pages = [MockPage(mock_pdf_text)]
    monkeypatch.setattr(pypdf, "PdfReader", lambda path: mock_reader)
    
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    dummy_file = os.path.join(temp_dir, "audited_financials.pdf")
    with open(dummy_file, "w") as f:
        f.write("DUMMY DATA")
        
    doc_id = document_service.ingest_document(b_id, dummy_file, "AuditedFinancials", "FY24")
    
    res = extraction_service.extract_and_store(b_id, doc_id)
    assert res["sales"] == 313348371.15
    assert res["pat"] == 7807738.08
    assert res["depreciation"] == 1200000.00
    
    # Verify DB
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT sales, pat, depreciation, reserves FROM Financials WHERE borrower_id = ? AND financial_year = 'FY24'", (b_id,))
    row = cursor.fetchone()
    assert row["sales"] == 313348371.15
    assert row["pat"] == 7807738.08
    assert row["depreciation"] == 1200000.00
    assert row["reserves"] == 15000000.00
    conn.close()

def test_cibil_parsing_and_storage(temp_db, temp_dir, monkeypatch):
    mock_pdf_text = """
Credit Information Bureau Report (CIBIL)
CIBIL Score: 785
Active Accounts: 4
Total Enquiries: 12
Days Past Due occurrences: 30+ DPD
"""
    mock_reader = MagicMock()
    mock_reader.pages = [MockPage(mock_pdf_text)]
    monkeypatch.setattr(pypdf, "PdfReader", lambda path: mock_reader)
    
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    dummy_file = os.path.join(temp_dir, "cibil_report.pdf")
    with open(dummy_file, "w") as f:
        f.write("DUMMY DATA")
        
    doc_id = document_service.ingest_document(b_id, dummy_file, "CIBIL")
    
    res = extraction_service.extract_and_store(b_id, doc_id)
    assert res["score"] == 785
    assert res["active_loans"] == 4
    assert res["dpd_count"] == 1
    
    # Verify DB
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT score, risk_tier FROM RiskAssessments WHERE borrower_id = ?", (b_id,))
    row = cursor.fetchone()
    assert row["score"] == 785.0
    assert row["risk_tier"] == "Low"
    conn.close()
