"""
coverage_analysis.py
Joins the regional recording set to the species checklist, computes coverage
tiers, and tests coverage against conservation classifications.

Inputs (in the working directory):
    jkl_recordings.csv   from rebuild_dataset.py
    avibase_775.csv      from parse_avibase.py
    jk_v2.xlsx           Kichloo (2025) checklist v2.0, downloaded from
                         https://indianbirds.in/indian-states/

Outputs:
    coverage_all_species.csv
    deficit_list.csv
    priority_list.csv

    pip install pandas scipy openpyxl
    python3 coverage_analysis.py
"""

import pandas as pd
from scipy.stats import chi2_contingency

# Families whose members are habitually and conspicuously vocal. A coarse
# proxy used only to filter the deficit list into realistic recording targets.
VOCAL_FAMILIES = [
    "Muscicapidae", "Turdidae", "Phylloscopidae", "Leiothrichidae",
    "Sylviidae", "Emberizidae", "Fringillidae", "Alaudidae", "Motacillidae",
    "Paridae", "Cisticolidae", "Acrocephalidae", "Hirundinidae",
    "Pycnonotidae", "Sittidae", "Certhiidae", "Prunellidae", "Cuculidae",
    "Picidae", "Strigidae",
]

THREATENED = ["Critically endangered", "Endangered", "Vulnerable",
              "Near-threatened"]


def norm(s):
    return (s.astype(str).str.strip().str.lower()
             .str.replace(r"\s+", " ", regex=True))


def report(label, mask, frame):
    ct = pd.crosstab(mask, frame.has)
    if ct.shape != (2, 2):
        print(f"\n{label}: skipped (insufficient variation)")
        return
    chi2, p, _, _ = chi2_contingency(ct)
    hit = 100 * ct.loc[True, True] / ct.loc[True].sum()
    base = 100 * ct.loc[False, True] / ct.loc[False].sum()
    print(f"\n{label}: {hit:.1f}% covered vs {base:.1f}% "
          f"| chi2={chi2:.2f} p={p:.4g}")
    print(ct.to_string())


def main():
    av = pd.read_csv("avibase_775.csv")
    kc = pd.read_excel("jk_v2.xlsx",
                       sheet_name="Jammu & Kashmir_Checklist_v2_0")
    xc = pd.read_csv("jkl_recordings.csv")

    av["key"] = norm(av.scientific_name)
    kc["key"] = norm(kc["Scientific Name"])
    xc["key"] = norm(xc.scientific_name)

    kc_slim = kc[["key", "WPA Schedule", "SOIB",
                  "Endemic (Western Himalayas)"]].drop_duplicates("key")

    m = av.merge(kc_slim, on="key", how="left")
    m = m.merge(xc.groupby("key").size().rename("n").reset_index(),
                on="key", how="left")
    m["n"] = m.n.fillna(0).astype(int)
    m["has"] = m.n > 0

    print("=== COVERAGE ===")
    print("checklist species:", len(m))
    print("with recording:   ", m.has.sum(),
          f"({100*m.has.mean():.1f}%)")
    print("zero recordings:  ", (~m.has).sum(),
          f"({100*(~m.has).mean():.1f}%)")
    print("1-2 recordings:   ", m.n.between(1, 2).sum())
    print(">=3 recordings:   ", (m.n >= 3).sum())
    print("matched to Kichloo:", m["SOIB"].notna().sum())
    print("recorded species not on checklist:",
          len(set(xc.key) - set(av.key)))

    # Species lacking Indian classifications are excluded from those two
    # tests, so that unknown status is not treated as "not listed".
    sub = m[m["SOIB"].notna() | m["WPA Schedule"].notna()]

    report("IUCN threatened/NT", m.iucn_status.isin(THREATENED), m)
    report("WPA Schedule-I",
           sub["WPA Schedule"].astype(str).str.strip() == "Schedule-I", sub)
    report("SoIB high priority",
           sub["SOIB"].astype(str).str.contains("High", na=False), sub)
    report("Western Himalayan endemic",
           m["Endemic (Western Himalayas)"].notna(), m)

    # ---- Publication files -------------------------------------------------
    out = m.drop(columns=["key", "has"]).rename(columns={
        "n": "n_recordings", "WPA Schedule": "wpa_schedule",
        "SOIB": "soib_priority",
        "Endemic (Western Himalayas)": "wh_endemic"})
    out["wh_endemic"] = out.wh_endemic.notna().map({True: "yes", False: "no"})
    out = out.sort_values(["n_recordings", "scientific_name"],
                          ascending=[False, True])
    out.to_csv("coverage_all_species.csv", index=False)

    deficit = out[out.n_recordings == 0].drop(columns=["n_recordings"])
    deficit.to_csv("deficit_list.csv", index=False)

    priority = deficit[(deficit.rare_accidental == "no") &
                       (deficit.family.isin(VOCAL_FAMILIES))]
    priority[["scientific_name", "common_name", "family", "iucn_status",
              "wpa_schedule", "soib_priority"]].to_csv("priority_list.csv",
                                                       index=False)

    print(f"\nwrote coverage_all_species.csv ({len(out)}), "
          f"deficit_list.csv ({len(deficit)}), "
          f"priority_list.csv ({len(priority)})")


if __name__ == "__main__":
    main()
