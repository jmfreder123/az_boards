#!/usr/bin/env python3
"""
Parse AZ Secretary of State voter registration CSV files.

Extracts county-level active registered voter counts (total and by party)
for the general election period from each file. Outputs a unified CSV
suitable for merging with the OpenElections turnout data.
"""

import csv
import io
import re
import os

# Files mapped to their election year and the G.E. period label to match
SOS_DIR = 'source_data/sos_voter_registration'

SOS_FILES = {
    '{}/2014-11-04.csv'.format(SOS_DIR):                         (2014, 'G.E. 2014'),
    '{}/2016-11-08.csv'.format(SOS_DIR):                         (2016, 'G.E. 2016'),
    '{}/2018-10-01.csv'.format(SOS_DIR):                         (2018, 'G.E. 2018'),
    '{}/state_voter_reigstration_2020_general.csv'.format(SOS_DIR): (2020, 'G.E. 2020'),
    '{}/State_Voter_Registration_2022_General.csv'.format(SOS_DIR): (2022, 'G.E. 2022'),
    '{}/State_Voter_Registration_October_2024.csv'.format(SOS_DIR): (2024, 'G.E. 2024'),
}

ELECTION_DATES = {
    2014: '2014-11-04', 2016: '2016-11-08', 2018: '2018-11-06',
    2020: '2020-11-03', 2022: '2022-11-08', 2024: '2024-11-05',
}

# Canonical county names
COUNTIES_CANONICAL = [
    'Apache', 'Cochise', 'Coconino', 'Gila', 'Graham', 'Greenlee',
    'La Paz', 'Maricopa', 'Mohave', 'Navajo', 'Pima', 'Pinal',
    'Santa Cruz', 'Yavapai', 'Yuma'
]


def clean_int(s):
    """Parse an integer from a string that may have commas and quotes."""
    if not s:
        return None
    s = s.strip().strip('"').replace(',', '').replace('*', '').strip()
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_2014(filepath):
    """Parse the 2014 format which has an unusual column layout.

    Structure per county:
      Row 1 (odd lines): blank, blank, blank, blank, <americans_elect?>, blank, blank, blank, <dem>, <green>, <lib>, <rep>, blank, blank, blank
      Row 2 (county line): blank, <County>, <precincts>, <period>, blank..., <other>, <total>, blank
    Actual pattern: 3 rows per period per county (G.E. 2012, P.E. 2014, G.E. 2014)
    """
    results = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        text = f.read()

    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    current_county = None
    i = 0
    past_totals = False

    while i < len(lines):
        line = lines[i]
        # Stop at Page Number 2 or INACTIVE section
        if 'Page Number 2' in line or 'INACTIVE' in line.upper():
            break
        if 'PERCENTAGES' in line:
            break

        fields = list(csv.reader(io.StringIO(line)))[0] if line.strip() else []

        if len(fields) < 5:
            i += 1
            continue

        # Detect county name in field[1]
        county_field = fields[1].strip() if len(fields) > 1 else ''
        period_field = fields[3].strip() if len(fields) > 3 else ''

        # Stop collecting when we hit TOTALS
        if 'TOTALS' in county_field.upper():
            past_totals = True

        if not past_totals and county_field and county_field not in ('', 'TOTALS:', 'PERCENTAGES:'):
            # Check if this looks like a county name (not a number)
            if not county_field.replace(',', '').replace('"', '').strip().isdigit():
                current_county = county_field.strip()

        # Check if this line has G.E. 2014 period
        if period_field == 'G.E. 2014' and current_county and not past_totals:
            # Find the TOTAL which is in the second-to-last populated field
            # Format: ,,<precincts>,G.E. 2014,,,,,,,,,"<other>","<total>",
            # The total is typically in field index 13 or the last significant field
            total_val = None
            other_val = None

            # Walk backwards to find total
            for j in range(len(fields) - 1, 5, -1):
                v = clean_int(fields[j])
                if v is not None and v > 1000:
                    if total_val is None:
                        total_val = v
                    elif other_val is None:
                        other_val = v
                        break

            # Previous line has party breakdown: dem, green, lib, rep
            if i > 0:
                prev_fields = list(csv.reader(io.StringIO(lines[i-1])))[0] if lines[i-1].strip() else []
                dem = clean_int(prev_fields[8]) if len(prev_fields) > 8 else None
                green = clean_int(prev_fields[9]) if len(prev_fields) > 9 else None
                lib = clean_int(prev_fields[10]) if len(prev_fields) > 10 else None
                rep = clean_int(prev_fields[11]) if len(prev_fields) > 11 else None
            else:
                dem = green = lib = rep = None

            precincts = clean_int(fields[2]) if len(fields) > 2 else None

            results[current_county] = {
                'precincts': precincts,
                'total': total_val,
                'dem': dem,
                'rep': rep,
                'lib': lib,
                'green': green,
                'other': other_val,
            }

        i += 1

    return results


