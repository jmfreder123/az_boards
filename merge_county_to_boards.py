#!/usr/bin/env python3
"""
Merge county-level election data (voter registration, turnout, party breakdown)
into the school board master and summary CSVs.

Join key: (year, county). Adds columns prefixed with 'county_' to avoid
collisions with existing candidate/district-level fields.
"""

import csv

ELECTION_DATA = 'az_county_election_data.csv'
MASTER_FILE = 'az_school_board_master.csv'
SUMMARY_FILE = 'az_district_year_summary.csv'

# Columns to add from county election data
COUNTY_COLS = [
    ('registered_voters', 'county_registered_voters'),
    ('dem_registration', 'county_dem_registration'),
    ('rep_registration', 'county_rep_registration'),
    ('lib_registration', 'county_lib_registration'),
    ('other_registration', 'county_other_registration'),
    ('ballots_cast', 'county_ballots_cast'),
    ('turnout_pct', 'county_turnout_pct'),
]


def load_election_data():
    """Load county election data keyed by (year_int, county)."""
    data = {}
    with open(ELECTION_DATA) as f:
        for row in csv.DictReader(f):
            key = (int(row['year']), row['county'])
            data[key] = row
    return data


def normalize_year(year_str):
    """Convert '2014.0' or '2014' to int 2014."""
    try:
        return int(float(year_str))
    except (ValueError, TypeError):
        return None


def merge_into_file(filepath, election_data):
    """Read a CSV, add county columns, write it back."""
    with open(filepath) as f:
        reader = csv.DictReader(f)
        old_cols = list(reader.fieldnames)
        rows = list(reader)

    # Remove any existing county_ columns from prior runs
    new_county_col_names = [nc for _, nc in COUNTY_COLS]
    clean_cols = [c for c in old_cols if c not in new_county_col_names]

    # Build new column list
    new_cols = clean_cols + new_county_col_names

    matched = 0
    unmatched_keys = set()

    for row in rows:
        year = normalize_year(row.get('year', ''))
        county = row.get('county', '').strip()

        if year and county:
            key = (year, county)
            edata = election_data.get(key, {})
            if edata:
                matched += 1
            else:
                unmatched_keys.add(key)

            for src_col, dst_col in COUNTY_COLS:
                row[dst_col] = edata.get(src_col, '')
        else:
            for _, dst_col in COUNTY_COLS:
                row[dst_col] = ''

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_cols, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    return matched, len(rows), unmatched_keys


def main():
    election_data = load_election_data()
    print("Loaded {} county-year records from {}".format(len(election_data), ELECTION_DATA))
    print()

    # Merge into master
    print("=== Merging into {} ===".format(MASTER_FILE))
    matched, total, unmatched = merge_into_file(MASTER_FILE, election_data)
    print("  {} / {} rows matched on (year, county)".format(matched, total))
    if unmatched:
        print("  Unmatched keys: {}".format(sorted(unmatched)))
    print()

    # Merge into summary
    print("=== Merging into {} ===".format(SUMMARY_FILE))
    matched, total, unmatched = merge_into_file(SUMMARY_FILE, election_data)
    print("  {} / {} rows matched on (year, county)".format(matched, total))
    if unmatched:
        print("  Unmatched keys: {}".format(sorted(unmatched)))
    print()

    # Verify
    print("=== Verification ===")
    for filepath in [MASTER_FILE, SUMMARY_FILE]:
        with open(filepath) as f:
            reader = csv.DictReader(f)
            cols = reader.fieldnames
            rows = list(reader)
        new_cols = [c for c in cols if c.startswith('county_')]
        filled = sum(1 for r in rows if r.get('county_registered_voters', ''))
        print("  {}: {} cols, {} rows, {} with county data, new cols: {}".format(
            filepath, len(cols), len(rows), filled, new_cols))


if __name__ == '__main__':
    main()
