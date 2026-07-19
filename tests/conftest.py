import pytest
import os
import sys
import tempfile
import shutil

# Make sure imports resolved
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

@pytest.fixture
def temp_db(temp_dir):
    db_path = os.path.join(temp_dir, "test_cuis.db")
    from database.db_manager import db
    original_path = db.db_path
    db.db_path = db_path
    db.initialize_tables()
    yield db
    db.db_path = original_path
