import pytest
import os
import openpyxl
from models.borrower import Borrower
from services.borrower_service import borrower_service
from services.cam_service import cam_service

def test_cam_generation_success(temp_db, temp_dir):
    # Onboard borrower
    b = Borrower(
        company_name="HARIKA SHIPPING",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Shipping",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    # Financials
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Financials (borrower_id, financial_year, sales, pat, depreciation, interest_paid, reserves, net_worth, current_assets, current_liabilities)
        VALUES (?, ?, 10000000.0, 500000.0, 100000.0, 200000.0, 1500000.0, 4600000.0, 8500000.0, 6000000.0)
        """,
        (b_id, "FY24")
    )
    
    # GST Sales
    cursor.execute(
        """
        INSERT INTO GSTSales (borrower_id, document_id, filing_period, taxable_sales)
        VALUES (?, 1, 'April 2024', 800000.0)
        """,
        (b_id,)
    )
    
    # Bank Transactions
    cursor.execute(
        """
        INSERT INTO BankTransactions (borrower_id, document_id, tx_date, narration, credit, debit, balance)
        VALUES (?, 2, '2024-04-10 10:00:00', 'CLIENT WIRE CREDIT', 900000.0, 0.0, 900000.0)
        """,
        (b_id,)
    )
    
    # Document registration
    cursor.execute(
        """
        INSERT INTO Documents (id, borrower_id, file_name, file_type, file_size, financial_year, hash)
        VALUES (2, ?, 'au_statement.pdf', 'BankStatement', 500, 'FY24', 'hash_code_bank')
        """,
        (b_id,)
    )
    conn.commit()
    conn.close()
    
    # Evaluate Policy to populate Risk Assessments
    from engines.policy_engine import policy_engine
    policy_engine.evaluate_policy(b_id, "FY24")
    
    # Generate CAM
    out_path = cam_service.generate_cam(b_id, "FY24")
    assert os.path.exists(out_path)
    
    # Load and assert values were set
    wb = openpyxl.load_workbook(out_path)
    sheet_fs = wb['FINANCIAL SHEET']
    assert sheet_fs['B1'].value == "ABZPV8982E"
    assert sheet_fs['E1'].value == "HARIKA SHIPPING"
    # Sales in Lakhs (10000000.0 / 100000.0 = 100.0)
    assert sheet_fs['E4'].value == 100.0
    wb.close()
