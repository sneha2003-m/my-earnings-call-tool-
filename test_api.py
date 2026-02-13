"""
Simple test script to verify the research portal works.
Usage: python test_api.py <path_to_pdf>
"""

import requests
import sys
import json

BASE_URL = "http://localhost:5000"

def test_upload(file_path):
    """Test document upload."""
    print(f"\n1️⃣ Testing Upload: {file_path}")
    print("=" * 60)
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/upload", files=files)
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    if response.status_code == 200:
        return data['document_id']
    else:
        return None

def test_analyze(document_id):
    """Test document analysis."""
    print(f"\n2️⃣ Testing Analysis")
    print("=" * 60)
    
    payload = {"document_id": document_id}
    response = requests.post(
        f"{BASE_URL}/analyze",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2))
    
    return response.status_code == 200

def test_health():
    """Test health endpoint."""
    print(f"\n0️⃣ Testing Health Check")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    return response.status_code == 200

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_api.py <path_to_pdf_or_txt>")
        print("Example: python test_api.py earnings_call.pdf")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print("🧪 Research Portal API Test")
    print("=" * 60)
    
    # Test 1: Health check
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        print("Start server with: python app.py")
        sys.exit(1)
    
    # Test 2: Upload
    document_id = test_upload(file_path)
    if not document_id:
        print("\n❌ Upload failed")
        sys.exit(1)
    
    # Test 3: Analyze
    if test_analyze(document_id):
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Analysis failed")
        sys.exit(1)
