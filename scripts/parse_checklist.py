"""
parse_checklist.py
Extracts the 592-species checklist from Kichloo et al. (2024),
Indian BIRDS 19(6):163-180, into jk_checklist.csv.

Setup:
    pip install pdfplumber pandas
    Download the PDF to this folder as kichloo2024.pdf from:
    https://indianbirds.in/pdfs/IB_19_6_KichlooETAL_JandK_Checklist.pdf

Run:
    python3 parse_checklist.py
    python3 parse_checklist.py --text raw.txt     # parse a text file instead
"""

import re
import sys
import pandas as pd

PDF = "kichloo2024.pdf"
OUT = "jk_checklist.csv"

# Status codes that may follow the scientific name
STATUS = {"CR", "EN", "VU", "NT", "S", "H"}
SOURCES = {"B", "G", "N", "U", "M", "O"}

ENDEMICS = {
    "Tragopan melanocephalus", "Catreus wallichii", "Aegithalos niveogularis",
    "Sitta cashmirensis", "Sitta leucopsis", "Pyrrhula aurantiaca",
    "Callacanthis burtoni",
}

FAMILY_RE = re.compile(r"^\d+\.\s+([A-Z][a-z]+idae|[A-Z][a-z]+inae)\s*\(")
ENTRY_RE = re.compile(r"^(\d{1,3})\s+(.+)$")


def get_text():
    """Extract text column-by-column. The paper is two-column, so a plain
    page.extract_text() glues left-column rows onto right-column rows."""
    if "--text" in sys.argv:
        return open(sys.argv[sys.argv.index("--text") + 1]).read()
    import pdfplumber
    out = []
    with pdfplumber.open(PDF) as pdf:
        for page in pdf.pages:
            w, h = page.width, page.height
            for x0, x1 in ((0, w / 2), (w / 2, w)):
                try:
                    t = page.crop((x0, 0, x1, h)).extract_text()
                except Exception:
                    t = None
                if t:
                    out.append(t)
                out.append("@@COLBREAK@@")
    return "\n".join(out)


def split_entry(rest):
    """Split 'Common Name Genus species VU, S, H G M' into its parts."""
    # Strip the trailing status/source codes token by token from the right
    toks = rest.replace(",", " ").split()
    tail = []
    while toks and (toks[-1] in STATUS or toks[-1] in SOURCES):
        tail.insert(0, toks.pop())
    if not toks:
        return None

    # The scientific name is the last two tokens: Genus species.
    # An asterisk may be glued to the epithet; a lone capital status code
    # may be glued too (e.g. "albaS", "flammeusS").
    if len(toks) < 3:
        return None
    epithet = toks[-1]
    starred = epithet.endswith("*")
    epithet = epithet.rstrip("*")
    m = re.match(r"^([a-zA-Z]+?)((?:CR|EN|VU|NT|[SH])?)$", epithet)
    if m and m.group(2):
        epithet = m.group(1)
        tail.insert(0, m.group(2))
    genus = toks[-2]
    if not genus[0].isupper():
        return None
    common = " ".join(toks[:-2])
    sci = f"{genus} {epithet[0].lower() + epithet[1:]}"

    codes = set(tail)
    iucn = next((c for c in ("CR", "EN", "VU", "NT") if c in codes), "")
    return {
        "scientific_name": sci,
        "common_name": common,
        "iucn_status": iucn,
        "schedule_1": "yes" if "S" in codes else "no",
        "soib_high_priority": "yes" if "H" in codes else "no",
        "not_since_1950": "yes" if starred else "no",
        "endemic": "yes" if sci in ENDEMICS else "no",
    }


def main():
    text = get_text()
    lines = text.split("\n")

    # Join lines where a long name wrapped (next line starts lowercase)
    joined, i = [], 0
    while i < len(lines):
        cur = lines[i].strip()
        if (i + 1 < len(lines) and cur and cur != "@@COLBREAK@@"
                and lines[i + 1].strip() != "@@COLBREAK@@"
                and not cur.endswith(("M", "G", "O", "N", "U", "B"))
                and lines[i + 1].strip()[:1].islower()):
            cur = cur + " " + lines[i + 1].strip()
            i += 1
        joined.append(cur)
        i += 1

    family = ""
    rows, seen = [], set()
    for line in joined:
        fm = FAMILY_RE.match(line)
        if fm:
            family = fm.group(1)
            continue
        em = ENTRY_RE.match(line)
        if not em:
            continue
        num = int(em.group(1))
        if num in seen or not (1 <= num <= 592):
            continue
        parsed = split_entry(em.group(2))
        if not parsed:
            continue
        parsed["sno"] = num
        parsed["family"] = family
        rows.append(parsed)
        seen.add(num)

    df = pd.DataFrame(rows).sort_values("sno")
    cols = ["sno", "scientific_name", "common_name", "family", "iucn_status",
            "schedule_1", "soib_high_priority", "endemic", "not_since_1950"]
    df = df[cols]
    df.to_csv(OUT, index=False)

    print(f"parsed {len(df)} species -> {OUT}")
    missing = sorted(set(range(1, 593)) - seen)
    if missing:
        print(f"MISSING {len(missing)} numbers:", missing[:40])
    print("\nendemics found:", (df.endemic == "yes").sum(), "(expect 7)")
    print("IUCN threatened (CR/EN/VU):",
          df.iucn_status.isin(["CR", "EN", "VU"]).sum(), "(expect 25)")
    print("SoIB high priority:", (df.soib_high_priority == "yes").sum(),
          "(expect 85)")
    print("\nfirst 5:")
    print(df.head().to_string(index=False))


if __name__ == "__main__":
    main()
