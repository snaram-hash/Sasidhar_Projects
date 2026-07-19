import os
import re
import logging
import pypdf
from datetime import datetime
from parsers.base_parser import BaseParser
from utils.exceptions import DocumentValidationError

logger = logging.getLogger("cuis.bank_parser")

class BankParser(BaseParser):
    def parse_amount(self, val_str: str) -> float:
        if not val_str:
            return 0.0
        val_str = val_str.replace(",", "").strip()
        return float(val_str)

    def parse_balance(self, val_str: str) -> float:
        if not val_str:
            return 0.0
        val_str = val_str.replace(",", "").strip()
        is_neg = False
        if val_str.startswith("(") and val_str.endswith(")"):
            is_neg = True
            val_str = val_str[1:-1]
        elif val_str.endswith("CR") or val_str.endswith("cr"):
            val_str = val_str[:-2].strip()
        elif val_str.endswith("DR") or val_str.endswith("dr"):
            is_neg = True
            val_str = val_str[:-2].strip()
        val = float(val_str)
        return -val if is_neg else val

    def parse_date(self, date_str: str) -> datetime:
        date_str = date_str.strip()
        for fmt in ["%Y-%m-%d", "%d-%b-%y", "%d-%b-%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                pass
        raise ValueError(f"Unknown date format: {date_str}")

    def parse(self, file_path: str) -> dict:
        logger.info(f"Parsing Bank Statement: {file_path}")
        
        bank_name = "Unknown Bank"
        ac_no = "Unknown"
        limit = 0.0
        
        filename_lower = os.path.basename(file_path).lower()
        if "au" in filename_lower:
            bank_name = "AU SMALL FINANCE BANK"
        elif "hdfc" in filename_lower:
            bank_name = "HDFC BANK"
        elif "icici" in filename_lower:
            bank_name = "ICICI BANK"
            
        try:
            reader = pypdf.PdfReader(file_path)
            first_page_text = reader.pages[0].extract_text() or ""
            first_page_lower = first_page_text.lower()
            
            if "au small finance" in first_page_lower:
                bank_name = "AU SMALL FINANCE BANK"
            elif "hdfc bank" in first_page_lower:
                bank_name = "HDFC BANK"
            elif "icici bank" in first_page_lower:
                bank_name = "ICICI BANK"
                
            m_ac = re.search(r"Account\s+No\.\s*[:\-]?\s*(\d{5,})", first_page_text, re.IGNORECASE)
            if m_ac:
                ac_no = m_ac.group(1)
            
            tx_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2}|\d{1,2}-[A-Za-z]{3}-\d{2,4}|\d{1,2}/\d{1,2}/\d{2,4})\s*(.*?)\s+(\d[\d,.]*)\s+(\(?\d[\d,.]*\)?(?:\s*[CD]R)?)$")
            
            transactions = []
            for p in range(len(reader.pages)):
                text = reader.pages[p].extract_text() or ""
                for line in text.split('\n'):
                    m = tx_pattern.match(line.strip())
                    if m:
                        try:
                            dt = self.parse_date(m.group(1))
                            amt = self.parse_amount(m.group(3))
                            bal = self.parse_balance(m.group(4))
                            nar = m.group(2).strip()
                            
                            transactions.append({
                                "date": dt,
                                "narration": nar,
                                "amount": amt,
                                "balance": bal
                            })
                        except Exception as ex:
                            logger.warning(f"Failed to parse transaction line: {line.strip()}. Error: {ex}")
            
            if transactions:
                for i in range(len(transactions)):
                    if i == 0:
                        transactions[i]["type"] = "DEBIT"
                    else:
                        diff = transactions[i]["balance"] - transactions[i-1]["balance"]
                        if diff > 0.01:
                            transactions[i]["type"] = "CREDIT"
                        else:
                            transactions[i]["type"] = "DEBIT"
                            
            return {
                "bank_name": bank_name,
                "account_no": ac_no,
                "limit": limit,
                "transactions": transactions
            }
        except Exception as e:
            logger.error(f"Error parsing PDF bank statement: {e}")
            raise DocumentValidationError(f"Failed to parse bank statement: {e}")
