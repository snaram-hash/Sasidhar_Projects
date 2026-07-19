import os
import sqlite3
import logging
from database.db_manager import db
from utils.exceptions import DocumentValidationError
from utils.constants import *
from parsers.bank_parser import BankParser
from parsers.gst_parser import GSTParser
from parsers.itr_parser import ITRParser
from parsers.financial_parser import FinancialParser
from parsers.cibil_parser import CibilParser

logger = logging.getLogger("cuis.extraction_service")

class ExtractionService:
    def __init__(self):
        self.parsers = {
            DOC_BANK_STATEMENT: BankParser(),
            DOC_GST_RETURNS: GSTParser(),
            DOC_ITR: ITRParser(),
            DOC_FINANCIALS: FinancialParser(),
            DOC_CIBIL: CibilParser()
        }

    def extract_and_store(self, borrower_id: int, document_id: int) -> dict:
        """Retrieve document file, run the appropriate parser, and save structured output in the DB."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT file_name, file_type, financial_year FROM Documents WHERE id = ? AND borrower_id = ?", (document_id, borrower_id))
            doc = cursor.fetchone()
            if not doc:
                raise DocumentValidationError(f"Document with ID {document_id} not found for Borrower {borrower_id}.")
                
            file_type = doc["file_type"]
            filename = doc["file_name"]
            fy = doc["financial_year"]
            
            from config.settings import settings
            file_path = os.path.join(settings.UPLOAD_DIR, str(borrower_id), file_type, filename)
            
            if not os.path.exists(file_path):
                raise DocumentValidationError(f"Physical file missing at path: {file_path}")
                
            parser = self.parsers.get(file_type)
            if not parser:
                raise DocumentValidationError(f"No parser defined for document type: {file_type}")
                
            parsed_data = parser.parse(file_path)
            
            if file_type == DOC_BANK_STATEMENT:
                txs = parsed_data.get("transactions", [])
                for tx in txs:
                    cursor.execute(
                        """
                        INSERT INTO BankTransactions (borrower_id, document_id, tx_date, narration, credit, debit, balance)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (borrower_id, document_id, tx["date"].strftime("%Y-%m-%d %H:%M:%S"), tx["narration"], 
                         tx["amount"] if tx["type"] == "CREDIT" else 0.0,
                         tx["amount"] if tx["type"] == "DEBIT" else 0.0,
                         tx["balance"])
                    )
                logger.info(f"Stored {len(txs)} transactions in BankTransactions table.")
                
            elif file_type == DOC_FINANCIALS:
                cursor.execute("SELECT id FROM Financials WHERE borrower_id = ? AND financial_year = ?", (borrower_id, fy or "FY24"))
                row = cursor.fetchone()
                if row:
                    cursor.execute(
                        """
                        UPDATE Financials SET sales=?, pat=?, depreciation=?, interest_paid=?, reserves=?, net_worth=?, current_assets=?, current_liabilities=?, secured_loans=?, unsecured_loans=?, working_capital_limits=?, purchases=?, direct_expenses=?, debtors=?, creditors=?, inventory=?, fixed_assets=?, employee_expenses=?, other_income=?
                        WHERE id = ?
                        """,
                        (parsed_data["sales"], parsed_data["pat"], parsed_data["depreciation"], 
                         parsed_data["interest_paid"], parsed_data["reserves"], parsed_data["net_worth"],
                         parsed_data["current_assets"], parsed_data["current_liabilities"], parsed_data.get("secured_loans", 0.0), parsed_data.get("unsecured_loans", 0.0), parsed_data.get("working_capital_limits", 0.0),
                         parsed_data["purchases"], parsed_data.get("direct_expenses", 0.0), parsed_data["debtors"], parsed_data["creditors"], parsed_data["inventory"], parsed_data["fixed_assets"], parsed_data.get("employee_expenses", 0.0), parsed_data.get("other_income", 0.0), row["id"])
                    )
                else:
                    cursor.execute(
                        """
                        INSERT INTO Financials (borrower_id, financial_year, sales, pat, depreciation, interest_paid, reserves, net_worth, current_assets, current_liabilities, secured_loans, unsecured_loans, working_capital_limits, purchases, direct_expenses, debtors, creditors, inventory, fixed_assets, employee_expenses, other_income)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (borrower_id, fy or "FY24", parsed_data["sales"], parsed_data["pat"], 
                         parsed_data["depreciation"], parsed_data["interest_paid"], parsed_data["reserves"], parsed_data["net_worth"],
                         parsed_data["current_assets"], parsed_data["current_liabilities"], parsed_data.get("secured_loans", 0.0), parsed_data.get("unsecured_loans", 0.0), parsed_data.get("working_capital_limits", 0.0),
                         parsed_data["purchases"], parsed_data.get("direct_expenses", 0.0), parsed_data["debtors"], parsed_data["creditors"], parsed_data["inventory"], parsed_data["fixed_assets"], parsed_data.get("employee_expenses", 0.0), parsed_data.get("other_income", 0.0))
                    )
                logger.info("Stored financial figures in Financials table.")
                
            elif file_type == DOC_GST_RETURNS:
                cursor.execute(
                    """
                    INSERT INTO GSTSales (borrower_id, document_id, filing_period, taxable_sales)
                    VALUES (?, ?, ?, ?)
                    """,
                    (borrower_id, document_id, parsed_data["filing_period"], parsed_data["taxable_sales"])
                )
                logger.info(f"Stored GST outward sales value of {parsed_data['taxable_sales']} in GSTSales table.")
                
            elif file_type == DOC_ITR:
                # 1. Store ITR details
                cursor.execute(
                    """
                    INSERT INTO ITRDetails (borrower_id, document_id, financial_year, gross_income, tax_paid)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (borrower_id, document_id, parsed_data.get("financial_year", fy or "FY24"), parsed_data.get("gross_income", 0.0), parsed_data.get("tax_paid", 0.0))
                )
                logger.info("Stored ITR details in ITRDetails table.")
                
                # 2. Automatically run FinancialParser on the same file to extract audited financials!
                try:
                    logger.info("ITR detected. Automatically extracting audited financials from it...")
                    fin_parser = self.parsers[DOC_FINANCIALS]
                    fin_data = fin_parser.parse(file_path)
                    
                    if fin_data["sales"] > 0.0 or fin_data["net_worth"] != 0.0:
                        cursor.execute("SELECT id FROM Financials WHERE borrower_id = ? AND financial_year = ?", (borrower_id, fy or "FY24"))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute(
                                """
                                UPDATE Financials SET sales=?, pat=?, depreciation=?, interest_paid=?, reserves=?, net_worth=?, current_assets=?, current_liabilities=?, secured_loans=?, unsecured_loans=?, working_capital_limits=?, purchases=?, direct_expenses=?, debtors=?, creditors=?, inventory=?, fixed_assets=?, employee_expenses=?, other_income=?
                                WHERE id = ?
                                """,
                                (fin_data["sales"], fin_data["pat"], fin_data["depreciation"], 
                                 fin_data["interest_paid"], fin_data["reserves"], fin_data["net_worth"],
                                 fin_data["current_assets"], fin_data["current_liabilities"], fin_data.get("secured_loans", 0.0), fin_data.get("unsecured_loans", 0.0), fin_data.get("working_capital_limits", 0.0),
                                 fin_data["purchases"], fin_data.get("direct_expenses", 0.0), fin_data["debtors"], fin_data["creditors"], fin_data["inventory"], fin_data["fixed_assets"], fin_data.get("employee_expenses", 0.0), fin_data.get("other_income", 0.0), row["id"])
                            )
                        else:
                            cursor.execute(
                                """
                                INSERT INTO Financials (borrower_id, financial_year, sales, pat, depreciation, interest_paid, reserves, net_worth, current_assets, current_liabilities, secured_loans, unsecured_loans, working_capital_limits, purchases, direct_expenses, debtors, creditors, inventory, fixed_assets, employee_expenses, other_income)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (borrower_id, fy or "FY24", fin_data["sales"], fin_data["pat"], 
                                 fin_data["depreciation"], fin_data["interest_paid"], fin_data["reserves"], fin_data["net_worth"],
                                 fin_data["current_assets"], fin_data["current_liabilities"], fin_data.get("secured_loans", 0.0), fin_data.get("unsecured_loans", 0.0), fin_data.get("working_capital_limits", 0.0),
                                 fin_data["purchases"], fin_data.get("direct_expenses", 0.0), fin_data["debtors"], fin_data["creditors"], fin_data["inventory"], fin_data["fixed_assets"], fin_data.get("employee_expenses", 0.0), fin_data.get("other_income", 0.0))
                            )
                        logger.info("Automatically populated Financials table from ITR PDF.")
                    else:
                        logger.info("No valid balance sheet or PL detected in ITR PDF. Skipping automatic Financials update.")
                except Exception as e:
                    logger.warning(f"Audited financials not found or failed to parse in ITR PDF: {e}")
                
            elif file_type == DOC_CIBIL:
                cursor.execute(
                    """
                    INSERT INTO RiskAssessments (borrower_id, score, risk_tier)
                    VALUES (?, ?, ?)
                    """,
                    (borrower_id, parsed_data["score"], "Low" if parsed_data["score"] >= 750 else "Medium")
                )
                logger.info("Stored credit score in RiskAssessments table.")
                
            conn.commit()
            return parsed_data
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database error during parser data storage: {e}")
            raise DocumentValidationError(f"Failed to store parsed document data: {e}")
        finally:
            conn.close()

extraction_service = ExtractionService()
