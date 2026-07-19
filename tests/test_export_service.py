import pytest
import os
from models.borrower import Borrower
from services.borrower_service import borrower_service
from services.export_service import export_service

def test_export_and_dashboard_compilation(temp_db, temp_dir):
    # Setup borrower
    b = Borrower(
        company_name="HARIKA SHIPPING LTD",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Shipping",
        constitution="Corporation"
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
    conn.commit()
    conn.close()
    
    # Run export
    csv_dir = os.path.join(temp_dir, "powerbi_data")
    export_service.export_powerbi_data(b_id, csv_dir)
    
    # Assert files exist
    assert os.path.exists(os.path.join(csv_dir, "Dim_Company.csv"))
    assert os.path.exists(os.path.join(csv_dir, "Fact_Financials.csv"))
    assert os.path.exists(os.path.join(csv_dir, "Fact_GST_Monthly.csv"))
    assert os.path.exists(os.path.join(csv_dir, "Fact_Banking_Monthly.csv"))
    assert os.path.exists(os.path.join(csv_dir, "Fact_Bank_Alerts.csv"))
    assert os.path.exists(os.path.join(csv_dir, "Dim_Date.csv"))
