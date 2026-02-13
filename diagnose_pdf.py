import pdfplumber
from PyPDF2 import PdfReader
import sys

pdf_path = "Kaynes Concall Transcript.pdf"

print("=" * 60)
print("Testing PDF extraction methods")
print("=" * 60)

# Test 1: pdfplumber
print("\n1. Testing pdfplumber...")
try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"   Pages: {len(pdf.pages)}")
        for i in range(min(3, len(pdf.pages))):
            text1 = pdf.pages[i].extract_text()
            text2 = pdf.pages[i].extract_text(layout=True)
            print(f"   Page {i+1}:")
            print(f"   - Standard: {len(text1) if text1 else 0} chars")
            print(f"   - Layout: {len(text2) if text2 else 0} chars")
            if text1:
                print(f"   - Sample: {text1[:100]}")
            if text2 and not text1:
                print(f"   - Layout Sample: {text2[:100]}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 2: PyPDF2
print("\n2. Testing PyPDF2...")
try:
    reader = PdfReader(pdf_path)
    print(f"   Pages: {len(reader.pages)}")
    for i in range(min(3, len(reader.pages))):
        text = reader.pages[i].extract_text()
        print(f"   Page {i+1}: {len(text) if text else 0} chars")
        if text:
            print(f"   - Sample: {text[:100]}")
except Exception as e:
    print(f"   ERROR: {e}")

# Test 3: Check PDF metadata
print("\n3. Checking PDF info...")
try:
    with pdfplumber.open(pdf_path) as pdf:
        if pdf.metadata:
            print(f"   Metadata: {pdf.metadata}")
        print(f"   First page properties:")
        page = pdf.pages[0]
        print(f"   - Width: {page.width}, Height: {page.height}")
        print(f"   - Has chars: {len(page.chars)}")
        print(f"   - Has images: {len(page.images)}")
        if page.chars:
            print(f"   First few chars: {page.chars[:3]}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 60)
