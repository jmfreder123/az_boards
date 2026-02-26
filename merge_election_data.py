#!/usr/bin/env python3
"""
Merge AZ SOS voter registration data with OpenElections turnout data.

Produces a unified CSV with county-level registration (from SOS) and
ballots cast / turnout (from OpenElections precinct files).
"""

import csv

SOS_FILE = 'az_sos_voter_registration.csv'
TURNOUT_FILE = 'az_county_election_turnout.csv'
OUTPUT_FILE = 'az_county_election_data.csv'


def main():
    # Load SOS registration data (authoritative for registered voters)
    sos = {}
    with open(SOS_FILE) as f:
        for row in csv.DictReader(f):
            key = (int(row['year']), row['county'])
            sos[key] = row

    # Load OpenElections turnout data (ballots cast, early/eday/provisional)
    oe = {}
    with open(TURNOUT_FILE) as f:
        for row in csv.DictReader(f):
            key = (int(row['year']), row['county'])
            oe[key] = row

    # Merge: SOS is the base (all 15 counties x 6 years = 90 rows)
    # Supplement with OpenElections ballots_cast and vote method breakdowns
    rows = []
    for key in sorted(sos.keys()):
        year, county = key
        s = sos[key]
        o = oe.get(key, {})

        reg_sos = int(s['registered_voters_sos'])

        # Use OpenElections ballots_cast if available
        ballots = o.get('ballots_cast', '')
        ballots_int = int(ballots) if ballots else None

        # Compute turnout from SOS registration + OpenElections ballots
        # Note: 2014 OpenElections ballots_cast may be inflated (OpenElections
        # registered voter counts were ~2x SOS active counts, suggesting the
        # source files mixed ACTIVE+INACTIVE registrations). Treat 2014 turnout
        # with caution.
        turnout = ''
        if ballots_int and reg_sos > 0:
            turnout = round(ballots_int / reg_sos * 100, 1)

        rows.append({
            'year': year,
            'election_date': s['election_date'],
            'county': county,
            'registered_voters': reg_sos,
            'dem_registration': s.get('dem_registration', ''),
            'rep_registration': s.get('rep_registration', ''),
            'lib_registration': s.get('lib_registration', ''),
            'green_registration': s.get('green_registration', ''),
            'other_registration': s.get('other_registration', ''),
            'ballots_cast': ballots if ballots else '',
            'turnout_pct': turnout,
            'early_voting': o.get('early_voting', ''),
            'election_day': o.get('election_day', ''),
            'provisional': o.get('provisional', ''),
            'turnout_source': 'OpenElections' if ballots_int else '',
            'registration_source': 'AZ_SOS',
        })

    # Write output
    cols = ['year', 'election_date', 'county',
            'registered_voters', 'dem_registration', 'rep_registration',
            'lib_registration', 'green_registration', 'other_registration',
            'ballots_cast', 'turnout_pct',
            'early_voting', 'election_day', 'provisional',
            'turnout_source', 'registration_source']

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print(f"Output: {OUTPUT_FILE}")
    print(f"Total rows: {len(rows)}")
    print()

    for year in sorted(set(r['year'] for r in rows)):
        yr = [r for r in rows if r['year'] == year]
        total_reg = sum(r['registered_voters'] for r in yr)
        with_ballots = [r for r in yr if r['ballots_cast']]
        total_bal = sum(int(r['ballots_cast']) for r in with_ballots)
        missing = [r['county'] for r in yr if not r['ballots_cast']]
        state_turnout = round(total_bal / total_reg * 100, 1) if total_bal else 'N/A'
        print(f"{year}: {len(yr)} counties, {total_reg:,} registered, "
              f"{total_bal:,} ballots ({len(with_ballots)}/15 with turnout)")
        if missing:
            print(f"       Missing turnout: {', '.join(missing)}")
        print(f"       State turnout: {state_turnout}%")


if __name__ == '__main__':
    main()
