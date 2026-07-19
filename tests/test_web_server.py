import pytest
import threading
import time
import urllib.request
import json
from http.server import HTTPServer
from app.main import CUISHTTPRequestHandler

@pytest.fixture
def run_test_server(temp_db):
    server = HTTPServer(('127.0.0.1', 8089), CUISHTTPRequestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    time.sleep(0.5) # Allow server boot
    yield "http://127.0.0.1:8089"
    server.shutdown()
    thread.join()

def test_borrowers_api_list(run_test_server):
    url = f"{run_test_server}/api/borrowers"
    response = urllib.request.urlopen(url)
    assert response.status == 200
    data = json.loads(response.read().decode('utf-8'))
    assert isinstance(data, list)
