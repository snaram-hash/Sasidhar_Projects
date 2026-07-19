import sqlite3
import logging
from database.db_manager import db

logger = logging.getLogger("cuis.validation_service")

class ValidationService:
    def validate_borrower_data(self, borrower_id: int, financial_year: str) -> dict:
        """Perform cross-source data validation and reconciliation.
        
        Validates:
        1. GST Sales vs Audited Sales (Variance within 10%)
        2. Bank credits (BTO) vs Audited Sales (Variance within 15%)
        3. ITR Gross Income vs Audited Sales (Variance within 5%)
        4. Negative values check in key audited variables
        """
        conn = db.get_connection()
        cursor = conn.cursor()
        
        report = {
            "borrower_id": borrower_id,
            "financial_year": financial_year,
            "status": "PASSED",
            "checks": {}
        }
        
        try:
            # 1. Fetch Audited Financials
            cursor.execute(
                """
                SELECT sales, pat, depreciation, net_worth, current_assets, current_liabilities
                FROM Financials WHERE borrower_id = ? AND financial_year = ?
                """,
                (borrower_id, financial_year)
            )
            fin = cursor.fetchone()
            if not fin:
                report["status"] = "FAILED"
                report["checks"]["audited_financials"] = {
                    "status": "FAILED",
                    "message": "Missing audited financials."
                }
                return report
                
            audited_sales = fin["sales"]
            
            # Check for negative values
            negatives = []
            for col in ["sales", "pat", "net_worth", "current_assets", "current_liabilities"]:
                if fin[col] is not None and fin[col] < 0:
                    negatives.append(f"{col} ({fin[col]})")
            
            if negatives:
                report["status"] = "WARNING"
                report["checks"]["negative_values"] = {
                    "status": "WARNING",
                    "message": f"Negative value(s) flagged: {', '.join(negatives)}. Manual review recommended."
                }
            else:
                report["checks"]["negative_values"] = {
                    "status": "PASSED",
                    "message": "No negative values detected in key balance sheet/P&L accounts."
                }

            # 2. Reconcile GST Outward Sales
            # Sum taxable sales from GSTSales table for GSTR-3B filings uploaded for this borrower
            cursor.execute(
                """
                SELECT SUM(taxable_sales) as total_gst
                FROM GSTSales WHERE borrower_id = ?
                """,
                (borrower_id,)
            )
            gst_row = cursor.fetchone()
            total_gst_sales = gst_row["total_gst"] if gst_row["total_gst"] is not None else 0.0
            
            if total_gst_sales == 0.0:
                report["checks"]["gst_reconciliation"] = {
                    "status": "WARNING",
                    "message": "No GST sales records found. GST validation skipped."
                }
                if report["status"] != "FAILED":
                    report["status"] = "WARNING"
            else:
                gst_variance = abs(total_gst_sales - audited_sales) / audited_sales if audited_sales > 0 else 0.0
                if gst_variance <= 0.10:
                    report["checks"]["gst_reconciliation"] = {
                        "status": "PASSED",
                        "message": f"GST-declared sales (Rs. {total_gst_sales:,.2f}) aligns with Audited Sales (Rs. {audited_sales:,.2f}). Variance: {gst_variance:.2%}."
                    }
                else:
                    report["checks"]["gst_reconciliation"] = {
                        "status": "FAILED",
                        "message": f"GST sales (Rs. {total_gst_sales:,.2f}) mismatch with Audited Sales (Rs. {audited_sales:,.2f}). Variance: {gst_variance:.2%} exceeds 10% limit."
                    }
                    report["status"] = "FAILED"

            # 3. Reconcile Bank Statement Credits (BTO)
            cursor.execute(
                """
                SELECT SUM(credit) as total_credits
                FROM BankTransactions WHERE borrower_id = ?
                """,
                (borrower_id,)
            )
            bank_row = cursor.fetchone()
            total_credits = bank_row["total_credits"] if bank_row["total_credits"] is not None else 0.0
            
            if total_credits == 0.0:
                report["checks"]["bank_reconciliation"] = {
                    "status": "WARNING",
                    "message": "No bank statement transactions found. Bank reconciliation skipped."
                }
                if report["status"] != "FAILED":
                    report["status"] = "WARNING"
            else:
                # Bank credits should offset business turnover (BTO check)
                # Credits should align with sales (within 15% normally)
                bto_variance = abs(total_credits - audited_sales) / audited_sales if audited_sales > 0 else 0.0
                if bto_variance <= 0.15:
                    report["checks"]["bank_reconciliation"] = {
                        "status": "PASSED",
                        "message": f"Banking credit turnover (Rs. {total_credits:,.2f}) aligns with Audited Sales (Rs. {audited_sales:,.2f}). Variance: {bto_variance:.2%}."
                    }
                else:
                    # In logistics/shipping, bank credits are sometimes higher due to freight forwarding deposits.
                    # Underwriting rules recommend warning or failure depending on how high it goes.
                    report["checks"]["bank_reconciliation"] = {
                        "status": "WARNING",
                        "message": f"Banking credits (Rs. {total_credits:,.2f}) deviate from Audited Sales (Rs. {audited_sales:,.2f}). Variance: {bto_variance:.2%} exceeds 15% threshold."
                    }
                    if report["status"] == "PASSED":
                        report["status"] = "WARNING"

            # 4. Reconcile ITR gross income vs Audited Sales
            cursor.execute(
                """
                SELECT gross_income FROM ITRDetails
                WHERE borrower_id = ? AND financial_year = ?
                """,
                (borrower_id, financial_year)
            )
            itr_row = cursor.fetchone()
            if not itr_row:
                report["checks"]["itr_reconciliation"] = {
                    "status": "WARNING",
                    "message": f"No ITR details found for {financial_year}. ITR validation skipped."
                }
                if report["status"] != "FAILED":
                    report["status"] = "WARNING"
            else:
                itr_inc = itr_row["gross_income"]
                itr_variance = abs(itr_inc - audited_sales) / audited_sales if audited_sales > 0 else 0.0
                if itr_variance <= 0.05:
                    report["checks"]["itr_reconciliation"] = {
                        "status": "PASSED",
                        "message": f"ITR Income (Rs. {itr_inc:,.2f}) matches Audited Sales (Rs. {audited_sales:,.2f}). Variance: {itr_variance:.2%}."
                    }
                else:
                    report["checks"]["itr_reconciliation"] = {
                        "status": "FAILED",
                        "message": f"ITR Income (Rs. {itr_inc:,.2f}) mismatches Audited Sales (Rs. {audited_sales:,.2f}). Variance: {itr_variance:.2%} exceeds 5% limit."
                    }
                    report["status"] = "FAILED"
                    
            return report
        except sqlite3.Error as e:
            logger.error(f"Database error during validation checks: {e}")
            report["status"] = "FAILED"
            report["checks"]["system_error"] = {
                "status": "FAILED",
                "message": f"Reconciliation crashed: {e}"
            }
            return report
        finally:
            conn.close()

validation_service = ValidationService()
