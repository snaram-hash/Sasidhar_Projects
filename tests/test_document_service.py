import pytest
import os
from models.borrower import Borrower
from services.borrower_service import borrower_service
from services.document_service import document_service
from utils.exceptions import DocumentValidationError
from config.settings import settings

def test_document_ingestion_success(temp_db, temp_dir):
    # Setup borrower
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    # Setup dummy upload file
    dummy_file = os.path.join(temp_dir, "dummy_bank_statement.pdf")
    with open(dummy_file, "w") as f:
        f.write("DUMMY PDF TRANSACTION CONTENT")
        
    doc_id = document_service.ingest_document(b_id, dummy_file, "BankStatement", "FY25")
    assert doc_id == 1
    
    # Verify file was copied to assets
    expected_path = os.path.join(settings.UPLOAD_DIR, str(b_id), "BankStatement", "dummy_bank_statement.pdf")
    assert os.path.exists(expected_path)
    
    # Verify listings
    docs = document_service.list_documents_for_borrower(b_id)
    assert len(docs) == 1
    assert docs[0]["file_name"] == "dummy_bank_statement.pdf"

def test_document_duplicate_hash(temp_db, temp_dir):
    # Setup borrower
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    dummy_file = os.path.join(temp_dir, "dummy_bank_statement.pdf")
    with open(dummy_file, "w") as f:
        f.write("DUMMY PDF TRANSACTION CONTENT")
        
    # First upload
    doc_id1 = document_service.ingest_document(b_id, dummy_file, "BankStatement", "FY25")
    
    # Attempt to upload duplicate file (same hash) - should return existing ID
    doc_id2 = document_service.ingest_document(b_id, dummy_file, "BankStatement", "FY25")
    assert doc_id1 == doc_id2

def test_document_invalid_extension(temp_db, temp_dir):
    b = Borrower(
        company_name="HARIKA SHIPPING & LOGISTICS",
        pan="ABZPV8982E",
        gstin="37ABZPV8982E1ZS",
        industry="Logistics",
        constitution="Proprietorship"
    )
    b_id = borrower_service.onboard_borrower(b)
    
    # Invalid extension file
    bad_file = os.path.join(temp_dir, "unsupported_data.exe")
    with open(bad_file, "w") as f:
        f.write("SOME BYTECODE DATA")
        
    with pytest.raises(DocumentValidationError):
        document_service.ingest_document(b_id, bad_file, "BankStatement", "FY25")
