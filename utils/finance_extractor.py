"""
Enhanced financial statement extractor with LLM-powered intelligence.
Extracts multi-period data with hierarchy, calculates derived metrics.
"""
import re
from typing import Dict, List, Any, Optional, Tuple
import json


def extract_periods_from_text(text: str) -> List[str]:
    """Extract all financial periods from document (FY25, Q4 FY25, etc.)"""
    periods = []
    
    # Pattern for fiscal years: FY25, FY 2025, FY2025
    fy_patterns = [
        r'FY\s*(\d{2})',
        r'FY\s*(\d{4})',
        r'fiscal\s+year\s+(\d{4})',
        r'year\s+ended\s+.*?(\d{4})'
    ]
    
    for pattern in fy_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            year = match.group(1)
            if len(year) == 2:
                fy = f"FY{year}"
            else:
                fy = f"FY{year[-2:]}"
            if fy not in periods:
                periods.append(fy)
    
    return sorted(set(periods), reverse=True)


def extract_currency_and_unit(text: str) -> Tuple[str, str]:
    """Detect currency (INR/USD) and unit (crores/millions)"""
    header = text[:2000].lower()
    
    currency = "INR"
    if "₹" in header or "rs." in header or "rupees" in header:
        currency = "INR"
    elif "$" in header or "usd" in header:
        currency = "USD"
    
    unit = ""
    if "crore" in header:
        unit = "crores"
    elif "million" in header:
        unit = "millions"
    
    return currency, unit


def create_extraction_prompt(text: str, periods: List[str]) -> str:
    """Create LLM prompt for structured extraction"""
    periods_str = ", ".join(periods)
    
    return f"""Extract financial statement data from this document.

PERIODS TO EXTRACT: {periods_str}

RULES:
1. Extract ONLY values explicitly stated
2. Do NOT calculate or infer values
3. Use null for missing items
4. Preserve exact numbers

OUTPUT JSON:
{{
  "periods": [list of periods found],
  "currency": "INR|USD",
  "unit": "crores|millions",
  "line_items": [
    {{
      "name": "Revenue from operations",
      "values": {{"FY25": 204813.0, "FY24": 163210.0}},
      "confidence": "high"
    }}
  ]
}}

EXTRACT THESE LINE ITEMS (if present):
- Revenue from operations
- Other income  
- Cost of materials consumed
- Employee benefits expense
- Other expenses
- Finance costs
- Depreciation
- Profit before tax
- Tax expense
- Profit after tax

DOCUMENT:
{text}

Return ONLY the JSON object."""


def parse_extraction_result(llm_response: str) -> Dict[str, Any]:
    """Parse LLM JSON response"""
    response = llm_response.strip()
    if response.startswith('```'):
        lines = response.split('\n')
        response = '\n'.join(lines[1:-1]) if len(lines) > 2 else response
        response = response.replace('```json', '').replace('```', '').strip()
    
    return json.loads(response)


