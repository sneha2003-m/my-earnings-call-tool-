"""
Flask Research Portal Application
Earnings Call / Management Commentary Analysis Tool
Frontend handles all file processing - backend only analyzes text
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from dotenv import load_dotenv

from utils.text_processor import chunk_text, needs_chunking
from utils.gemini_analyzer import analyze_document
from utils.validator import validate_analysis_output, sanitize_output

# Load environment variables
load_dotenv()

# Get GitHub token from environment
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN not found in environment variables")

# Ensure it's a string (Render sometimes passes as different types)
GITHUB_TOKEN = str(GITHUB_TOKEN).strip()

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Configuration
MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 20))
MAX_TEXT_LENGTH = MAX_FILE_SIZE_MB * 1024 * 1024  # Max text length in characters

# In-memory storage for document texts
documents = {}


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/upload', methods=['POST'])
def upload():
    """
    Receive extracted text from frontend.
    Frontend handles all file processing (PDF extraction, OCR, text reading).
    
    Request: JSON with 'text' and 'filename'
    Response: document_id and text_length
    """
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({"error": "No text provided. Frontend must extract text from files."}), 400
        
        text = data['text']
        filename = data.get('filename', 'document.txt')
        
        # Validate text
        if not text or not text.strip():
            return jsonify({"error": "Empty text received. Please ensure file has content."}), 400
        
        if len(text) > MAX_TEXT_LENGTH:
            return jsonify({
                "error": f"Text too large. Maximum {MAX_FILE_SIZE_MB}MB allowed."
            }), 413
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Store text in memory
        documents[document_id] = {
            'text': text,
            'filename': filename
        }
        
        return jsonify({
            "document_id": document_id,
            "filename": filename,
            "text_length": len(text),
            "status": "ready",
            "message": "Text received successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze uploaded document using GitHub Models AI.
    
    Request: JSON with document_id
    Response: Structured analysis result
    """
    # Check API key
    if not GITHUB_TOKEN:
        return jsonify({
            "error": "GITHUB_TOKEN not configured. Please set it in .env file"
        }), 500
    
    # Get document_id from request
    data = request.get_json()
    if not data or 'document_id' not in data:
        return jsonify({"error": "document_id required in request body"}), 400
    
    document_id = data['document_id']
    
    # Check if document exists
    if document_id not in documents:
        return jsonify({"error": "Document not found. Please upload first."}), 404
    
    try:
        # Get document text
        doc = documents[document_id]
        text = doc['text']
        
        # Check if chunking is needed (gpt-4o has 8000 token limit)
        chunks = None
        if needs_chunking(text, max_tokens=6000):  # Leave margin for prompt overhead
            chunks = chunk_text(text, max_tokens=6000)
        
        # Analyze using GitHub Models
        try:
            result = analyze_document(GITHUB_TOKEN, text, chunks)
        except Exception as api_error:
            return jsonify({
                "error": f"AI API error: {str(api_error)}",
                "error_type": type(api_error).__name__
            }), 500
        
        # Sanitize output
        try:
            result = sanitize_output(result)
        except Exception as sanitize_error:
            return jsonify({
                "error": f"Output sanitization error: {str(sanitize_error)}",
                "error_type": type(sanitize_error).__name__,
                "raw_result": str(result)[:500]  # First 500 chars for debugging
            }), 500
        
        # Validate output
        is_valid, error_msg = validate_analysis_output(result)
        if not is_valid:
            return jsonify({
                "error": f"Analysis output validation failed: {error_msg}",
                "raw_output": result
            }), 500
        
        # Remove from documents dictionary after successful analysis
        documents.pop(document_id, None)
        
        return jsonify({
            "document_id": document_id,
            "filename": doc['filename'],
            "analysis": result,
            "status": "completed"
        }), 200
        
    except Exception as e:
        return jsonify({
            "error": f"Analysis failed: {str(e)}",
            "error_type": type(e).__name__
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "research-portal"}), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True') == 'True'
    app.run(host='0.0.0.0', port=port, debug=debug)
