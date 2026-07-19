import sqlite3
import os
import logging
from config.settings import settings
from utils.exceptions import DatabaseConnectionError

logger = logging.getLogger("cuis.database")

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite DB: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {e}")

    def initialize_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Borrowers Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Borrowers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    pan TEXT NOT NULL UNIQUE,
                    gstin TEXT NOT NULL UNIQUE,
                    industry TEXT NOT NULL,
                    constitution TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Documents Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrower_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    financial_year TEXT,
                    hash TEXT UNIQUE,
                    FOREIGN KEY (borrower_id) REFERENCES Borrowers(id)
                );
            """)

            # Financials Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Financials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrower_id INTEGER NOT NULL,
                    financial_year TEXT NOT NULL,
                    sales REAL DEFAULT 0.0,
                    pat REAL DEFAULT 0.0,
                    depreciation REAL DEFAULT 0.0,
                    interest_paid REAL DEFAULT 0.0,
                    reserves REAL DEFAULT 0.0,
                    net_worth REAL DEFAULT 0.0,
                    current_assets REAL DEFAULT 0.0,
                    current_liabilities REAL DEFAULT 0.0,
                    secured_loans REAL DEFAULT 0.0,
                    unsecured_loans REAL DEFAULT 0.0,
                    working_capital_limits REAL DEFAULT 0.0,
                    purchases REAL DEFAULT 0.0,
                    direct_expenses REAL DEFAULT 0.0,
                    debtors REAL DEFAULT 0.0,
                    creditors REAL DEFAULT 0.0,
                    inventory REAL DEFAULT 0.0,
                    fixed_assets REAL DEFAULT 0.0,
                    employee_expenses REAL DEFAULT 0.0,
                    other_income REAL DEFAULT 0.0,
                    FOREIGN KEY (borrower_id) REFERENCES Borrowers(id),
                    UNIQUE(borrower_id, financial_year)
                );
            """)

            # Dynamic migrations for Financials columns
            new_cols = {
                "purchases": "REAL DEFAULT 0.0",
                "direct_expenses": "REAL DEFAULT 0.0",
                "debtors": "REAL DEFAULT 0.0",
                "creditors": "REAL DEFAULT 0.0",
                "inventory": "REAL DEFAULT 0.0",
                "fixed_assets": "REAL DEFAULT 0.0",
                "employee_expenses": "REAL DEFAULT 0.0",
                "other_income": "REAL DEFAULT 0.0"
            }
            for col_name, col_def in new_cols.items():
                try:
                    cursor.execute(f"ALTER TABLE Financials ADD COLUMN {col_name} {col_def}")
                except sqlite3.OperationalError:
                    pass

            # BankTransactions Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS BankTransactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrower_id INTEGER NOT NULL,
                    document_id INTEGER NOT NULL,
                    tx_date TIMESTAMP NOT NULL,
                    narration TEXT NOT NULL,
                    credit REAL DEFAULT 0.0,
                    debit REAL DEFAULT 0.0,
                    balance REAL NOT NULL,
                    instrument_id TEXT,
                    FOREIGN KEY (borrower_id) REFERENCES Borrowers(id),
                    FOREIGN KEY (document_id) REFERENCES Documents(id)
                );
            """)

            # RiskAssessments Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS RiskAssessments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrower_id INTEGER NOT NULL,
                    score REAL NOT NULL,
                    risk_tier TEXT NOT NULL,
                    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (borrower_id) REFERENCES Borrowers(id)
                );
            """)

            # CAMHistory Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS CAMHistory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrower_id INTEGER NOT NULL,
                    cam_path TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'Draft',
                    underwriter_notes TEXT,
                    FOREIGN KEY (borrower_id) REFERENCES Borrowers(id)
                );
            """)

            # ApplicationLogs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ApplicationLogs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    log_level TEXT NOT NULL,
                    module TEXT NOT NULL,
                    message TEXT NOT NULL,
                    stack_trace TEXT
                );
            """)

            # GSTSales Table (New in Sprint 4)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS GSTSales (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrower_id INTEGER NOT NULL,
                    document_id INTEGER NOT NULL,
                    filing_period TEXT NOT NULL,
                    taxable_sales REAL NOT NULL,
                    FOREIGN KEY (borrower_id) REFERENCES Borrowers(id),
                    FOREIGN KEY (document_id) REFERENCES Documents(id)
                );
            """)

            # ITRDetails Table (New in Sprint 4)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ITRDetails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    borrower_id INTEGER NOT NULL,
                    document_id INTEGER NOT NULL,
                    financial_year TEXT NOT NULL,
                    gross_income REAL NOT NULL,
                    tax_paid REAL NOT NULL,
                    FOREIGN KEY (borrower_id) REFERENCES Borrowers(id),
                    FOREIGN KEY (document_id) REFERENCES Documents(id)
                );
            """)
            
            conn.commit()
            logger.info("Successfully initialized all database tables.")
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"SQL execution error during database initialization: {e}")
            raise DatabaseConnectionError(f"Database schema initialization failed: {e}")
        finally:
            conn.close()

db = DatabaseManager(settings.DATABASE_PATH)