def parse_2016(filepath):
    """Parse 2016 format with quoted fields.

    Header: Precincts, Date/Period, Democratic, (blank), Green, Libertarian, Republican, Other, TOTAL
    """
    results = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        text = f.read()

    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    current_county = None
    past_totals = False

    for line in lines:
        if not line.strip():
            continue
        if 'Page Number 2' in line:
            break

        fields = list(csv.reader(io.StringIO(line)))[0]

        # Skip header rows
        if any(x in str(fields) for x in ['REGISTRATION REPORT', 'Compiled and Issued',
                                            'ACTIVE', 'Precincts', 'PERCENTAGES']):
            continue

        # Stop collecting when we hit TOTALS
        if len(fields) > 1 and 'TOTALS' in fields[1].upper():
            past_totals = True

        # Detect county (field[1] non-empty, non-numeric, not TOTALS)
        if not past_totals and len(fields) > 1:
            f1 = fields[1].strip()
            if f1 and f1 not in ('TOTALS:', 'PERCENTAGES:') and not f1.replace(',', '').isdigit():
                current_county = f1

        # Check for G.E. 2016 period
        if len(fields) > 3 and 'G.E. 2016' in fields[3]:
            if current_county and not past_totals:
                precincts = clean_int(fields[2]) if len(fields) > 2 else None
                dem = clean_int(fields[4]) if len(fields) > 4 else None
                green = clean_int(fields[6]) if len(fields) > 6 else None
                lib = clean_int(fields[7]) if len(fields) > 7 else None
                rep = clean_int(fields[8]) if len(fields) > 8 else None
                other = clean_int(fields[9]) if len(fields) > 9 else None
                total = clean_int(fields[10]) if len(fields) > 10 else None

                results[current_county] = {
                    'precincts': precincts,
                    'total': total,
                    'dem': dem,
                    'rep': rep,
                    'lib': lib,
                    'green': green,
                    'other': other,
                }

    return results


def parse_standard(filepath, ge_label):
    """Parse 2018-2024 format (similar structure).

    These files have varying numbers of party columns but share:
    County, Precincts, (blank), Date/Period, (blanks), party cols..., Total
    """
    results = {}
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        text = f.read()

    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')

    # Find the header line to determine column positions
    header_line = None
    for line in lines:
        if 'County' in line and 'Precincts' in line and 'Total' in line:
            header_line = line
            break

    if not header_line:
        print(f"  WARNING: No header found in {filepath}")
        return results

    header_fields = list(csv.reader(io.StringIO(header_line)))[0]

    # Find column indices for party names and Total
    col_map = {}
    for idx, h in enumerate(header_fields):
        h_clean = h.strip().lower()
        if h_clean == 'county':
            col_map['county'] = idx
        elif h_clean == 'precincts':
            col_map['precincts'] = idx
        elif h_clean in ('date/period',):
            col_map['period'] = idx
        elif h_clean == 'democratic':
            col_map['dem'] = idx
        elif h_clean == 'republican':
            col_map['rep'] = idx
        elif h_clean == 'libertarian':
            col_map['lib'] = idx
        elif h_clean == 'green':
            col_map['green'] = idx
        elif h_clean in ('no labels',):
            col_map['no_labels'] = idx
        elif h_clean in ('arizona',):
            col_map['arizona'] = idx
        elif h_clean == 'other':
            col_map['other'] = idx
        elif h_clean == 'total':
            col_map['total'] = idx

    # If we didn't find explicit period column, determine it from layout
    if 'period' not in col_map:
        # Period is typically at index 3
        col_map['period'] = 3

    current_county = None
    past_totals = False

    for line in lines:
        if not line.strip():
            continue
        # Stop at Page 2 / Congressional / INACTIVE / Legislative
        stop_words = ['Page Number 2', 'Page: 2', 'Congressional', 'Legislative',
                      'INACTIVE', 'PERCENTAGES']
        if any(sw in line for sw in stop_words):
            break

        fields = list(csv.reader(io.StringIO(line)))[0]

        if len(fields) < 5:
            continue

        # Check for TOTALS row
        county_idx = col_map.get('county', 0)
        if county_idx < len(fields):
            c = fields[county_idx].strip()
            if 'TOTALS' in c.upper() or 'TOTAL' in c.upper():
                past_totals = True

        # Also check if the precincts field contains a statewide precinct count (> 1000)
        # which indicates a totals row even without explicit label
        precincts_idx = col_map.get('precincts', 1)

        # Detect county
        if not past_totals and county_idx < len(fields):
            c = fields[county_idx].strip()
            if c and c not in ('STATE OF ARIZONA REGISTRATION REPORT', 'Active',
                              'County', 'Compiled and Issued') and not c.startswith('20'):
                if not c.replace(',', '').replace('"', '').strip().isdigit():
                    current_county = c

        # Check for G.E. period
        period_idx = col_map.get('period', 3)
        if period_idx < len(fields):
            period = fields[period_idx].strip()
            if period == ge_label and current_county and not past_totals:

                precincts_idx = col_map.get('precincts', 1)
                precincts = clean_int(fields[precincts_idx]) if precincts_idx < len(fields) else None

                # Find Total - it's the last significant numeric column
                total = None
                total_idx = col_map.get('total')
                if total_idx and total_idx < len(fields):
                    total = clean_int(fields[total_idx])

                # If total not found by header, search from the right
                if total is None:
                    for j in range(len(fields) - 1, 4, -1):
                        v = clean_int(fields[j])
                        if v is not None and v > 100:
                            total = v
                            break

                dem = clean_int(fields[col_map['dem']]) if 'dem' in col_map and col_map['dem'] < len(fields) else None
                rep = clean_int(fields[col_map['rep']]) if 'rep' in col_map and col_map['rep'] < len(fields) else None
                lib = clean_int(fields[col_map['lib']]) if 'lib' in col_map and col_map['lib'] < len(fields) else None
                green = clean_int(fields[col_map.get('green', 999)]) if col_map.get('green', 999) < len(fields) else None
                other = clean_int(fields[col_map['other']]) if 'other' in col_map and col_map['other'] < len(fields) else None

                results[current_county] = {
                    'precincts': precincts,
                    'total': total,
                    'dem': dem,
                    'rep': rep,
                    'lib': lib,
                    'green': green,
                    'other': other,
                }

    return results


