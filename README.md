# Research Portal - Earnings Call Analysis Tool

A deterministic research tool that analyzes earnings call transcripts and management discussions using Google Gemini API with strict hallucination prevention.

## 🎯 Overview

This is **NOT a chatbot**. It's a structured research tool that:
- Extracts text from PDF/TXT documents
- Analyzes management tone, guidance, and sentiment
- Returns JSON output with explicit "Not mentioned" for missing data
- **Prevents hallucination** through strict prompt engineering

---

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.11+
- Google Gemini API Key ([Get it here](https://aistudio.google.com/app/apikey))

### 2. Installation

```bash
# Clone or download the project
cd research-portal

# Create virtual environment (optional but recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file with your API key:

```bash
# Copy template
cp .env.example .env

# Edit .env and add your key
GOOGLE_GEMINI_API_KEY=your_actual_api_key_here
```

### 4. Run the Application

```bash
python app.py
```

Server will start at: `http://localhost:5000`

---

## 📡 API Usage

### **Endpoint 1: Upload Document (frontend-first)**

The frontend extracts text from PDF/TXT files (using `pdf.js` + optional OCR) and sends the raw text to the backend.

Request:

```bash
POST /upload
Content-Type: application/json

# Example JSON body:
{
  "text": "...extracted document text...",
  "filename": "earnings_call.pdf"
}
```

**Response:**

```json
{
  "document_id": "abc-123-xyz",
  "filename": "earnings_call.pdf",
  "text_length": 12543,
  "status": "ready",
  "message": "Text received successfully"
}
```

---

### **Endpoint 2: Analyze Document**

```bash
POST /analyze
Content-Type: application/json

# Example with curl:
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"document_id": "abc-123-xyz"}'
```

**Response:**
```json
{
  "document_id": "abc-123-xyz",
  "filename": "earnings_call.pdf",
  "analysis": {
    "management_tone": "optimistic",
    "confidence_level": "high",
    "key_positives": [
      "Revenue grew 25% YoY",
      "New product launch exceeding expectations",
      "Expanded into 3 new markets"
    ],
    "key_concerns": [
      "Supply chain constraints in Q2",
      "Rising raw material costs"
    ],
    "forward_guidance": {
      "revenue": "Expected to reach $500M in FY2024",
      "margin": "Gross margin projected at 42-45%",
      "capex": "Not mentioned"
    },
    "capacity_utilization_trends": "Currently at 78%, targeting 85% by Q3",
    "growth_initiatives": [
      "Investing in AI-driven automation",
      "Strategic partnership with Tech Corp"
    ]
  },
  "status": "completed"
}
```

---

### **Other Endpoints**

```bash
GET /              # API documentation
GET /health        # Health check
DELETE /delete/:id # Delete document
```

---

## 🛡️ How Hallucination is Prevented

### 1. **Strict Prompt Engineering**

The system uses a carefully crafted system prompt:

```
You are a professional financial research analyst.

CRITICAL RULES:
1. Use ONLY information explicitly stated in the document.
2. Do NOT infer, guess, or use external knowledge.
3. If information is missing or unclear, return "Not mentioned".
4. Do NOT add explanations, notes, or commentary.
5. Output MUST be valid JSON matching the provided schema.
```

### 2. **Explicit Schema Enforcement**

The LLM receives the exact JSON structure to populate:
- No markdown formatting allowed
- No text outside JSON object
- Strict type constraints (enum values for tone/confidence)

### 3. **Conservative Merging Strategy**

When documents are chunked (>2,500 tokens):
- Lists: Combine and deduplicate
- Tone/Confidence: Majority vote
- Missing data: Prefer "Not mentioned" over guessing
- Conflicts: Flag as inconsistent rather than choosing arbitrarily

### 4. **JSON Schema Validation**

Every response is validated before returning:
- Required fields present
- Enum values match allowed options
- Data types correct
- Malformed responses rejected

### 5. **Deterministic Text Extraction**

- Uses `pdfplumber` (not AI-based extraction)
- No interpretation during extraction phase
- Only raw text sent to LLM

---

## 📋 How Missing Data is Handled

### Strategy: Explicit "Not mentioned" Sentinel Value

**Why not null or empty string?**
- `null`: Could be a parsing error
- `""`: Could be accidentally empty
- `"Not mentioned"`: **Intentional and explicit**

**Examples:**

```json
{
  "forward_guidance": {
    "revenue": "Expected $100M",
    "margin": "Not mentioned",  // ← Explicitly absent
    "capex": "Not mentioned"
  }
}
```

**Validation Rules:**
- Lists can be empty `[]` if nothing mentioned
- Strings must be "Not mentioned" if absent
- No null values in schema
- No inference allowed

---

## ⚙️ Technical Architecture

### Text Processing Pipeline

```
Document Upload
    ↓
PDF/TXT Extraction (pdfplumber)
    ↓
Token Estimation (~4 chars = 1 token)
    ↓
Chunking (if >2,500 tokens)
    ↓
Gemini API Call(s)
    ↓
Result Merging (if chunked)
    ↓
JSON Validation
    ↓
Return Structured Output
```

### Chunking Logic

**When:** Document exceeds ~2,500 tokens (~10,000 characters)

**Strategy:**
- Split on sentence boundaries (preserve context)
- 100-token overlap between chunks
- Analyze each chunk independently
- Merge results conservatively

**Example:**
```python
Text: 15,000 chars → 3 chunks
Chunk 1: Chars 0-10,000
Chunk 2: Chars 9,600-14,000  # 400 char overlap
Chunk 3: Chars 13,600-15,000 # 400 char overlap
```

---

## ⚠️ Known Limitations

### 1. **File Format Constraints**
- **PDF Tables**: May extract incorrectly (pdfplumber limitation)
- **Multi-column Layouts**: Can scramble text order
- **Scanned PDFs**: No OCR support (text-based PDFs only)
- **Images/Charts**: Not processed (text-only analysis)

### 2. **Language Support**
- **Optimized for**: English documents
- **Other languages**: Gemini supports them, but not validated
- **Mixed languages**: May cause inconsistent results

### 3. **File Size**
- **Max**: 20MB (configurable in `.env`)
- **Reason**: Free hosting constraints and processing time

### 4. **API Rate Limits**
- **Gemini Free Tier**: 60 requests/minute
- **Large documents**: May require multiple API calls (chunking)
- **Mitigation**: Sequential chunk processing (not parallel)

### 5. **Processing Time**
- **Single chunk**: ~3-5 seconds
- **Large document (5+ chunks)**: ~15-30 seconds
- **No streaming**: Results returned after complete analysis

### 6. **Storage**
- **In-memory**: Documents cleared on server restart
- **Production**: Use database (Supabase/PostgreSQL)

### 7. **Context Window**
- **Max per chunk**: ~2,500 tokens (~10,000 chars)
- **Very long documents**: Information spread across chunks may lose context
- **Mitigation**: Overlap between chunks

---

## 🐛 Troubleshooting

### "GOOGLE_GEMINI_API_KEY not configured"
**Solution:** Create `.env` file with your API key

### "No text could be extracted from the document"
**Causes:**
- Scanned PDF (image-based, not text)
- Corrupted file
- Empty document

**Solution:** Use text-based PDFs or TXT files

### "Analysis output validation failed"
**Cause:** Gemini returned unexpected format

**Solution:** Check API logs, retry with simpler document

### "Document not found"
**Cause:** Server restarted (in-memory storage cleared)

**Solution:** Re-upload document

---

## 🚢 Deployment

### Option 1: Render (Recommended)

1. Push code to GitHub
2. Create new Web Service on [Render](https://render.com)
3. Connect GitHub repo
4. Set environment variables:
   - `GOOGLE_GEMINI_API_KEY`
5. Deploy

**render.yaml:**
```yaml
services:
  - type: web
    name: research-portal
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    envVars:
      - key: GOOGLE_GEMINI_API_KEY
        sync: false
```

### Option 2: Railway

1. Install Railway CLI: `npm i -g railway`
2. Run: `railway login`
3. Run: `railway init`
4. Set env vars: `railway variables set GOOGLE_GEMINI_API_KEY=your_key`
5. Deploy: `railway up`

### Option 3: Local Development

```bash
python app.py
# Access at http://localhost:5000
```

---

## 📊 Output Schema Reference

```json
{
  "management_tone": "optimistic | cautious | neutral | pessimistic",
  "confidence_level": "high | medium | low",
  "key_positives": ["string", "string", ...],  // 0-5 items
  "key_concerns": ["string", "string", ...],   // 0-5 items
  "forward_guidance": {
    "revenue": "string or 'Not mentioned'",
    "margin": "string or 'Not mentioned'",
    "capex": "string or 'Not mentioned'"
  },
  "capacity_utilization_trends": "string or 'Not mentioned'",
  "growth_initiatives": ["string", "string", ...]  // 0-5 items
}
```

---

## 🧪 Testing

### Manual Testing

1. **Start server:**
   ```bash
   python app.py
   ```

2. **Test upload:**
   ```bash
   curl -X POST http://localhost:5000/upload \
     -F "file=@test_document.pdf"
   ```

3. **Test analysis:**
   ```bash
   curl -X POST http://localhost:5000/analyze \
     -H "Content-Type: application/json" \
     -d '{"document_id": "<your_document_id>"}'
   ```

### Test Cases

- ✅ Complete earnings call (all fields present)
- ✅ Partial document (some "Not mentioned" fields)
- ✅ Long document (>10,000 chars, requires chunking)
- ✅ Short document (<100 words)
- ✅ Invalid file type (should reject)

---

## 📁 Project Structure

```
research-portal/
├── app.py                    # Flask API
├── requirements.txt          # Dependencies
├── .env.example             # Environment template
├── .env                     # Your config (gitignored)
├── .gitignore
├── README.md
├── utils/
│   ├── __init__.py
│   ├── text_extractor.py    # PDF/TXT extraction
│   ├── text_processor.py    # Chunking logic
│   ├── gemini_analyzer.py   # AI analysis
│   └── validator.py         # JSON validation
└── uploads/                 # Temporary storage
    └── .gitkeep
```

---

## 🔑 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| `pdfplumber` over `PyPDF2` | More reliable text extraction |
| `gemini-1.5-flash` | Fast and cost-effective |
| JSON-only output | Easier validation, no markdown |
| "Not mentioned" sentinel | Explicit vs implicit missing data |
| In-memory storage | Simplifies deployment, good for POC |
| Sequential chunking | Avoids rate limits |

---

## 📝 License

This project is provided as-is for educational and research purposes.

---

## 🙋 Support

For issues or questions:
1. Check **Troubleshooting** section
2. Verify `.env` configuration
3. Test with simple document first
4. Check Gemini API quota

---

**Built with ❤️ for deterministic research analysis❤️**
