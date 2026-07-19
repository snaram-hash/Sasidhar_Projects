import os
import shutil
import hashlib
import sqlite3
import logging
from typing import Optional, List
from config.settings import settings
from database.db_manager import db
from utils.exceptions import DocumentValidationError

logger = logging.getLogger("cuis.document_service")

class DocumentService:
    def _calculate_md5(self, file_path: str) -> str:
        """Compute MD5 hash of a file."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def ingest_document(self, borrower_id: int, file_path: str, document_type: str, financial_year: Optional[str] = None) -> int:
        """Validate, verify, hash, copy, and register an uploaded document."""
        # Normalize and strip any copy-pasted quotes from path
        file_path = os.path.abspath(os.path.normpath(file_path.strip('"').strip("'")))
        
        if not os.path.exists(file_path):
            raise DocumentValidationError(f"Source file does not exist at: {file_path}")
            
        file_size = os.path.getsize(file_path)
        if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
            raise DocumentValidationError(f"File size {file_size} exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes.")
            
        filename = os.path.basename(file_path)
        ext = filename.split('.')[-1].lower() if '.' in filename else ""
        if ext not in settings.ALLOWED_EXTENSIONS:
            raise DocumentValidationError(f"File extension '.{ext}' is not allowed. Allowed types: {settings.ALLOWED_EXTENSIONS}")

        # Ensure borrower exists
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM Borrowers WHERE id = ?", (borrower_id,))
            if not cursor.fetchone():
                raise DocumentValidationError(f"Borrower with ID {borrower_id} does not exist.")
            
            # Generate MD5 hash for duplicate checks
            file_hash = self._calculate_md5(file_path)
            
            # Check for duplicate document hash across this borrower
            cursor.execute("SELECT id, financial_year FROM Documents WHERE borrower_id = ? AND hash = ?", (borrower_id, file_hash))
            row = cursor.fetchone()
            if row:
                if financial_year and row["financial_year"] != financial_year:
                    cursor.execute("UPDATE Documents SET financial_year = ?, file_type = ? WHERE id = ?", (financial_year, document_type, row["id"]))
                    conn.commit()
                    logger.info(f"Updated financial year for duplicate document ID {row['id']} to {financial_year}")
                return row["id"]
            
            # Set up target path: assets/uploads/{borrower_id}/{document_type}/{filename}
            target_dir = os.path.join(settings.UPLOAD_DIR, str(borrower_id), document_type)
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, filename)
            
            # Copy file
            shutil.copy2(file_path, target_path)
            logger.info(f"Copied file to target path: {target_path}")
            
            # Register in database
            cursor.execute(
                """
                INSERT INTO Documents (borrower_id, file_name, file_type, file_size, financial_year, hash)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (borrower_id, filename, document_type, file_size, financial_year, file_hash)
            )
            doc_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Successfully registered document: {filename} (ID: {doc_id})")
            return doc_id
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error during document ingestion: {e}")
            raise DocumentValidationError(f"Failed to register document: {e}")
        finally:
            conn.close()

    def ingest_folder(self, borrower_id: int, folder_path: str) -> List[dict]:
        """Scan a folder path, automatically detect document types, and ingest all files."""
        import re
        folder_path = os.path.abspath(os.path.normpath(folder_path.strip('"').strip("'")))
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise DocumentValidationError(f"Folder path does not exist or is not a directory: {folder_path}")
            
        ingested_docs = []
        
        for root, _, files in os.walk(folder_path):
            for file in files:
                # Ignore temp and unsupported formats
                if file.startswith("~$") or not file.lower().endswith(('.pdf', '.xlsx', '.csv')):
                    continue
                    
                full_path = os.path.join(root, file)
                path_lower = full_path.lower()
                doc_type = None
                
                # Determine document type based on path keywords
                if "cibil" in path_lower:
                    doc_type = "CIBIL"
                elif "bank" in path_lower or "statement" in path_lower:
                    doc_type = "BankStatement"
                elif "gstr" in path_lower or "gst" in path_lower:
                    doc_type = "GST_Returns"
                elif "itr" in path_lower or "tax return" in path_lower or (("it " in path_lower or "it_" in path_lower) and "full" in path_lower):
                    doc_type = "ITR"
                elif "financial" in path_lower or "audited" in path_lower:
                    doc_type = "AuditedFinancials"
                else:
                    doc_type = "GST_Returns" # fallback
                    
                # Determine financial year if possible
                fy = None
                m_range = re.search(r"(?:\b|_|-)\s*((?:20)?\d{2})\s*[-_]\s*(\d{2})\s*(?:\b|_|-)", path_lower)
                if m_range:
                    fy = f"FY{m_range.group(2)}"
                else:
                    m_fy = re.search(r"fy\s*(\d{2})", path_lower)
                    if m_fy:
                        fy = f"FY{m_fy.group(1)}"
                    else:
                        m_year = re.search(r"\b(20\d{2})\b", path_lower)
                        if m_year:
                            fy = f"FY{m_year.group(1)[2:]}"
                        
                try:
                    doc_id = self.ingest_document(borrower_id, full_path, doc_type, fy)
                    ingested_docs.append({
                        "document_id": doc_id,
                        "file_name": file,
                        "file_type": doc_type,
                        "financial_year": fy,
                        "status": "Ingested"
                    })
                except Exception as e:
                    logger.warning(f"Failed to ingest file {file} in folder walk: {e}")
                    
        return ingested_docs

    def list_documents_for_borrower(self, borrower_id: int) -> List[dict]:
        """Fetch all documents registered for a borrower."""
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, file_name, file_type, file_size, upload_date, financial_year, hash
                FROM Documents WHERE borrower_id = ?
                """,
                (borrower_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

document_service = DocumentService()
