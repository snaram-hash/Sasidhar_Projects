import sqlite3
import logging
from database.db_manager import db

logger = logging.getLogger("cuis.policy_engine")

class PolicyEngine:
    def calculate_credit_metrics(self, borrower_id: int, financial_year: str) -> dict:
        """Query raw database values and compute underwriting financial ratios and indicators."""
        conn = db.get_connection()
        cursor = conn.cursor()
        
        metrics = {
            "current_ratio": 0.0,
            "dscr": 0.0,
            "debt_to_equity": 0.0,
            "interest_coverage": 0.0,
            "cibil_score": 300,
            "cheque_bounces": 0
        }
        
        try:
            # 1. Fetch Audited Financials
            cursor.execute(
                """
                SELECT sales, pat, depreciation, interest_paid, reserves, net_worth, current_assets, current_liabilities, secured_loans, unsecured_loans
                FROM Financials WHERE borrower_id = ? AND financial_year = ?
                """,
                (borrower_id, financial_year)
            )
            fin = cursor.fetchone()
            if fin:
                ca = fin["current_assets"] or 0.0
                cl = fin["current_liabilities"] or 0.0
                pat = fin["pat"] or 0.0
                dep = fin["depreciation"] or 0.0
                interest = fin["interest_paid"] or 0.0
                nw = fin["net_worth"] or 0.0
                sec_loans = fin["secured_loans"] or 0.0
                unsec_loans = fin["unsecured_loans"] or 0.0
                
                # Ratios
                metrics["current_ratio"] = ca / cl if cl > 0 else (99.0 if ca > 0 else 0.0)
                metrics["dscr"] = (pat + dep + interest) / interest if interest > 0 else (99.0 if (pat + dep) > 0 else 0.0)
                
                total_debt = sec_loans + unsec_loans
                metrics["debt_to_equity"] = total_debt / nw if nw > 0 else (99.0 if total_debt > 0 else 0.0)
                metrics["interest_coverage"] = (pat + interest) / interest if interest > 0 else (99.0 if pat > 0 else 0.0)

            # 2. Fetch CIBIL Score
            cursor.execute(
                """
                SELECT score FROM RiskAssessments WHERE borrower_id = ? ORDER BY id DESC LIMIT 1
                """,
                (borrower_id,)
            )
            cibil = cursor.fetchone()
            if cibil:
                metrics["cibil_score"] = int(cibil["score"])

            # 3. Sum Cheque Bounces
            cursor.execute(
                """
                SELECT COUNT(*) as bounce_count FROM BankTransactions 
                WHERE borrower_id = ? AND (
                    LOWER(narration) LIKE '%inward return%' OR 
                    LOWER(narration) LIKE '%outward return%' OR 
                    LOWER(narration) LIKE '%cheque return%' OR 
                    LOWER(narration) LIKE '%chq ret%' OR 
                    LOWER(narration) LIKE '%insufficient%'
                )
                """,
                (borrower_id,)
            )
            bounce_row = cursor.fetchone()
            if bounce_row:
                metrics["cheque_bounces"] = bounce_row["bounce_count"]
                
            return metrics
        finally:
            conn.close()

    def evaluate_policy(self, borrower_id: int, financial_year: str) -> dict:
        """Run policy rules and assign a risk tier and status."""
        metrics = self.calculate_credit_metrics(borrower_id, financial_year)
        
        rules = {
            "R001": {
                "name": "Current Ratio",
                "value": metrics["current_ratio"],
                "threshold": ">= 1.0",
                "status": "PASSED" if metrics["current_ratio"] >= 1.0 else "FAILED",
                "severity": "High",
                "flag": "Flag Liquidity"
            },
            "R002": {
                "name": "DSCR",
                "value": metrics["dscr"],
                "threshold": ">= 1.2",
                "status": "PASSED" if metrics["dscr"] >= 1.2 else "FAILED",
                "severity": "High",
                "flag": "Flag Repayment"
            },
            "R003": {
                "name": "Debt-to-Equity",
                "value": metrics["debt_to_equity"],
                "threshold": "<= 3.0",
                "status": "PASSED" if metrics["debt_to_equity"] <= 3.0 else "FAILED",
                "severity": "Medium",
                "flag": "High Leverage"
            },
            "R004": {
                "name": "CIBIL Score",
                "value": metrics["cibil_score"],
                "threshold": ">= 700",
                "status": "PASSED" if metrics["cibil_score"] >= 700 else "FAILED",
                "severity": "Medium",
                "flag": "Manual Review Required"
            },
            "R005": {
                "name": "Cheque Bounces",
                "value": metrics["cheque_bounces"],
                "threshold": "<= 3",
                "status": "PASSED" if metrics["cheque_bounces"] <= 3 else "FAILED",
                "severity": "High",
                "flag": "Excessive Bounces"
            }
        }
        
        has_high_failure = any(r["status"] == "FAILED" and r["severity"] == "High" for r in rules.values())
        has_medium_failure = any(r["status"] == "FAILED" and r["severity"] == "Medium" for r in rules.values())
        
        if has_high_failure:
            risk_tier = "High"
        elif has_medium_failure:
            risk_tier = "Medium"
        else:
            risk_tier = "Low"
            
        passed_rules = sum(1 for r in rules.values() if r["status"] == "PASSED")
        score = (passed_rules / len(rules)) * 100.0
        
        conn = db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO RiskAssessments (borrower_id, score, risk_tier)
                VALUES (?, ?, ?)
                """,
                (borrower_id, score, risk_tier)
            )
            conn.commit()
        finally:
            conn.close()
            
        return {
            "borrower_id": borrower_id,
            "financial_year": financial_year,
            "risk_tier": risk_tier,
            "score": score,
            "rules": rules
        }

policy_engine = PolicyEngine()
