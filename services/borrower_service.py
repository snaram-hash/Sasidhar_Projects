import sqlite3
import logging
from typing import Optional, List
from models.borrower import Borrower
from database.db_manager import db
from utils.exceptions import DocumentValidationError

logger = logging.getLogger("cuis.borrower_service")

class BorrowerService:
    def onboard_borrower(self, borrower: Borrower) -> int:
        """Onboard a new borrower into the system.
        
        Validates business rules and inputs, checks for duplicate PAN/GSTIN in the database,
        and creates a new database record.
        """
        if len(borrower.company_name.strip()) < 2:
            raise DocumentValidationError("Company name must be at least 2 characters long.")
        if not borrower.constitution.strip():
            raise DocumentValidationError("Constitution cannot be empty.")
            
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check for duplicate PAN or GSTIN
            cursor.execute("SELECT id FROM Borrowers WHERE pan = ? OR gstin = ?", (borrower.pan, borrower.gstin))
            if cursor.fetchone():
                raise DocumentValidationError(f"Borrower with PAN {borrower.pan} or GSTIN {borrower.gstin} already exists.")
            
            # Insert record
            cursor.execute(
                """
                INSERT INTO Borrowers (company_name, pan, gstin, industry, constitution)
                VALUES (?, ?, ?, ?, ?)
                """,
                (borrower.company_name, borrower.pan, borrower.gstin, borrower.industry, borrower.constitution)
            )
            borrower_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Successfully onboarded borrower: {borrower.company_name} (ID: {borrower_id})")
            return borrower_id
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error during borrower onboarding: {e}")
            raise DocumentValidationError(f"Failed to onboard borrower: {e}")
        finally:
            conn.close()

    def get_borrower(self, borrower_id: int) -> Optional[Borrower]:
        """Fetch a borrower by ID."""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, company_name, pan, gstin, industry, constitution, created_at FROM Borrowers WHERE id = ?", (borrower_id,))
            row = cursor.fetchone()
            if row:
                # Handle datetime conversion string to datetime
                return Borrower(
                    id=row["id"],
                    company_name=row["company_name"],
                    pan=row["pan"],
                    gstin=row["gstin"],
                    industry=row["industry"],
                    constitution=row["constitution"]
                )
            return None
        finally:
            conn.close()

    def list_borrowers(self) -> List[Borrower]:
        """Fetch all onboarded borrowers."""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, company_name, pan, gstin, industry, constitution FROM Borrowers")
            rows = cursor.fetchall()
            return [
                Borrower(
                    id=row["id"],
                    company_name=row["company_name"],
                    pan=row["pan"],
                    gstin=row["gstin"],
                    industry=row["industry"],
                    constitution=row["constitution"]
                ) for row in rows
            ]
        finally:
            conn.close()

borrower_service = BorrowerService()
