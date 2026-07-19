import re
import logging
import pypdf
from parsers.base_parser import BaseParser
from utils.exceptions import DocumentValidationError

logger = logging.getLogger("cuis.itr_parser")

class ITRParser(BaseParser):
    def parse(self, file_path: str) -> dict:
        logger.info(f"Parsing ITR Document: {file_path}")
        ay = "Unknown"
        income = 0.0
        tax_paid = 0.0
        
        try:
            reader = pypdf.PdfReader(file_path)
            full_text = ""
            for page in reader.pages[:10]:
                full_text += page.extract_text() or ""
                
            m_ay = re.search(r"Assessment\s+Year\s*[:\-]?\s*(\d{4})-\d{2,4}", full_text, re.IGNORECASE)
            if m_ay:
                ay = f"FY{str(int(m_ay.group(1))-1)[2:]}"
            else:
                m_ay2 = re.search(r"Assessment\s+Year\s*[:\-]?\s*(\d{4})", full_text, re.IGNORECASE)
                if m_ay2:
                    ay = f"FY{str(int(m_ay2.group(1))-1)[2:]}"
                    
            m_inc = re.search(r"(?:Gross\s+Total\s+Income|Total\s+Income)\s+([\d,.]+)", full_text, re.IGNORECASE)
            if m_inc:
                income = float(m_inc.group(1).replace(",", ""))
                
            m_tax = re.search(r"(?:Total\s+Tax\s+Paid|Tax\s+Paid|Net\s+Tax\s+Payable)\s+([\d,.]+)", full_text, re.IGNORECASE)
            if m_tax:
                tax_paid = float(m_tax.group(1).replace(",", ""))
                
            return {
                "financial_year": ay,
                "gross_income": income,
                "tax_paid": tax_paid
            }
        except Exception as e:
            logger.error(f"Error parsing ITR PDF: {e}")
            raise DocumentValidationError(f"Failed to parse ITR: {e}")
