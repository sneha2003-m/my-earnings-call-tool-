# 🚀 QUICK START GUIDE

## ✅ System is Ready!

Your research portal has been successfully built. Here's what to do next:

---

## 📝 STEP 1: Get Your Gemini API Key

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key (it starts with `AIza...`)

---

## 🔑 STEP 2: Add API Key to .env File

Open the file: `.env`

Replace this line:
```
GOOGLE_GEMINI_API_KEY=YOUR_API_KEY_HERE
```

With your actual key:
```
GOOGLE_GEMINI_API_KEY=AIza...your_actual_key...
```

**Save the file!**

---

## 🎮 STEP 3: Run the Server

Open a terminal/PowerShell in this folder and run:

```bash
python app.py
```

You should see:
```
Starting Research Portal API on port 5000...
Running on http://0.0.0.0:5000
```

---

## 🌐 STEP 4: Access the Application

### Option A: Web Interface (Recommended)
Open your browser and go to:
```
http://localhost:5000
```

You'll see a nice web interface where you can:
- Drag and drop PDF/TXT files
- Click "Upload Document"
- Click "Analyze Document"
- View structured results

### Option B: Test Script
Open another terminal and run:
```bash
python test_api.py your_document.pdf
```

### Option C: Direct API (curl)
```bash
# Upload
curl -X POST http://localhost:5000/upload -F "file=@your_document.pdf"

# Analyze (use document_id from upload response)
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"document_id": "your_document_id"}'
```

---

## 📄 What You Need to Test

**Sample Documents:**
- Earnings call transcript (PDF or TXT)
- Management discussion from annual report
- Quarterly results commentary

**Where to Find Test Files:**
- Search: "earnings call transcript PDF"
- Company investor relations pages
- SEC filings (10-K, 10-Q)

---

## ✅ Expected Output Format

```json
{
  "management_tone": "optimistic",
  "confidence_level": "high",
  "key_positives": [
    "Revenue grew 25% YoY",
    "Strong product adoption"
  ],
  "key_concerns": [
    "Supply chain issues"
  ],
  "forward_guidance": {
    "revenue": "$500M expected",
    "margin": "42-45%",
    "capex": "Not mentioned"
  },
  "capacity_utilization_trends": "78% currently",
  "growth_initiatives": [
    "AI automation investment"
  ]
}
```

---

## 🐛 Troubleshooting

### "GOOGLE_GEMINI_API_KEY not configured"
→ Check your .env file has the correct key

### "Is the server running?"
→ Make sure `python app.py` is running in another terminal

### "No text could be extracted"
→ Make sure PDF has text (not scanned images)

### "Module not found"
→ Run: `pip install -r requirements.txt`

---

## 📂 Project Files

```
✅ app.py               - Flask server
✅ utils/               - Core logic modules
✅ static/index.html    - Web interface
✅ test_api.py          - Testing script
✅ requirements.txt     - Dependencies
✅ .env                 - Your API key (EDIT THIS!)
✅ README.md            - Full documentation
```

---

## 🎯 Next Steps

1. [ ] Get Gemini API key
2. [ ] Add key to .env file
3. [ ] Run `python app.py`
4. [ ] Open http://localhost:5000
5. [ ] Upload a test document
6. [ ] Analyze and see results!

---

## 📞 Need Help?

Check the full README.md for:
- Detailed API documentation
- Hallucination prevention explanation
- Deployment instructions
- Troubleshooting guide

---

**You're all set! Start the server and test it out! 🎉**
