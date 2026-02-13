"""
Clean and summarize extracted income statement CSVs.
Usage: python utils/finance_cleaner.py <input_csv>
Produces: cleaned_<input_filename> and prints an issues summary.
"""
import csv
import sys
import re
from collections import defaultdict

YEAR_RE = re.compile(r"^(19\d{2}|20\d{2})$")

CANONICAL_ORDER = [
    "revenue",
    "cost_of_goods_sold",
    "gross_profit",
    "operating_expenses",
    "operating_income",
    "ebitda",
    "net_income"
]

def is_year_token(s: str) -> bool:
    if not s:
        return False
    s = s.strip()
    return bool(YEAR_RE.match(s))

def load_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def summarize(rows):
    # Group by (line_item, year)
    groups = defaultdict(list)
    other_rows = []
    for r in rows:
        item = (r.get('line_item') or '').strip()
        year = (r.get('year') or '').strip()
        raw = (r.get('raw') or '').strip()
        val = r.get('value')
        try:
            num = float(val) if val not in (None, '') else None
        except Exception:
            num = None

        if item == 'other':
            other_rows.append({'year': year, 'raw': raw, 'num': num})
        else:
            groups[(item, year)].append({'raw': raw, 'num': num})

    cleaned = []
    issues = []

    # For each canonical item, pick best value per year (largest abs non-year number)
    years = sorted({y for (_, y) in groups.keys() if y})
    # also include years found in other rows
    for r in other_rows:
        if r['year'] and r['year'] not in years and is_year_token(r['year']):
            years.append(r['year'])

    years = sorted(years)

    for item in CANONICAL_ORDER:
        for y in years:
            vals = groups.get((item, y), [])
            chosen = None
            if vals:
                # prefer numeric values that are not equal to the year
                numeric_vals = [v['num'] for v in vals if v['num'] is not None and (str(v['num']).find(y) == -1)]
                if not numeric_vals:
                    numeric_vals = [v['num'] for v in vals if v['num'] is not None]
                if numeric_vals:
                    # choose the max absolute value assuming top-line larger
                    chosen_val = max(numeric_vals, key=lambda x: abs(x))
                    chosen = {'line_item': item, 'year': y, 'value': chosen_val, 'note': ''}
            if not chosen:
                cleaned.append({'line_item': item, 'year': y, 'value': '', 'note': 'Not found'})
            else:
                cleaned.append(chosen)

    # Simple heuristics to flag noisy other rows
    noise_count = 0
    year_tokens = 0
    for o in other_rows:
        if (o['raw'] and o['raw'].isdigit() and len(o['raw']) <= 4) or is_year_token(o['raw']):
            noise_count += 1
        if is_year_token(o['raw']) or is_year_token(o['year']):
            year_tokens += 1

    issues.append(f"Total rows: {len(rows)}")
    issues.append(f"Other rows (noise candidates): {len(other_rows)}")
    issues.append(f"Other rows that look like years: {year_tokens}")
    issues.append(f"Suspected noisy entries: {noise_count}")

    return cleaned, issues

def write_cleaned(cleaned, outpath):
    with open(outpath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['line_item','year','value','note'])
        writer.writeheader()
        for r in cleaned:
            writer.writerow(r)

def main():
    if len(sys.argv) < 2:
        print('Usage: python utils/finance_cleaner.py <input_csv>')
        sys.exit(1)
    inp = sys.argv[1]
    rows = load_rows(inp)
    cleaned, issues = summarize(rows)
    out = 'cleaned_' + inp
    write_cleaned(cleaned, out)
    print('Wrote cleaned CSV to', out)
    print('\nIssues:')
    for i in issues:
        print('-', i)

if __name__ == '__main__':
    main()
