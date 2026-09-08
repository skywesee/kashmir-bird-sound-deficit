# Acoustic coverage of the Kashmir avifauna

Which birds of Jammu & Kashmir and Ladakh have never been sound-recorded?

This repository holds the data behind a poster presented at **ECSSPP 2026** (3-Day National Conference on Environment, Climate and Sustainability: Science, Policy and Pathways), University of Kashmir, abstract BC-P-36.

We queried Xeno-canto, the global citizen-science archive of wildlife sound, for every bird recording from the Kashmir region and compared the result against the regional checklist.

## What we found

- **802** identified recordings, **176** species, **37** recordists, spanning 1999–2026
- **606 of 778** checklist species (77.9%) have **no recording at all**
- Only **82 species** (10.5%) have three or more recordings
- Coverage is significantly *lower* for species of conservation concern (IUCN threatened or Near Threatened, 7.5% vs 23.5%, p = 0.004; Wildlife Protection Act Schedule-I, 10.7% vs 28.8%, p = 0.001)
- Coverage is significantly *higher* for western Himalayan endemics (71.4% vs 21.7%, p = 0.007)
- Within Jammu & Kashmir, **four recordists produced 91% of the archive across roughly 32 days** of fieldwork, all in spring and summer
- Autumn and winter together account for **1.5%** of Jammu & Kashmir recordings

## Files

| File | Rows | What it is |
|---|---:|---|
| `data/coverage_all_species.csv` | 778 | Every checklist species with its recording count and conservation status |
| `data/deficit_list.csv` | 606 | Species with no recording from the region |
| `data/priority_list.csv` | 212 | Filtered targets: regularly occurring species in habitually vocal families |

### Columns

- `scientific_name`, `common_name`, `order`, `family` — taxonomy (Clements v2025)
- `iucn_status` — IUCN Red List category, blank if Least Concern or unassessed
- `rare_accidental` — `yes` for vagrants and accidentals
- `wpa_schedule` — Indian Wildlife (Protection) Act schedule; blank where the species did not match the Indian checklist
- `soib_priority` — State of India's Birds conservation priority; blank as above
- `wh_endemic` — endemic to the western Himalaya
- `n_recordings` — Xeno-canto recordings from the region

## How the data were assembled

**Recordings.** Xeno-canto API v3, retrieved 8 September 2026 using the [`xcapi`](https://github.com/bghani/xcapi) library. Bounding box 32.0–37.5°N, 73.0–80.5°E, country = India. 802 recordings retained: 705 located by coordinates, and 97 that carry a regional locality name but no coordinates. Nine unidentified or non-avian entries excluded. Restricting to coordinates alone would drop the 97, which are disproportionately from Indian and Kashmir-based recordists.

**Species list.** [Avibase](https://avibase.bsc-eoc.org/) regional checklist for Jammu and Kashmir (incl. Ladakh), Clements v2025 taxonomy, accessed 8 September 2026. The page header reports 775 species; parsing the same page yields 778 entries.

**Indian conservation codes.** Joined from the [Checklist of birds of Jammu & Kashmir v2.0](https://indianbirds.in/indian-states/) (Kichloo 2025). Because the two sources follow different taxonomic authorities, 484 species matched directly and 595 carry at least one Indian classification. Statistical tests involving these codes were restricted to that subset, so species of unknown status are not counted as unlisted.

**Priority list.** From the 606 unrecorded species, we removed 49 flagged rare or accidental, leaving 557 regularly occurring. Of those, 212 belong to families whose members are habitually and conspicuously vocal. This is a working list based on a coarse family-level proxy, not a definitive one.

## Important caveat

**This measures recording effort, not bird abundance.** A species absent from this archive has no recording; it is not absent from the landscape. Nothing here supports inference about population status.

Two of the zero-recording endemics illustrate the point. Cheer Pheasant *Catreus wallichii* has 24 recordings worldwide and White-throated Tit *Aegithalos niveogularis* has nine, from Uttarakhand, Himachal Pradesh and Pakistan. Neither has been recorded in Jammu & Kashmir. They are recordable birds; nobody has recorded them here.

## Why it matters

BirdNET, Perch and similar classifiers are trained largely on Xeno-canto. A species with no recordings from a region cannot be reliably detected by automated monitoring deployed there. On present holdings, acoustic monitoring in the Kashmir region would be blind to roughly 78% of the documented avifauna, and least reliable for the species carrying legal protection.

The gaps are specific and cheap to close. A smartphone with a directional microphone is enough to start, and uploads go to [xeno-canto.org/upload](https://xeno-canto.org/upload).

## Sources

Recordings are from Xeno-canto, contributed by recordists worldwide under Creative Commons licences. Please credit them and the archive in any reuse. Species list © Denis Lepage / Avibase, Birds Canada. Indian conservation codes from Kichloo (2025), Indian BIRDS.

## Authors

Natiq Nabi Sofi, Gazifa Amin, Baasit Abubakr
Centre for Design Your Degree, University of Kashmir (Institute of Technology, Zakura Campus)

## Reproducing the analysis

```bash
pip install pandas scipy openpyxl pdfplumber beautifulsoup4 lxml xenocanto-api
export XENO_CANTO_API_KEY="your-key"          # free from xeno-canto.org/account

xcapi --grp birds --cnt India --metadata_only --output_dir ./kashmir
python3 scripts/rebuild_dataset.py            # -> jkl_recordings.csv
python3 scripts/parse_avibase.py              # -> avibase_775.csv (save the
                                              #    Avibase page as avibase.html first)
python3 scripts/coverage_analysis.py          # -> the three files in data/
```

`scripts/parse_checklist.py` extracts the printed 592-species checklist from the
Kichloo et al. (2024) PDF. It is included for completeness; the analysis uses the
v2.0 spreadsheet instead.

## Licence

Data files: CC BY 4.0. Scripts: MIT.
