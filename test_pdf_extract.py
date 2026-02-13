import pdfplumber

pdf_path = "Kaynes Concall Transcript.pdf"

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")
        
        full_text = ""
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
                print(f"Page {i+1}: {len(page_text)} characters")
        
        print(f"\nTotal characters extracted: {len(full_text)}")
        print(f"\nFirst 500 characters:\n{full_text[:500]}")
        
        if len(full_text.strip()) > 0:
            print("\n✅ PDF text extraction SUCCESSFUL")
        else:
            print("\n❌ PDF has no extractable text (might be scanned/image-based)")
            
except Exception as e:
    print(f"❌ Error: {e}")
