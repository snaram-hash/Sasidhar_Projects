import os
import sqlite3
from config.settings import settings

def test_config_loads():
    assert settings.APP_VERSION == "1.0.0"
    assert settings.ENV in ["Development", "Production"]
    assert settings.MAX_UPLOAD_SIZE_BYTES > 0
    assert "pdf" in settings.ALLOWED_EXTENSIONS

def test_database_initialization(temp_db):
    assert os.path.exists(temp_db.db_path)
    
    conn = sqlite3.connect(temp_db.db_path)
    cursor = conn.cursor()
    
    # Check that all tables exist
    expected_tables = {
        "Borrowers", 
        "Documents", 
        "Financials", 
        "BankTransactions", 
        "RiskAssessments", 
        "CAMHistory", 
        "ApplicationLogs"
    }
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = {row[0] for row in cursor.fetchall()}
    
    for table in expected_tables:
        assert table in tables, f"Expected table {table} is missing."
    
    conn.close()

def test_pydantic_borrower_validation():
    from models.borrower import Borrower
    import pytest
    from pydantic import ValidationError
    
    # Valid model
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    assert b.company_name == "HARIKA SHIPPING & LOGISTICS"
    assert b.pan == "ABZPV8982E"
    
    # Invalid PAN type/regex should fail
    with pytest.raises(ValidationError):
        Borrower(
            company_name="A", # too short, but min_length is 2
            pan="INVALID123", # Fail
            gstin="37ABZPV8982E1ZS",
            industry="Logistics",
            constitution="Proprietorship"
        )
