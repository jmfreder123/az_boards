# Arizona School Board Elections & Accountability Data

This repository links Arizona school board election results (2014-2024) with district-level accountability metrics from the Arizona Department of Education (ADE), including A-F letter grades, dropout rates, enrollment, graduation rates, and superintendent characteristics.

## Files

### Analysis-Ready Files

| File | Rows | Unit of Analysis | Description |
|------|------|------------------|-------------|
| `az_school_board_master.csv` | 2,523 | Candidate | Every candidate in every school board election, with accountability and superintendent data broadcast-joined by district-year |
| `az_district_year_summary.csv` | 299 | District-Year | One row per district per election year, with derived analytical variables for competitiveness, voter engagement, and accountability |

### Source Files

| File | Description |
|------|-------------|
| `School Board Data_2025-2026 (1).xlsx` | Hand-collected superintendent data (48 of ~208 districts filled so far) |
| `ccd_lea_029_2425_w_1a_073025.csv` | NCES Common Core of Data, Arizona LEAs, 2024-2025 — used as the CTDS-to-NCES crosswalk |
| `ccd_lea_029_2425_w_1a_073025.sas7bdat` | Same CCD data in SAS format |
| `ccd_lea_029_2425_w_1a_073025 (1).zip` | Compressed CCD archive |
| `arizona_school_board_elections_summary.numbers` | Original Apple Numbers workbook (election results) |
| `arizona_school_board_enhanced 3.numbers` | Enhanced Apple Numbers workbook |

## Data Sources

- **Election results**: Arizona county election offices (2014-2024 general elections, some primaries)
- **A-F letter grades**: ADE A-F Accountability files (FY13-14, FY17-19, FY22-25). No grades published for FY15-16 or FY20-21 (COVID moratorium).
- **Dropout rates**: ADE Dropout Rate reports (FY13-25), filtered to Subgroup = "All"
- **Enrollment**: ADE October 1 Enrollment counts (FY14-26)
- **Graduation rates**: ADE 4-Year Cohort Graduation Rates (Cohort 2013-2025), filtered to Subgroup = "All"
- **Superintendent data**: Hand-collected from district websites, press releases, and LinkedIn (2025-2026 snapshot, in progress)
- **District identifiers**: NCES CCD 2024-2025 (CTDS Entity ID and NCES LEAID crosswalk)

## Key Identifiers

| ID | Description | Example |
|----|-------------|---------|
| `ctds_id` | ADE County-Type-District-School Entity ID | `4289` |
| `nces_leaid` | NCES national LEA identifier | `408580` |

The join key between election data and ADE accountability data is `ctds_id` + `year`.

## Coverage Notes

- **139 unique districts** appear across 6 election cycles (2014, 2016, 2018, 2020, 2022, 2024)
- Not all districts appear in every cycle; 87 districts appear in 2+ cycles
- The summary file filters to **clean governing board races only** (excludes bonds, budget overrides, county superintendent races, and rows without a `ctds_id`)
- **A-F grades** have structural gaps in 2016 and 2020 (ADE did not publish grades those years)
- **Graduation rates** are only available for districts with high schools (~50% of districts)
- **Superintendent data** currently covers 48 districts; historical data back to 2013 is in progress

See `DATA_DICTIONARY.md` for full column definitions.
