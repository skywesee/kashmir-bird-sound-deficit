"""
parse_avibase.py
Parses the locally saved Avibase checklist page (Jammu and Kashmir incl. Ladakh)
into avibase_775.csv.

    pip install beautifulsoup4 lxml
    python3 parse_avibase.py            # reads avibase.html
    python3 parse_avibase.py page.html  # or a named file
"""

import os
import re
import sys
import pandas as pd
from bs4 import BeautifulSoup

SRC = sys.argv[1] if len(sys.argv) > 1 else "avibase.html"
OUT = "avibase_775.csv"

IUCN = ["Critically endangered", "Endangered", "Vulnerable", "Near-threatened"]


def main():
    if not os.path.exists(SRC):
        raise SystemExit(f"{SRC} not found. Save the Avibase page there first.")

    soup = BeautifulSoup(open(SRC, errors="ignore").read(), "lxml")

    rows, order, family = [], "", ""
    for tr in soup.find_all("tr"):
        text = tr.get_text(" ", strip=True)

        # Family header rows: "ANSERIFORMES: Anatidae"
        m = re.match(r"^([A-Z]{4,}):\s*([A-Z][a-z]+)$", text)
        if m:
            order, family = m.group(1).title(), m.group(2)
            continue

        link = tr.find("a", href=re.compile("species\\.jsp"))
        if not link:
            continue

        sci = link.get_text(" ", strip=True)
        if len(sci.split()) < 2:
            continue

        cells = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
        common = cells[0] if cells else ""
        status = cells[-1] if len(cells) > 2 else ""

        rows.append({
            "scientific_name": sci,
            "common_name": common,
            "order": order,
            "family": family,
            "iucn_status": next((s for s in IUCN if s in status), ""),
            "rare_accidental": "yes" if "Rare/Accidental" in status else "no",
        })

    df = pd.DataFrame(rows)
    before = len(df)
    df = df.drop_duplicates("scientific_name").reset_index(drop=True)
    df.to_csv(OUT, index=False)

    print(f"rows found: {before} | unique species: {len(df)} -> {OUT}")
    print("  (Avibase reports 775)")
    print("\nIUCN:")
    print(df.iucn_status.replace("", "(none)").value_counts().to_string())
    print("\nrare/accidental:", (df.rare_accidental == "yes").sum())
    print("\nfamilies:", df.family.nunique())
    print("\nfirst 5:")
    print(df.head().to_string(index=False))
    if df.family.eq("").sum():
        print("\nWARNING: blank family for", df.family.eq("").sum(), "species")


if __name__ == "__main__":
    main()
