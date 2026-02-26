#!/usr/bin/env python3
"""
Data audit for az_school_board_master.csv and az_district_year_summary.csv.
Checks: completeness, type validity, range/outlier issues, consistency,
cross-file validation.
"""

import csv
import math
from collections import Counter, defaultdict

MASTER = 'az_school_board_master.csv'
SUMMARY = 'az_district_year_summary.csv'

# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────

def load(path):
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames), list(reader)

def to_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def to_int(val):
    f = to_float(val)
    return int(f) if f is not None else None

def pct(n, total):
    return f"{n}/{total} ({100*n/total:.1f}%)" if total else "0/0"

def section(title):
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)

def subsection(title):
    print()
    print(f"--- {title} ---")


# ──────────────────────────────────────────────────────────────────────
# 1. MASTER AUDIT
# ──────────────────────────────────────────────────────────────────────

def audit_master():
    cols, rows = load(MASTER)
    N = len(rows)
    section(f"MASTER CSV AUDIT  ({N} rows, {len(cols)} columns)")

    # -- Completeness -----------------------------------------------
    subsection("1. Column Completeness")
    print(f"{'Column':<32} {'Filled':>8} {'Empty':>8} {'Fill%':>7}")
    print("-" * 60)
    for c in cols:
        filled = sum(1 for r in rows if r[c].strip())
        empty = N - filled
        print(f"{c:<32} {filled:>8} {empty:>8} {100*filled/N:>6.1f}%")

    # -- Year / election_date consistency ---------------------------
    subsection("2. Year & Election Date")
    for y in sorted(set(r['year'] for r in rows)):
        yr = [r for r in rows if r['year'] == y]
        dates = Counter(r['election_date'] for r in yr)
        types = Counter(r['election_type'] for r in yr)
        counties = len(set(r['county'] for r in yr))
        districts = len(set(r['school_district'] for r in yr))
        print(f"  {y}: {len(yr)} rows, {counties} counties, {districts} districts")
        print(f"         dates={dict(dates)}, types={dict(types)}")

    # -- CTDS ID checks ---------------------------------------------
    subsection("3. CTDS ID Checks")
    missing_ctds = [r for r in rows if not r['ctds_id'].strip()]
    print(f"  Missing ctds_id: {len(missing_ctds)}")

    # Check format (should be numeric)
    bad_ctds = []
    for r in rows:
        v = r['ctds_id'].strip()
        if v:
            f = to_float(v)
            if f is None:
                bad_ctds.append(v)
    if bad_ctds:
        print(f"  Non-numeric ctds_id values: {set(bad_ctds)}")
    else:
        print(f"  All ctds_id values are numeric")

    ctds_vals = [to_int(r['ctds_id']) for r in rows if r['ctds_id'].strip()]
    if ctds_vals:
        print(f"  Range: {min(ctds_vals)} - {max(ctds_vals)}")

    # -- NCES LEAID checks -----------------------------------------
    subsection("4. NCES LEA ID Checks")
    nces_filled = sum(1 for r in rows if r['nces_leaid'].strip())
    print(f"  Filled: {pct(nces_filled, N)}")

    # Check if CTDS ↔ NCES mapping is consistent
    ctds_to_nces = defaultdict(set)
    for r in rows:
        ct = r['ctds_id'].strip()
        nc = r['nces_leaid'].strip()
        if ct and nc:
            ctds_to_nces[ct].add(nc)
    multi_nces = {k: v for k, v in ctds_to_nces.items() if len(v) > 1}
    if multi_nces:
        print(f"  WARNING: {len(multi_nces)} ctds_id(s) map to multiple nces_leaid:")
        for k, v in sorted(multi_nces.items())[:5]:
            print(f"    ctds={k} -> nces={v}")
    else:
        print(f"  CTDS → NCES mapping is 1-to-1 (consistent)")

    # -- Vote totals ------------------------------------------------
    subsection("5. Vote Data")
    for r in rows:
        total = to_float(r['total_votes'])
        ev = to_float(r.get('early_voting', ''))
        ed = to_float(r.get('election_day', ''))
        pv = to_float(r.get('provisional', ''))
        if total is not None and ev is not None and ed is not None:
            components = ev + ed + (pv or 0)
            if abs(total - components) > 1:
                print(f"  MISMATCH: {r['year']} {r['county']} {r['candidate']}: "
                      f"total={total}, early+ed+prov={components}")
                break
    else:
        # Check a count instead
        pass

    has_total = sum(1 for r in rows if to_float(r['total_votes']) is not None)
    has_early = sum(1 for r in rows if to_float(r.get('early_voting', '')) is not None)
    print(f"  total_votes filled: {pct(has_total, N)}")
    print(f"  early_voting filled: {pct(has_early, N)}")

    # Zero vote candidates
    zero_votes = [r for r in rows if to_float(r['total_votes']) == 0]
    print(f"  Candidates with 0 votes: {len(zero_votes)}")
    if zero_votes:
        for r in zero_votes[:3]:
            print(f"    {r['year']} {r['county']} {r['school_district']} - {r['candidate']}")

    # Negative votes
    neg_votes = [r for r in rows if (to_float(r['total_votes']) or 0) < 0]
    if neg_votes:
        print(f"  WARNING: {len(neg_votes)} rows with negative total_votes!")
    else:
        print(f"  No negative vote counts")

    # Vote outliers
    votes = [to_float(r['total_votes']) for r in rows if to_float(r['total_votes']) is not None]
    if votes:
        votes_sorted = sorted(votes)
        p50 = votes_sorted[len(votes_sorted)//2]
        p95 = votes_sorted[int(len(votes_sorted)*0.95)]
        p99 = votes_sorted[int(len(votes_sorted)*0.99)]
        print(f"  Vote distribution: min={min(votes):.0f}, median={p50:.0f}, "
              f"p95={p95:.0f}, p99={p99:.0f}, max={max(votes):.0f}")

    # -- Winner field -----------------------------------------------
    subsection("6. Winner Field")
    winner_vals = Counter(r['winner'] for r in rows)
    print(f"  Value distribution: {dict(winner_vals)}")

    # Check each district-year has at least one winner
    dist_year = defaultdict(list)
    for r in rows:
        dist_year[(r['year'], r['school_district'])].append(r)

    no_winner = []
    for (y, d), rlist in dist_year.items():
        winners = [r for r in rlist if r['winner'].strip().upper() in ('TRUE', 'YES', '1', 'Y')]
        if not winners:
            no_winner.append((y, d, len(rlist)))
    if no_winner:
        print(f"  District-years with no winner marked: {len(no_winner)}")
        for y, d, n in no_winner[:5]:
            print(f"    {y} {d} ({n} candidates)")
    else:
        print(f"  All district-years have at least one winner marked")

    # -- School performance data ------------------------------------
    subsection("7. School Performance Data")
    perf_cols = ['lea_letter_grade', 'total_enrollment', 'dropout_rate', 'grad_rate_4yr']
    for c in perf_cols:
        filled = sum(1 for r in rows if r[c].strip())
        print(f"  {c}: {pct(filled, N)}")

    # Letter grade distribution
    grades = Counter(r['lea_letter_grade'] for r in rows if r['lea_letter_grade'].strip())
    if grades:
        print(f"  Letter grade distribution: {dict(sorted(grades.items()))}")

    # Enrollment range
    enrollments = [to_float(r['total_enrollment']) for r in rows if to_float(r['total_enrollment']) is not None]
    if enrollments:
        print(f"  Enrollment range: {min(enrollments):.0f} - {max(enrollments):.0f}, "
              f"median={sorted(enrollments)[len(enrollments)//2]:.0f}")

    # Dropout rate sanity
    drs = [to_float(r['dropout_rate']) for r in rows if to_float(r['dropout_rate']) is not None]
    if drs:
        bad_dr = [d for d in drs if d < 0 or d > 100]
        print(f"  Dropout rates: {len(drs)} values, range {min(drs):.2f}-{max(drs):.2f}")
        if bad_dr:
            print(f"    WARNING: {len(bad_dr)} values outside 0-100 range")

    # Grad rate sanity
    grs = [to_float(r['grad_rate_4yr']) for r in rows if to_float(r['grad_rate_4yr']) is not None]
    if grs:
        bad_gr = [g for g in grs if g < 0 or g > 100]
        print(f"  Grad rates: {len(grs)} values, range {min(grs):.2f}-{max(grs):.2f}")
        if bad_gr:
            print(f"    WARNING: {len(bad_gr)} values outside 0-100 range")

    # -- Superintendent data ----------------------------------------
    subsection("8. Superintendent Data")
    supt_cols = ['superintendent', 'supt_hire_year', 'supt_gender',
                 'prior_supt_experience', 'prior_admin_experience',
                 'prior_principal_experience', 'internal_vs_external', 'advanced_degree',
                 'supt_tenure_at_election']
    for c in supt_cols:
        filled = sum(1 for r in rows if r[c].strip())
        print(f"  {c}: {pct(filled, N)}")

    # Gender distribution
    genders = Counter(r['supt_gender'] for r in rows if r['supt_gender'].strip())
    if genders:
        print(f"  Gender distribution: {dict(genders)}")

    # -- County election data ---------------------------------------
    subsection("9. County Election Data")
    county_cols = ['county_registered_voters', 'county_dem_registration',
                   'county_rep_registration', 'county_lib_registration',
                   'county_other_registration', 'county_ballots_cast', 'county_turnout_pct']
    for c in county_cols:
        filled = sum(1 for r in rows if r[c].strip())
        print(f"  {c}: {pct(filled, N)}")

    # Registration sanity: dem + rep + lib + other should be close to total
    subsection("10. Registration Consistency Check")
    checked = 0
    mismatches = 0
    for r in rows:
        total_reg = to_float(r['county_registered_voters'])
        dem = to_float(r['county_dem_registration'])
        rep = to_float(r['county_rep_registration'])
        lib = to_float(r['county_lib_registration'])
        other = to_float(r['county_other_registration'])
        if all(v is not None for v in [total_reg, dem, rep, lib, other]):
            checked += 1
            component_sum = dem + rep + lib + other
            if abs(total_reg - component_sum) > 1:
                if mismatches < 3:
                    print(f"  NOTE: {r['year']} {r['county']}: total_reg={total_reg:.0f}, "
                          f"sum(parties)={component_sum:.0f}, diff={total_reg-component_sum:.0f}")
                mismatches += 1
    if mismatches:
        print(f"  {mismatches}/{checked} rows have registration sum != total "
              f"(likely due to 'green' party not included in 'other')")
    else:
        print(f"  All {checked} rows: party registration sums match total")

    # Turnout sanity
    turnouts = [to_float(r['county_turnout_pct']) for r in rows if to_float(r['county_turnout_pct']) is not None]
    if turnouts:
        bad_t = [t for t in turnouts if t < 0 or t > 100]
        print(f"  Turnout range: {min(turnouts):.1f}% - {max(turnouts):.1f}%")
        if bad_t:
            print(f"    WARNING: {len(bad_t)} turnout values outside 0-100%")

    # -- Duplicate check --------------------------------------------
    subsection("11. Duplicate Rows")
    keys = Counter()
    for r in rows:
        key = (r['year'], r['county'], r['school_district'], r['candidate'])
        keys[key] += 1
    dupes = {k: v for k, v in keys.items() if v > 1}
    if dupes:
        print(f"  {len(dupes)} duplicate (year, county, district, candidate) combos:")
        for (y, co, d, c), n in sorted(dupes.items())[:10]:
            print(f"    {y} | {co} | {d} | {c} (x{n})")
    else:
        print(f"  No duplicate (year, county, district, candidate) combos")

    return cols, rows


# ──────────────────────────────────────────────────────────────────────
# 2. SUMMARY AUDIT
# ──────────────────────────────────────────────────────────────────────

def audit_summary():
    cols, rows = load(SUMMARY)
    N = len(rows)
    section(f"SUMMARY CSV AUDIT  ({N} rows, {len(cols)} columns)")

    # -- Completeness -----------------------------------------------
    subsection("1. Column Completeness")
    print(f"{'Column':<32} {'Filled':>8} {'Empty':>8} {'Fill%':>7}")
    print("-" * 60)
    for c in cols:
        filled = sum(1 for r in rows if r[c].strip())
        empty = N - filled
        print(f"{c:<32} {filled:>8} {empty:>8} {100*filled/N:>6.1f}%")

    # -- Computed field validation ----------------------------------
    subsection("2. Computed Fields")

    # candidates_per_seat = num_candidates / num_seats
    cps_issues = 0
    for r in rows:
        nc = to_float(r['num_candidates'])
        ns = to_float(r['num_seats'])
        cps = to_float(r['candidates_per_seat'])
        if nc is not None and ns is not None and ns > 0 and cps is not None:
            expected = nc / ns
            if abs(cps - expected) > 0.01:
                if cps_issues < 3:
                    print(f"  candidates_per_seat mismatch: {r['year']} {r['school_district']}: "
                          f"nc={nc}, ns={ns}, cps={cps}, expected={expected:.2f}")
                cps_issues += 1
    print(f"  candidates_per_seat mismatches: {cps_issues}")

    # contested = candidates > seats
    contested_issues = 0
    for r in rows:
        nc = to_float(r['num_candidates'])
        ns = to_float(r['num_seats'])
        contested = r['contested'].strip()
        if nc is not None and ns is not None and contested:
            expected = nc > ns
            actual = contested.upper() in ('TRUE', 'YES', '1')
            if expected != actual:
                if contested_issues < 3:
                    print(f"  contested mismatch: {r['year']} {r['school_district']}: "
                          f"nc={nc}, ns={ns}, contested={contested}")
                contested_issues += 1
    print(f"  contested field mismatches: {contested_issues}")

    # -- District uniqueness ----------------------------------------
    subsection("3. District-Year Uniqueness")
    keys = Counter()
    for r in rows:
        key = (r['year'], r['school_district'])
        keys[key] += 1
    dupes = {k: v for k, v in keys.items() if v > 1}
    if dupes:
        print(f"  WARNING: {len(dupes)} duplicate (year, district) combos")
        for (y, d), n in sorted(dupes.items())[:5]:
            print(f"    {y} | {d} (x{n})")
    else:
        print(f"  All (year, district) combos are unique — PASS")

    # -- CTDS / NCES fill ------------------------------------------
    subsection("4. Identifier Coverage")
    ctds_filled = sum(1 for r in rows if r['ctds_id'].strip())
    nces_filled = sum(1 for r in rows if r['nces_leaid'].strip())
    ccd_filled = sum(1 for r in rows if r['ccd_lea_name'].strip())
    print(f"  ctds_id:      {pct(ctds_filled, N)}")
    print(f"  nces_leaid:   {pct(nces_filled, N)}")
    print(f"  ccd_lea_name: {pct(ccd_filled, N)}")

    # -- Numerical ranges -------------------------------------------
    subsection("5. Numerical Ranges & Outliers")
    num_cols = {
        'num_candidates': (1, 50),
        'num_seats': (1, 10),
        'total_votes_cast': (0, 500000),
        'total_enrollment': (1, 400000),
        'dropout_rate': (0, 100),
        'grad_rate_4yr': (0, 100),
        'county_turnout_pct': (0, 100),
    }
    for col, (lo, hi) in num_cols.items():
        vals = [to_float(r[col]) for r in rows if to_float(r[col]) is not None]
        if not vals:
            print(f"  {col}: no data")
            continue
        out_of_range = [v for v in vals if v < lo or v > hi]
        print(f"  {col}: n={len(vals)}, range=[{min(vals):.1f}, {max(vals):.1f}], "
              f"out-of-range={len(out_of_range)}")

    # -- Margin checks ---------------------------------------------
    subsection("6. Winner Margin Checks")
    neg_margin = [r for r in rows
                  if to_float(r['winner_margin_pct']) is not None
                  and to_float(r['winner_margin_pct']) < 0]
    if neg_margin:
        print(f"  WARNING: {len(neg_margin)} rows with negative winner_margin_pct")
        for r in neg_margin[:3]:
            print(f"    {r['year']} {r['school_district']}: {r['winner_margin_pct']}%")
    else:
        margins = [to_float(r['winner_margin_pct']) for r in rows if to_float(r['winner_margin_pct']) is not None]
        if margins:
            print(f"  All {len(margins)} margins >= 0. Range: {min(margins):.1f}% - {max(margins):.1f}%")

    # -- Performance data by year -----------------------------------
    subsection("7. Performance Data Coverage by Year")
    perf_cols = ['lea_letter_grade', 'total_enrollment', 'dropout_rate', 'grad_rate_4yr']
    print(f"  {'Year':<10}", end='')
    for c in perf_cols:
        print(f"  {c[:15]:>15}", end='')
    print()
    for y in sorted(set(r['year'] for r in rows)):
        yr = [r for r in rows if r['year'] == y]
        print(f"  {y:<10}", end='')
        for c in perf_cols:
            filled = sum(1 for r in yr if r[c].strip())
            print(f"  {filled:>6}/{len(yr):<6}", end='')
        print()

    return cols, rows


# ──────────────────────────────────────────────────────────────────────
# 3. CROSS-FILE VALIDATION
# ──────────────────────────────────────────────────────────────────────

def cross_validate():
    _, master_rows = load(MASTER)
    _, summary_rows = load(SUMMARY)

    section("CROSS-FILE VALIDATION")

    # -- District-years in both files --------------------------------
    subsection("1. District-Year Coverage")
    master_dy = set()
    for r in master_rows:
        master_dy.add((r['year'], r['school_district']))
    summary_dy = set()
    for r in summary_rows:
        summary_dy.add((r['year'], r['school_district']))

    in_both = master_dy & summary_dy
    master_only = master_dy - summary_dy
    summary_only = summary_dy - master_dy
    print(f"  In both files:  {len(in_both)}")
    print(f"  Master only:    {len(master_only)}")
    print(f"  Summary only:   {len(summary_only)}")
    if master_only:
        print(f"  Sample master-only: {sorted(master_only)[:5]}")
    if summary_only:
        print(f"  Sample summary-only: {sorted(summary_only)[:5]}")

    # -- Vote totals cross-check ------------------------------------
    subsection("2. Vote Total Cross-Check")
    # Sum total_votes per district-year from master, compare to summary total_votes_cast
    master_votes = defaultdict(float)
    master_candidates = defaultdict(int)
    for r in master_rows:
        key = (r['year'], r['school_district'])
        v = to_float(r['total_votes'])
        if v is not None:
            master_votes[key] += v
            master_candidates[key] += 1

    summary_votes = {}
    for r in summary_rows:
        key = (r['year'], r['school_district'])
        v = to_float(r['total_votes_cast'])
        if v is not None:
            summary_votes[key] = v

    mismatches = 0
    checked = 0
    for key in in_both:
        mv = master_votes.get(key)
        sv = summary_votes.get(key)
        if mv is not None and sv is not None:
            checked += 1
            if abs(mv - sv) > 1:
                if mismatches < 5:
                    print(f"  MISMATCH: {key}: master_sum={mv:.0f}, summary={sv:.0f}, "
                          f"diff={mv-sv:.0f} ({master_candidates[key]} candidates)")
                mismatches += 1
    print(f"  Checked {checked} district-years, {mismatches} mismatches")

    # -- Candidate count cross-check --------------------------------
    subsection("3. Candidate Count Cross-Check")
    summary_ncand = {}
    for r in summary_rows:
        key = (r['year'], r['school_district'])
        v = to_float(r['num_candidates'])
        if v is not None:
            summary_ncand[key] = int(v)

    cand_mismatches = 0
    for key in in_both:
        mc = master_candidates.get(key, 0)
        sc = summary_ncand.get(key)
        if sc is not None and mc != sc:
            if cand_mismatches < 5:
                print(f"  MISMATCH: {key}: master has {mc} rows, summary says {sc} candidates")
            cand_mismatches += 1
    print(f"  Checked {len([k for k in in_both if k in summary_ncand])} district-years, "
          f"{cand_mismatches} mismatches")

    # -- CTDS consistency across files -------------------------------
    subsection("4. CTDS Consistency Across Files")
    master_ctds = {}
    for r in master_rows:
        d = r['school_district']
        c = r['ctds_id'].strip()
        if c:
            master_ctds.setdefault(d, set()).add(c)

    summary_ctds = {}
    for r in summary_rows:
        d = r['school_district']
        c = r['ctds_id'].strip()
        if c:
            summary_ctds.setdefault(d, set()).add(c)

    ctds_conflicts = 0
    for d in set(master_ctds.keys()) & set(summary_ctds.keys()):
        if master_ctds[d] != summary_ctds[d]:
            if ctds_conflicts < 3:
                print(f"  CONFLICT: '{d}': master={master_ctds[d]}, summary={summary_ctds[d]}")
            ctds_conflicts += 1
    if ctds_conflicts:
        print(f"  {ctds_conflicts} districts with conflicting CTDS between files")
    else:
        print(f"  All shared districts have consistent CTDS IDs — PASS")

    # -- County election data consistency ---------------------------
    subsection("5. County Data Consistency Across Files")
    master_county = {}
    for r in master_rows:
        key = (r['year'], r['county'])
        master_county[key] = r['county_registered_voters']

    summary_county = {}
    for r in summary_rows:
        key = (r['year'], r['county'])
        summary_county[key] = r['county_registered_voters']

    county_mismatches = 0
    for key in set(master_county.keys()) & set(summary_county.keys()):
        if master_county[key] != summary_county[key]:
            print(f"  MISMATCH: {key}: master={master_county[key]}, summary={summary_county[key]}")
            county_mismatches += 1
    if county_mismatches:
        print(f"  {county_mismatches} county-year mismatches")
    else:
        print(f"  All county-year registration data matches — PASS")


# ──────────────────────────────────────────────────────────────────────
# 4. SUMMARY REPORT
# ──────────────────────────────────────────────────────────────────────

def overall_summary():
    _, master_rows = load(MASTER)
    _, summary_rows = load(SUMMARY)

    section("OVERALL DATA QUALITY SUMMARY")

    years = sorted(set(r['year'] for r in master_rows))
    counties = sorted(set(r['county'] for r in master_rows))
    districts = sorted(set(r['school_district'] for r in master_rows))

    print(f"  Years covered: {len(years)} ({years[0]} - {years[-1]})")
    print(f"  Counties: {len(counties)}")
    print(f"  Unique districts: {len(districts)}")
    print(f"  Master rows: {len(master_rows)}")
    print(f"  Summary rows: {len(summary_rows)}")
    print()

    # Key column fill rates
    key_cols_master = [
        ('ctds_id', 'CTDS ID'),
        ('nces_leaid', 'NCES LEA ID'),
        ('total_votes', 'Vote totals'),
        ('winner', 'Winner flag'),
        ('lea_letter_grade', 'Letter grade'),
        ('total_enrollment', 'Enrollment'),
        ('dropout_rate', 'Dropout rate'),
        ('grad_rate_4yr', 'Grad rate'),
        ('superintendent', 'Superintendent'),
        ('county_registered_voters', 'County registration'),
        ('county_ballots_cast', 'County ballots'),
    ]
    print(f"  {'Master Column':<25} {'Fill Rate':>12}")
    print(f"  {'-'*25} {'-'*12}")
    for col, label in key_cols_master:
        filled = sum(1 for r in master_rows if r[col].strip())
        print(f"  {label:<25} {100*filled/len(master_rows):>10.1f}%")


# ──────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    audit_master()
    audit_summary()
    cross_validate()
    overall_summary()
