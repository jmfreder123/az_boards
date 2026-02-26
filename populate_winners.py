#!/usr/bin/env python3
"""
Populate the 'winner' column in az_school_board_master.csv using the
top-N-by-votes rule (validated at 100% accuracy against existing labels).

Two passes:
1. Partial district-years (winners marked YES, losers left blank) — fill in
   NO for losing real candidates based on existing YES markers.
2. Fully-missing district-years where num_seats is known from the summary —
   rank real candidates by votes and assign top N as YES, rest as NO.

Non-candidate rows (Write-In, Over/Under Votes, Budget measures) are excluded
from winner selection and left blank.
"""

import csv
import re
from collections import defaultdict

MASTER = 'az_school_board_master.csv'
SUMMARY = 'az_district_year_summary.csv'

# Patterns that indicate a row is NOT a real candidate
NON_CANDIDATE_PATTERNS = [
    r'WRITE.?IN',
    r'NO CANDIDATE',
    r'OVER\s?VOTE',
    r'UNDER\s?VOTE',
    r'BUDGET INCREASE',
    r'BUDGET OVERRIDE',
    r'BOND ELECTION',
    r'BOND APPROVAL',
    r'TIMES COUNTED',
    r'TIMES BLANK',
    r'^TOTAL VOTE',
    r'^TOTALVOTE',
    r'^NOT ASSIGNED$',
]
NON_CANDIDATE_RE = re.compile('|'.join(NON_CANDIDATE_PATTERNS), re.IGNORECASE)


def is_real_candidate(name):
    return not NON_CANDIDATE_RE.search(name)


def main():
    # Load num_seats from summary
    with open(SUMMARY) as f:
        summary = list(csv.DictReader(f))

    seats_lookup = {}
    for r in summary:
        key = (r['year'], r['school_district'])
        ns = r['num_seats'].strip()
        if ns:
            try:
                seats_lookup[key] = int(float(ns))
            except ValueError:
                pass

    # Load master
    with open(MASTER) as f:
        reader = csv.DictReader(f)
        cols = list(reader.fieldnames)
        rows = list(reader)

    # Group rows by district-year
    dy_groups = defaultdict(list)
    for i, r in enumerate(rows):
        key = (r['year'], r['school_district'])
        dy_groups[key].append(i)

    # Stats
    partial_filled_rows = 0
    partial_filled_dys = 0
    newly_inferred_rows = 0
    newly_inferred_dys = 0
    no_seats_info = 0
    already_complete = 0

    for (y, d), indices in dy_groups.items():
        winner_indices_existing = [i for i in indices if rows[i]['winner'].strip()]
        empty_indices = [i for i in indices if not rows[i]['winner'].strip()]

        all_filled = len(empty_indices) == 0
        has_some_winner = len(winner_indices_existing) > 0

        if all_filled:
            # Every row already has YES or NO
            already_complete += len(indices)
            continue

        if has_some_winner:
            # PASS 1: Partial — winners are marked YES, fill in NO for losers
            for i in empty_indices:
                if is_real_candidate(rows[i]['candidate']):
                    rows[i]['winner'] = 'NO'
                # Non-candidate rows stay blank
            partial_filled_rows += len(empty_indices)
            partial_filled_dys += 1
            continue

        # PASS 2: Fully missing — infer from votes + num_seats
        seats = seats_lookup.get((y, d))
        if seats is None:
            no_seats_info += len(indices)
            continue

        real_indices = [i for i in indices if is_real_candidate(rows[i]['candidate'])]

        if not real_indices:
            continue

        # Sort real candidates by votes descending
        real_sorted = sorted(
            real_indices,
            key=lambda i: float(rows[i]['total_votes'] or 0),
            reverse=True
        )

        # Top N are winners
        top_n = set(real_sorted[:seats])

        for i in real_indices:
            rows[i]['winner'] = 'YES' if i in top_n else 'NO'

        # Non-candidate rows stay blank

        newly_inferred_rows += len(indices)
        newly_inferred_dys += 1

    # Write back
    with open(MASTER, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    # Report
    total = len(rows)
    now_filled = sum(1 for r in rows if r['winner'].strip())
    winners = sum(1 for r in rows if r['winner'].strip() == 'YES')
    losers = sum(1 for r in rows if r['winner'].strip() == 'NO')

    print("=== Winner Population Results ===")
    print(f"  Already complete:      {already_complete} rows")
    print(f"  Pass 1 (losers filled):{partial_filled_rows} rows ({partial_filled_dys} district-years)")
    print(f"  Pass 2 (inferred):     {newly_inferred_rows} rows ({newly_inferred_dys} district-years)")
    print(f"  Skipped (no seats):    {no_seats_info} rows")
    print()
    print(f"  Total rows:            {total}")
    print(f"  Winner field filled:   {now_filled} ({100*now_filled/total:.1f}%)")
    print(f"    YES: {winners}")
    print(f"    NO:  {losers}")
    print(f"    Empty: {total - now_filled}")


if __name__ == '__main__':
    main()
