# Data Dictionary

## az_school_board_master.csv

One row per candidate per election. 2,523 rows.

### Election Fields

| Column | Type | Description | Fill Rate |
|--------|------|-------------|-----------|
| `year` | float | Election year (2014-2024) | 100% |
| `election_date` | string | Full election date | 100% |
| `election_type` | string | `general` or `primary` | 100% |
| `county` | string | Arizona county name | 100% |
| `school_district` | string | District name as it appears on the ballot (not standardized across years) | 100% |
| `district` | string | District label (sparse, only in some source files) | 9% |
| `office` | string | Office title (e.g., "Governing Board Member-4yr") | 100% |
| `candidate` | string | Candidate name. Format varies: `LAST, FIRST` (2014-2022) or `First LAST` (2024) | 100% |
| `party` | string | Party affiliation (where applicable) | 46% |
| `total_votes` | float | Total votes received by this candidate | 100% |
| `early_voting` | float | Early/mail-in votes | 68% |
| `election_day` | float | Election day votes | 67% |
| `provisional` | float | Provisional ballot votes | 49% |
| `winner` | string | `YES` if candidate won the seat | 23% |
| `num_precincts` | float | Number of precincts reporting | 100% |

### Identifier Fields

| Column | Type | Description | Fill Rate |
|--------|------|-------------|-----------|
| `ctds_id` | float | ADE CTDS Entity ID (state district identifier) | 85% |
| `nces_leaid` | float | NCES national LEA identifier | 85% |
| `ccd_lea_name` | string | Standardized LEA name from NCES CCD | 85% |

Rows without `ctds_id` are typically bond elections, budget overrides, or county superintendent races that don't map to a single school district.

### Accountability Fields

Joined from ADE source files on `ctds_id` + `year`. These values are the same for every candidate row within a district-year.

| Column | Type | Description | Fill Rate |
|--------|------|-------------|-----------|
| `lea_letter_grade` | string | ADE A-F letter grade for the LEA (A/B/C/D/F) | 40% |
| `num_schools_in_lea` | float | Number of schools used to compute the LEA grade | 40% |
| `total_enrollment` | float | October 1 enrollment count | 73% |
| `dropout_rate` | float | District dropout rate (%), Subgroup = All | 66% |
| `num_enrolled` | string | Number of students enrolled (dropout denominator) | 7% |
| `num_dropouts` | string | Number of dropouts | 7% |
| `grad_rate_4yr` | float | 4-year cohort graduation rate (%) | 45% |
| `num_in_cohort` | float | Number of students in graduation cohort | 45% |
| `num_graduated` | float | Number who graduated in 4 years | 44% |

### Superintendent Fields

Joined from hand-collected 2025-2026 superintendent data on `ctds_id`. These are the **current** superintendent's characteristics, applied to all election years for that district.

| Column | Type | Description | Fill Rate |
|--------|------|-------------|-----------|
| `superintendent` | string | Current superintendent name | 11% |
| `supt_hire_year` | float | Year current superintendent was hired | 11% |
| `supt_tenure_at_election` | float | `year` minus `supt_hire_year`. Negative = superintendent was hired after this election. | 11% |
| `supt_gender` | string | Male / Female | 11% |
| `prior_supt_experience` | string | Yes / No — had prior superintendent experience before this role | 10% |
| `prior_admin_experience` | string | Yes / No — had prior district administration experience | 10% |
| `prior_principal_experience` | string | Yes / No — had prior principal experience | 9% |
| `internal_vs_external` | string | Internal (promoted from within district) or External hire | 10% |
| `advanced_degree` | string | Highest degree: Doctorate, Masters, Specialist, J.D., Ed.S. | 8% |

---

## az_district_year_summary.csv

One row per district per election year. 299 rows. Filtered to clean governing board races only (excludes bonds, overrides, county superintendent, and rows without `ctds_id`).

### Identifier Fields

| Column | Type | Description |
|--------|------|-------------|
| `year` | float | Election year |
| `election_date` | string | Full election date |
| `election_type` | string | `general` or `primary` |
| `county` | string | Arizona county |
| `school_district` | string | District name as it appears on the ballot |
| `ctds_id` | int | ADE CTDS Entity ID |
| `nces_leaid` | float | NCES national LEA identifier |
| `ccd_lea_name` | string | Standardized LEA name from CCD |

### Election Variables

| Column | Type | Description |
|--------|------|-------------|
| `num_candidates` | int | Number of real candidates (excludes write-ins) |
| `num_seats` | float | Number of winners (proxy for seats up for election) |
| `candidates_per_seat` | float | `num_candidates / num_seats` — competitiveness ratio. Higher = more competitive. |
| `contested` | float | Binary: `1` if more candidates than seats, `0` if uncontested |
| `total_votes_cast` | float | Sum of all votes cast in this race |
| `winner_margin_votes` | float | Vote gap between the last winner and the first loser |
| `winner_margin_pct` | float | `winner_margin_votes / total_votes_cast * 100` |
| `winner_names` | string | Semicolon-separated list of winning candidates |

### Accountability Variables

| Column | Type | Description |
|--------|------|-------------|
| `lea_letter_grade` | string | ADE A-F letter grade |
| `grade_numeric` | float | Numeric encoding: A=4, B=3, C=2, D=1, F=0 |
| `total_enrollment` | float | October 1 enrollment |
| `log_enrollment` | float | Natural log of enrollment |
| `district_size` | string | `small` (<1,000), `medium` (1,000-10,000), `large` (10,000+) |
| `dropout_rate` | float | District dropout rate (%) |
| `grad_rate_4yr` | float | 4-year graduation rate (%) |
| `votes_per_student` | float | `total_votes_cast / total_enrollment` — voter engagement relative to district size |

### Superintendent Variables

Same as master file — see definitions above.

---

## Known Limitations

1. **Name inconsistency**: Candidate names change format across years (`LAST, FIRST` vs `First LAST`). District names on ballots also vary by county and year. Fuzzy matching would be needed for any cross-year candidate tracking.

2. **A-F grade gaps**: ADE did not publish A-F grades in FY2015-2016 or FY2020-2021 (COVID moratorium). These years are structurally null.

3. **Graduation rate coverage**: Only ~50% of districts have graduation rates because elementary-only districts (ESDs) do not have high school graduation cohorts.

4. **Superintendent data is a 2025-2026 snapshot**: The `supt_tenure_at_election` variable is negative for elections that predate the current superintendent's hire. Historical superintendent data (back to 2013) is in progress.

5. **2024 Maricopa data**: Some 2024 Maricopa County results were reported under generic office names ("Governing Board Member-4yr") without district-specific identifiers. These 208 rows are in the master file but excluded from the summary due to missing `ctds_id`.

6. **Winner flag**: Only 23% of master rows have the `winner` field populated. This appears to be a source data limitation, not a processing error.
