import pytest
from database.db_manager import db
from models.borrower import Borrower
from services.borrower_service import borrower_service
from engines.policy_engine import policy_engine

def test_policy_engine_low_risk_pass(temp_db):
    # Setup borrower
    b = Borrower(
        company_name="HEALTHY COMPANY LTD",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Retail",
        constitution="Corporation"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    # 1. Setup healthy financials in DB
    # CA = 200,000 | CL = 100,000 -> Current Ratio = 2.0 (>= 1.0)
    # PAT = 50,000 | Dep = 10,000 | Interest = 10,000 -> DSCR = 7.0 (>= 1.2)
    # Secured Debt = 50,000 | Unsecured Debt = 50,000 | NW = 100,000 -> Debt to Equity = 1.0 (<= 3.0)
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Financials (borrower_id, financial_year, sales, pat, depreciation, interest_paid, reserves, net_worth, current_assets, current_liabilities, secured_loans, unsecured_loans)
        VALUES (?, ?, 500000.0, 50000.0, 10000.0, 10000.0, 20000.0, 100000.0, 200000.0, 100000.0, 50000.0, 50000.0)
        """,
        (b_id, "FY24")
    )
    
    # Insert healthy CIBIL assessment
    cursor.execute(
        """
        INSERT INTO RiskAssessments (borrower_id, score, risk_tier)
        VALUES (?, 750, 'Low')
        """,
        (b_id,)
    )
    conn.commit()
    conn.close()
    
    # Evaluate
    res = policy_engine.evaluate_policy(b_id, "FY24")
    assert res["risk_tier"] == "Low"
    assert res["score"] == 100.0 # 5/5 rules passed
    assert res["rules"]["R001"]["status"] == "PASSED"
    assert res["rules"]["R002"]["status"] == "PASSED"
    assert res["rules"]["R003"]["status"] == "PASSED"
    assert res["rules"]["R004"]["status"] == "PASSED"
    assert res["rules"]["R005"]["status"] == "PASSED"

def test_policy_engine_high_risk_fail(temp_db):
    b = Borrower(
        company_name="STRUGGLING LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Retail",
        constitution="Corporation"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    # CA = 50,000 | CL = 100,000 -> Current Ratio = 0.5 (fails R001 >= 1.0)
    # PAT = -10,000 | Dep = 2,000 | Interest = 10,000 -> DSCR = 0.2 (fails R002 >= 1.2)
    conn = temp_db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Financials (borrower_id, financial_year, sales, pat, depreciation, interest_paid, reserves, net_worth, current_assets, current_liabilities, secured_loans, unsecured_loans)
        VALUES (?, ?, 500000.0, -10000.0, 2000.0, 10000.0, 20000.0, 10000.0, 50000.0, 100000.0, 50000.0, 50000.0)
        """,
        (b_id, "FY24")
    )
    
    # Low CIBIL
    cursor.execute(
        """
        INSERT INTO RiskAssessments (borrower_id, score, risk_tier)
        VALUES (?, 620, 'Medium')
        """,
        (b_id,)
    )
    conn.commit()
    conn.close()
    
    # Evaluate
    res = policy_engine.evaluate_policy(b_id, "FY24")
    assert res["risk_tier"] == "High"
    assert res["rules"]["R001"]["status"] == "FAILED"
    assert res["rules"]["R002"]["status"] == "FAILED"
    assert res["rules"]["R004"]["status"] == "FAILED"
