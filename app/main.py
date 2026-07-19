import os
import sys
import json
import logging
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from logging.handlers import RotatingFileHandler

# Add parent directory to path so imports work correctly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from database.db_manager import db
from models.borrower import Borrower
from services.borrower_service import borrower_service
from services.document_service import document_service
from services.extraction_service import extraction_service
from services.validation_service import validation_service
from services.cam_service import cam_service
from services.export_service import export_service
from engines.policy_engine import policy_engine

logger = logging.getLogger("cuis.webserver")

def serialize_obj(obj):
    if isinstance(obj, dict):
        return {k: serialize_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_obj(i) for i in obj]
    elif hasattr(obj, 'strftime'):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    return obj

class CUISHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info("%s - [%s] %s" % (self.address_string(), self.log_date_time_string(), format%args))

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)

        # API: GET List Borrowers
        if path == "/api/borrowers":
            try:
                borrowers = borrower_service.list_borrowers()
                # Convert Pydantic models to dicts
                borrower_dicts = []
                for b in borrowers:
                    d = b.dict() if hasattr(b, 'dict') else b.model_dump()
                    borrower_dicts.append(d)
                self._set_headers(200)
                self.wfile.write(json.dumps(serialize_obj(borrower_dicts)).encode('utf-8'))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: GET List Documents
        elif path == "/api/documents":
            try:
                b_id = int(query.get("borrower_id", [0])[0])
                docs = document_service.list_documents_for_borrower(b_id)
                self._set_headers(200)
                self.wfile.write(json.dumps(serialize_obj(docs)).encode('utf-8'))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: GET Reconciliation report
        elif path == "/api/reconcile":
            try:
                b_id = int(query.get("borrower_id", [0])[0])
                fy = query.get("fy", ["FY24"])[0]
                report = validation_service.validate_borrower_data(b_id, fy)
                self._set_headers(200)
                self.wfile.write(json.dumps(serialize_obj(report)).encode('utf-8'))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: GET Policy engine scorecard
        elif path == "/api/policy":
            try:
                b_id = int(query.get("borrower_id", [0])[0])
                fy = query.get("fy", ["FY24"])[0]
                result = policy_engine.evaluate_policy(b_id, fy)
                self._set_headers(200)
                self.wfile.write(json.dumps(serialize_obj(result)).encode('utf-8'))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        # Serve static UI files
        ui_dir = os.path.join(settings.BASE_DIR, "ui")
        file_name = path.lstrip("/")
        if file_name == "" or file_name == "/":
            file_name = "index.html"

        target_file = os.path.join(ui_dir, file_name)
        if os.path.exists(target_file) and os.path.isfile(target_file):
            content_type = "text/html"
            if file_name.endswith(".css"):
                content_type = "text/css"
            elif file_name.endswith(".js"):
                content_type = "application/javascript"
            elif file_name.endswith(".png"):
                content_type = "image/png"
            elif file_name.endswith(".jpg") or file_name.endswith(".jpeg"):
                content_type = "image/jpeg"
            elif file_name.endswith(".svg"):
                content_type = "image/svg+xml"
                
            self._set_headers(200, content_type=content_type)
            with open(target_file, "rb") as f:
                self.wfile.write(f.read())
        else:
            self._set_headers(404, content_type="text/plain")
            self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8'))
        except Exception:
            body = {}

        # API: POST Onboard borrower
        if path == "/api/borrowers":
            try:
                b = Borrower(
                    company_name=body.get("company_name", ""),
                    pan=body.get("pan", "").upper(),
                    gstin=body.get("gstin", "").upper(),
                    industry=body.get("industry", ""),
                    constitution=body.get("constitution", "")
                )
                b_id = borrower_service.onboard_borrower(b)
                self._set_headers(200)
                self.wfile.write(json.dumps({"borrower_id": b_id, "success": True}).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: POST Ingest Document
        elif path == "/api/documents":
            try:
                b_id = int(body.get("borrower_id", 0))
                file_path = body.get("file_path", "")
                doc_type = body.get("file_type", "")
                fy = body.get("financial_year", None)
                if not fy:
                    fy = None
                
                doc_id = document_service.ingest_document(b_id, file_path, doc_type, fy)
                # Auto-extract data immediately
                try:
                    extraction_service.extract_and_store(b_id, doc_id)
                except Exception as ext_err:
                    logger.warning(f"Auto-extraction failed for doc {doc_id}: {ext_err}")
                
                self._set_headers(200)
                self.wfile.write(json.dumps({"document_id": doc_id, "success": True}).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: POST Ingest Folder (Bulk)
        elif path == "/api/ingest_folder":
            try:
                b_id = int(body.get("borrower_id", 0))
                folder_path = body.get("folder_path", "")
                
                ingested = document_service.ingest_folder(b_id, folder_path)
                # Auto-extract data for all files immediately
                for doc in ingested:
                    try:
                        extraction_service.extract_and_store(b_id, doc["document_id"])
                        doc["status"] = "Parsed & Extracted"
                    except Exception as ext_err:
                        logger.warning(f"Auto-extraction failed for bulk doc {doc['document_id']}: {ext_err}")
                        doc["status"] = "Failed Auto-Extract"
                        
                self._set_headers(200)
                self.wfile.write(json.dumps({"data": serialize_obj(ingested), "success": True}).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: POST Extract data
        elif path == "/api/extract":
            try:
                b_id = int(body.get("borrower_id", 0))
                doc_id = int(body.get("document_id", 0))
                extracted = extraction_service.extract_and_store(b_id, doc_id)
                
                # Datetimes need string serialization
                def serialize_dt(obj):
                    if isinstance(obj, dict):
                        return {k: serialize_dt(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [serialize_dt(i) for i in obj]
                    elif hasattr(obj, 'strftime'):
                        return obj.strftime("%Y-%m-%d")
                    return obj
                    
                self._set_headers(200)
                self.wfile.write(json.dumps({"data": serialize_dt(extracted), "success": True}).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: POST Generate Excel CAM workbook
        elif path == "/api/generate_cam":
            try:
                b_id = int(body.get("borrower_id", 0))
                fy = body.get("fy", "FY24")
                export_path = cam_service.generate_cam(b_id, fy)
                self._set_headers(200)
                self.wfile.write(json.dumps({"path": export_path, "success": True}).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return
            
        # API: POST Generate Web dashboard
        elif path == "/api/generate_dashboard":
            try:
                b_id = int(body.get("borrower_id", 0))
                export_path = export_service.compile_and_export_dashboard(b_id)
                self._set_headers(200)
                self.wfile.write(json.dumps({"path": export_path, "success": True}).encode('utf-8'))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode('utf-8'))

def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    file_handler = RotatingFileHandler(
        settings.LOG_FILE_PATH,
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)

def run():
    setup_logging()
    logger = logging.getLogger("cuis.main")
    
    db.initialize_tables()
    
    if os.getenv("CUIS_NON_INTERACTIVE") == "1":
        logger.info("Non-interactive run detected. Booting database and stopping.")
        return

    # Start the HTTP API & GUI Web Server
    server_address = ('', 5000)
    httpd = HTTPServer(server_address, CUISHTTPRequestHandler)
    print("\n====================================================")
    print("      Credit Underwriting Intelligence Suite (CUIS)")
    print("====================================================")
    print("Server running successfully!")
    print("Open your browser and navigate to: http://localhost:5000")
    print("Press Ctrl+C to terminate.")
    print("====================================================\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server. Goodbye!")

if __name__ == "__main__":
    run()
