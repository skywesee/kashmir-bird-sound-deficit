"""
rebuild_dataset.py
Rebuilds the regional recording set, keeping records that have no
coordinates but whose locality string names a place in the region.

    python3 rebuild_dataset.py
"""

import glob
import re
import pandas as pd

BOX = (32.0, 37.5, 73.0, 80.5)          # lat_min, lat_max, lon_min, lon_max
JK_BOX = (32.30, 35.12, 73.40, 76.80)   # Kichloo extent, for sub-region tagging

# Word-boundary matches only, to avoid catching e.g. "Lehra" with "leh"
PLACES = [
    "jammu", "kashmir", "ladakh", "srinagar", "baramulla", "buniyar",
    "gulmarg", "pahalgam", "sonamarg", "kupwara", "anantnag", "dachigam",
    "leh", "kargil", "kazinag", "poonch", "rajouri", "doda", "kishtwar",
    "udhampur", "kathua", "ramban", "patnitop", "budgam", "ganderbal",
    "pulwama", "shopian", "kulgam", "bandipore", "samba", "reasi",
    "hokersar", "wular", "shallabugh", "hygam", "nubra", "zanskar",
    "changthang", "hemis", "overa", "yusmarg", "aru", "lidder",
]
PAT = re.compile(r"\b(" + "|".join(PLACES) + r")\b", re.I)

NON_BIRD_GENERA = {"mystery", "sonus", "soundscape"}


def main():
    src = sorted(glob.glob("kashmir/*.csv"))[0]
    df = pd.read_csv(src)
    print("India records pulled:", len(df))

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["cnt_clean"] = df["cnt"].astype(str).str.strip()
    india = df[df.cnt_clean == "India"]

    in_box = (india.lat.between(BOX[0], BOX[1]) &
              india.lon.between(BOX[2], BOX[3]))
    no_coord = india.lat.isna() | india.lon.isna()
    by_name = no_coord & india["loc"].astype(str).str.contains(PAT, na=False)

    keep = india[in_box | by_name].copy()
    keep["geo_source"] = keep.lat.notna().map({True: "coordinates",
                                               False: "locality name"})

    # Drop non-bird and unidentified entries
    before = len(keep)
    keep = keep[~keep["gen"].astype(str).str.lower().isin(NON_BIRD_GENERA)]
    print(f"dropped {before - len(keep)} unidentified / non-bird entries")

    keep["scientific_name"] = (keep.gen.astype(str).str.strip() + " " +
                               keep.sp.astype(str).str.strip())
    keep["date"] = pd.to_datetime(keep["date"], errors="coerce")
    keep["year"] = keep.date.dt.year
    keep["month"] = keep.date.dt.month
    keep["alt_m"] = pd.to_numeric(keep["alt"], errors="coerce")

    jk = (keep.lat.between(JK_BOX[0], JK_BOX[1]) &
          keep.lon.between(JK_BOX[2], JK_BOX[3]))
    ladakh_name = keep["loc"].astype(str).str.contains(
        r"\b(ladakh|leh|kargil|nubra|zanskar|changthang|hemis)\b", case=False, na=False)
    keep["region"] = "J&K"
    keep.loc[keep.lat.notna() & ~jk, "region"] = "Ladakh"
    keep.loc[keep.lat.isna() & ladakh_name, "region"] = "Ladakh"

    keep.to_csv("jkl_recordings.csv", index=False)

    print("\n=== REBUILT DATASET ===")
    print("recordings:", len(keep))
    print("species:   ", keep.scientific_name.nunique())
    print("recordists:", keep.rec.nunique())
    print("\nby geo source:")
    print(keep.geo_source.value_counts().to_string())
    print("\nby region:")
    print(keep.region.value_counts().to_string())

    print("\n=== RECORDISTS ===")
    print(keep.rec.value_counts().to_string())

    sm = {3: "Spring", 4: "Spring", 5: "Spring", 6: "Summer", 7: "Summer",
          8: "Summer", 9: "Autumn", 10: "Autumn", 11: "Autumn",
          12: "Winter", 1: "Winter", 2: "Winter"}
    keep["season"] = keep.month.map(sm)
    print("\n=== SEASON x REGION ===")
    print(pd.crosstab(keep.season, keep.region).to_string())

    print("\n=== ENDEMICS ===")
    for s in ["Tragopan melanocephalus", "Catreus wallichii",
              "Aegithalos niveogularis", "Sitta cashmirensis",
              "Sitta leucopsis", "Pyrrhula aurantiaca",
              "Callacanthis burtoni", "Ficedula subrubra"]:
        print(f"  {s:30s} {(keep.scientific_name == s).sum()}")


if __name__ == "__main__":
    main()
