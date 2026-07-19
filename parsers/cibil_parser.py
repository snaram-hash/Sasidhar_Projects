import re
import logging
import pypdf
from parsers.base_parser import BaseParser
from utils.exceptions import DocumentValidationError

logger = logging.getLogger("cuis.cibil_parser")

class CibilParser(BaseParser):
    def parse(self, file_path: str) -> dict:
        logger.info(f"Parsing CIBIL Bureau Report: {file_path}")
        score = 300
        dpd_count = 0
        active_loans = 0
        enquiries = 0
        
        try:
            reader = pypdf.PdfReader(file_path)
            full_text = ""
            for page in reader.pages:
                full_text += page.extract_text() or ""
                
            m_score = re.search(r"(?:CIBIL\s+Score|Bureau\s+Score|Score)\s*[:\-]?\s*(\d{3})", full_text, re.IGNORECASE)
            if m_score:
                score = int(m_score.group(1))
            else:
                m_score2 = re.search(r"\b([5-8]\d{2})\b", full_text)
                if m_score2:
                    score = int(m_score2.group(1))
                    
            m_loans = re.search(r"(?:Total\s+Accounts|Active\s+Accounts|Account\s+Summary)\s*[:\-]?\s*(\d+)", full_text, re.IGNORECASE)
            if m_loans:
                active_loans = int(m_loans.group(1))
                
            m_enq = re.search(r"(?:Enquiries\s+in\s+last\s+24\s+months|Total\s+Enquiries)\s*[:\-]?\s*(\d+)", full_text, re.IGNORECASE)
            if m_enq:
                enquiries = int(m_enq.group(1))
                
            dpd_patterns = [
                r"\b(90\+?\s*DPD|60\+?\s*DPD|30\+?\s*DPD)\b",
                r"(\b\d+[ \t]+days[ \t]+past[ \t]+due\b)"
            ]
            for p in dpd_patterns:
                if re.search(p, full_text, re.IGNORECASE):
                    dpd_count += 1
                    
            return {
                "score": score,
                "active_loans": active_loans,
                "enquiries": enquiries,
                "dpd_count": dpd_count
            }
        except Exception as e:
            logger.error(f"Error parsing CIBIL PDF: {e}")
            raise DocumentValidationError(f"Failed to parse CIBIL report: {e}")