def normalize_county(name):
    """Normalize county name to canonical form."""
    name = name.strip()
    lookup = {c.lower().replace(' ', ''): c for c in COUNTIES_CANONICAL}
    key = name.lower().replace(' ', '').replace('_', '')
    if key in lookup:
        return lookup[key]
    # Handle "La Paz" variants
    if key in ('lapaz',):
        return 'La Paz'
    if key in ('santacruz',):
        return 'Santa Cruz'
    return name


def main():
    all_rows = []

    for filename, (year, ge_label) in sorted(SOS_FILES.items(), key=lambda x: x[1][0]):
        if not os.path.exists(filename):
            print(f"  SKIP {filename} (not found)")
            continue

        print(f"\n=== {year}: {filename} ===")

        if year == 2014:
            county_data = parse_2014(filename)
        elif year == 2016:
            county_data = parse_2016(filename)
        else:
            county_data = parse_standard(filename, ge_label)

        if not county_data:
            print("  No data extracted!")
            continue

        for county_raw, d in sorted(county_data.items()):
            county = normalize_county(county_raw)
            total = d.get('total')
            if total is None or total < 100:
                continue

            print(f"  {county:15s}: {total:>10,}  (DEM={d.get('dem') or 'N/A':>10}, "
                  f"REP={d.get('rep') or 'N/A':>10}, "
                  f"LIB={d.get('lib') or 'N/A':>8}, "
                  f"OTH={d.get('other') or 'N/A':>10})")

            all_rows.append({
                'year': year,
                'election_date': ELECTION_DATES[year],
                'county': county,
                'num_precincts': d.get('precincts') or '',
                'registered_voters_sos': total,
                'dem_registration': d.get('dem') or '',
                'rep_registration': d.get('rep') or '',
                'lib_registration': d.get('lib') or '',
                'green_registration': d.get('green') or '',
                'other_registration': d.get('other') or '',
            })

    # Write output
    outfile = 'az_sos_voter_registration.csv'
    cols = ['year', 'election_date', 'county', 'num_precincts',
            'registered_voters_sos', 'dem_registration', 'rep_registration',
            'lib_registration', 'green_registration', 'other_registration']

    with open(outfile, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n=== SUMMARY ===")
    print(f"Output: {outfile}")
    print(f"Total rows: {len(all_rows)}")
    for year in sorted(set(r['year'] for r in all_rows)):
        yr = [r for r in all_rows if r['year'] == year]
        total_reg = sum(r['registered_voters_sos'] for r in yr)
        print(f"  {year}: {len(yr)} counties, {total_reg:,} total registered voters")


if __name__ == '__main__':
    main()