def calculate_derived_metrics(line_items: Dict[str, Dict]) -> Dict[str, Dict]:
    """Calculate Gross Profit, Gross Margin, EBITDA"""
    calculated = {}
    
    # Get all periods
    all_periods = set()
    for item in line_items.values():
        all_periods.update(item.get('values', {}).keys())
    
    # Gross Profit = Revenue - COGS
    if "Total Revenue" in line_items and "Cost of materials consumed" in line_items:
        gross_profit = {"name": "Gross Profit", "values": {}, "status": {}}
        
        for period in all_periods:
            revenue = line_items.get("Total Revenue", {}).get("values", {}).get(period)
            cogs = line_items.get("Cost of materials consumed", {}).get("values", {}).get(period)
            
            # Only calculate if BOTH values exist
            if revenue is not None and cogs is not None:
                gross_profit["values"][period] = revenue - cogs
                gross_profit["status"][period] = "calculated"
        
        if gross_profit["values"]:  # Only add if we calculated at least one value
            calculated["Gross Profit"] = gross_profit
    
    # Gross Margin = Gross Profit / Revenue
    if "Gross Profit" in calculated and "Total Revenue" in line_items:
        gross_margin = {"name": "Gross Margin", "values": {}, "status": {}}
        
        for period in all_periods:
            gp = calculated["Gross Profit"]["values"].get(period)
            revenue = line_items["Total Revenue"]["values"].get(period)
            
            # Only calculate if BOTH exist and revenue is not zero
            if gp is not None and revenue is not None and revenue != 0:
                gross_margin["values"][period] = gp / revenue
                gross_margin["status"][period] = "calculated"
        
        if gross_margin["values"]:
            calculated["Gross Margin"] = gross_margin
    
    # EBITDA = Gross Profit - Employee Benefits - Other Expenses
    if "Gross Profit" in calculated:
        ebitda = {"name": "EBITDA", "values": {}, "status": {}}
        
        for period in all_periods:
            gp = calculated["Gross Profit"]["values"].get(period)
            emp = line_items.get("Employee benefits expense", {}).get("values", {}).get(period)
            other = line_items.get("Other expenses", {}).get("values", {}).get(period)
            
            # Calculate only if we have gross profit
            if gp is not None:
                # Treat missing expenses as 0
                emp_val = emp if emp is not None else 0
                other_val = other if other is not None else 0
                
                ebitda["values"][period] = gp - emp_val - other_val
                ebitda["status"][period] = "calculated"
        
        if ebitda["values"]:
            calculated["EBITDA"] = ebitda
    
    return calculated
def generate_excel_data(line_items: Dict[str, Dict], metadata: Dict[str, Any]) -> Dict[str, List]:
    """Generate data structure for Excel export"""
    periods = sorted(metadata.get('periods', []), reverse=True)
    
    # Define display order
    display_order = [
        "Revenue from operations",
        "Other income",
        "Total Revenue",
        "",
        "Expenses:",
        "Cost of materials consumed",
        "Employee benefits expense",
        "Other expenses",
        "",
        "Gross Profit",
        "Gross Margin",
        "EBITDA",
        "Finance costs",
        "Depreciation",
        "Profit before tax",
        "Tax expense",
        "Profit after tax"
    ]
    
    # Build rows
    rows = []
    header = ["Particulars"] + periods + ["Status", "Notes"]
    rows.append(header)
    
    for item_name in display_order:
        if not item_name:  # Blank row
            rows.append([""] * len(header))
            continue
        
        if item_name.endswith(":"):  # Section header
            rows.append([item_name] + [""] * (len(periods) + 2))
            continue
        
        item = line_items.get(item_name)
        if not item:
            rows.append([item_name] + [""] * len(periods) + ["✗ Not found", "Not disclosed"])
            continue
        
        # Build data row
        row = [item_name]
        statuses = []
        
        for period in periods:
            value = item.get("values", {}).get(period)
            status = item.get("status", {}).get(period, "missing")
            
            if value is not None:
                if item_name == "Gross Margin":
                    row.append(f"{value:.4f}")
                else:
                    row.append(f"{value:,.2f}")
                statuses.append("✓" if status == "extracted" else "⚡")
            else:
                row.append("")
                statuses.append("✗")
        
        # Overall status
        if all(s == "✓" for s in statuses):
            status_col = "✓ Extracted"
        elif all(s == "⚡" for s in statuses):
            status_col = "⚡ Calculated"
        else:
            status_col = "⚠ Partial"
        
        row.append(status_col)
        row.append("")  # Notes
        rows.append(row)
    
    # Metadata sheet
    metadata_rows = [
        ["Field", "Value"],
        ["Source Document", metadata.get('source_document', 'N/A')],
        ["Currency", metadata.get('currency', 'INR')],
        ["Unit", metadata.get('unit', 'crores')],
        ["Periods", ", ".join(periods)],
    ]
    
    return {
        "Income Statement": rows,
        "Metadata": metadata_rows
    }


# Keep old function for backward compatibility
def extract_income_statement(text: str) -> Dict[str, Any]:
    """Legacy function - use LLM extraction instead"""
    return {
        "error": "Use enhanced extraction with /financial-extract-enhanced endpoint"
    }


def generate_csv(extracted: Dict[str, Any]) -> str:
    """Legacy function - use Excel export instead"""
    return "error,Use Excel export with enhanced extraction"