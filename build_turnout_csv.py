#!/usr/bin/env python3
"""
Build comprehensive county-year voter turnout CSV from OpenElections data.
Uses both county-level precinct files and consolidated statewide files.
"""

import csv
import io
import time
import urllib.request

BASE = "https://raw.githubusercontent.com/openelections/openelections-data-az/master"

COUNTIES = [
    "apache", "cochise", "coconino", "gila", "graham", "greenlee",
    "la_paz", "maricopa", "mohave", "navajo", "pima", "pinal",
    "santa_cruz", "yavapai", "yuma"
]

COUNTY_DISPLAY = {
    "apache": "Apache", "cochise": "Cochise", "coconino": "Coconino",
    "gila": "Gila", "graham": "Graham", "greenlee": "Greenlee",
    "la_paz": "La Paz", "maricopa": "Maricopa", "mohave": "Mohave",
    "navajo": "Navajo", "pima": "Pima", "pinal": "Pinal",
    "santa_cruz": "Santa Cruz", "yavapai": "Yavapai", "yuma": "Yuma"
}

# Map display name back to key for matching
DISPLAY_TO_KEY = {v: k for k, v in COUNTY_DISPLAY.items()}
# Also handle variations from consolidated files
DISPLAY_TO_KEY["LaPaz"] = "la_paz"
DISPLAY_TO_KEY["La paz"] = "la_paz"

CONSOLIDATED = {
    2016: "{}/2016/20161108__az__general__precinct.csv".format(BASE),
    2018: "{}/2018/20181106__az__general__precinct.csv".format(BASE),
    2020: "{}/2020/20201103__az__general__precinct.csv".format(BASE),
    2022: "{}/2022/20221108__az__general__precinct.csv".format(BASE),
}

COUNTY_URLS = {}
for c in COUNTIES:
    COUNTY_URLS.setdefault(2014, {})[c] = "{}/2014/20141104__az__general__{}__precinct.csv".format(BASE, c)
    COUNTY_URLS.setdefault(2016, {})[c] = "{}/2016/counties/20161108__az__general__{}__precinct.csv".format(BASE, c)
    COUNTY_URLS.setdefault(2018, {})[c] = "{}/2018/counties/20181106__az__general__{}__precinct.csv".format(BASE, c)
    COUNTY_URLS.setdefault(2020, {})[c] = "{}/2020/counties/20201103__az__general__{}__precinct.csv".format(BASE, c)
    COUNTY_URLS.setdefault(2022, {})[c] = "{}/2022/counties/20221108__az__general__{}__precinct.csv".format(BASE, c)
    COUNTY_URLS.setdefault(2024, {})[c] = "{}/2024/General/20241105__az__general__{}__precinct.csv".format(BASE, c)

ELECTION_DATES = {
    2014: '2014-11-04', 2016: '2016-11-08', 2018: '2018-11-06',
    2020: '2020-11-03', 2022: '2022-11-08', 2024: '2024-11-05'
}


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                return resp.read().decode('utf-8', errors='replace')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                return None


def extract_from_file(text):
    """Extract per-precinct registration and turnout from a CSV file."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []

    # Detect format
    if 'precinct_id' in headers:
        # 2014 format
        precinct_reg = {}
        precinct_bal = {}
        for row in reader:
            p = row.get('precinct_name', row.get('precinct_id', '')).strip()
            cand = row.get('candidate', '').upper()
            cid = row.get('candidate_id', '').strip()
            try:
                count = int(row.get('count', '0').strip())
            except ValueError:
                continue
            if cid == '999997' or 'REGISTERED VOTER' in cand:
                precinct_reg[p] = max(precinct_reg.get(p, 0), count)
            elif cid == '999996' or 'TIMES COUNTED' in cand:
                precinct_bal[p] = max(precinct_bal.get(p, 0), count)

        total_reg = sum(precinct_reg.values()) if precinct_reg else None
        total_bal = sum(precinct_bal.values()) if precinct_bal else None
        return {
            'num_precincts': len(set(list(precinct_reg.keys()) + list(precinct_bal.keys()))),
            'registered_voters': total_reg,
            'ballots_cast': total_bal,
            'early_voting': None, 'election_day': None, 'provisional': None
        }
    else:
        # Standard format
        office_col = None
        precinct_col = None
        votes_col = None
        early_col = None
        eday_col = None
        prov_col = None

        for h in headers:
            hl = h.strip().lower()
            if hl in ('office', 'race'):
                office_col = h
            elif hl in ('precinct', 'precinct_name'):
                precinct_col = h
            elif hl in ('votes', 'count', 'vote_total'):
                votes_col = h
            elif hl in ('early_voting', 'early_votes', 'early'):
                early_col = h
            elif hl in ('election_day', 'polling_place_votes'):
                eday_col = h
            elif hl in ('provisional', 'provisional_votes'):
                prov_col = h

        if not office_col or not precinct_col:
            return None

        precincts = set()
        total_reg = 0
        total_bal = 0
        total_early = 0
        total_eday = 0
        total_prov = 0
        has_reg = False
        has_bal = False

        for row in reader:
            office = row.get(office_col, '').strip().upper()
            p = row.get(precinct_col, '').strip()
            if not p:
                continue
            precincts.add(p)

            if 'REGISTERED VOTER' in office:
                try:
                    total_reg += int(row.get(votes_col, '0').strip())
                    has_reg = True
                except ValueError:
                    pass
            elif ('BALLOTS CAST' in office or 'TIMES COUNTED' in office) and 'BLANK' not in office:
                try:
                    total_bal += int(row.get(votes_col, '0').strip())
                    has_bal = True
                except ValueError:
                    pass
                if early_col:
                    try:
                        total_early += int(row.get(early_col, '0').strip())
                    except ValueError:
                        pass
                if eday_col:
                    try:
                        total_eday += int(row.get(eday_col, '0').strip())
                    except ValueError:
                        pass
                if prov_col:
                    try:
                        total_prov += int(row.get(prov_col, '0').strip())
                    except ValueError:
                        pass

        return {
            'num_precincts': len(precincts),
            'registered_voters': total_reg if has_reg else None,
            'ballots_cast': total_bal if has_bal else None,
            'early_voting': total_early if total_early > 0 else None,
            'election_day': total_eday if total_eday > 0 else None,
            'provisional': total_prov if total_prov > 0 else None,
        }


def extract_consolidated(text):
    """Extract per-county data from consolidated statewide file."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []

    county_col = None
    office_col = None
    precinct_col = None
    votes_col = None
    early_col = None
    eday_col = None
    prov_col = None

    for h in headers:
        hl = h.strip().lower()
        if hl == 'county':
            county_col = h
        elif hl in ('office', 'race'):
            office_col = h
        elif hl in ('precinct', 'precinct_name'):
            precinct_col = h
        elif hl in ('votes', 'count'):
            votes_col = h
        elif hl in ('early_voting', 'early_votes', 'early'):
            early_col = h
        elif hl in ('election_day',):
            eday_col = h
        elif hl in ('provisional',):
            prov_col = h

    if not county_col or not office_col:
        return {}

    counties = {}

    for row in reader:
        county = row.get(county_col, '').strip()
        office = row.get(office_col, '').strip().upper()
        precinct = row.get(precinct_col, '').strip() if precinct_col else ''

        if not county:
            continue

        if county not in counties:
            counties[county] = {'precincts': set(), 'reg': 0, 'bal': 0,
                                'early': 0, 'eday': 0, 'prov': 0,
                                'has_reg': False, 'has_bal': False}

        if precinct:
            counties[county]['precincts'].add(precinct)

        if 'REGISTERED VOTER' in office:
            try:
                counties[county]['reg'] += int(row.get(votes_col, '0').strip())
                counties[county]['has_reg'] = True
            except ValueError:
                pass
        elif ('BALLOTS CAST' in office or 'TIMES COUNTED' in office) and 'BLANK' not in office:
            try:
                counties[county]['bal'] += int(row.get(votes_col, '0').strip())
                counties[county]['has_bal'] = True
            except ValueError:
                pass
            if early_col:
                try:
                    counties[county]['early'] += int(row.get(early_col, '0').strip())
                except ValueError:
                    pass
            if eday_col:
                try:
                    counties[county]['eday'] += int(row.get(eday_col, '0').strip())
                except ValueError:
                    pass
            if prov_col:
                try:
                    counties[county]['prov'] += int(row.get(prov_col, '0').strip())
                except ValueError:
                    pass

    result = {}
    for county, d in counties.items():
        result[county] = {
            'num_precincts': len(d['precincts']),
            'registered_voters': d['reg'] if d['has_reg'] else None,
            'ballots_cast': d['bal'] if d['has_bal'] else None,
            'early_voting': d['early'] if d['early'] > 0 else None,
            'election_day': d['eday'] if d['eday'] > 0 else None,
            'provisional': d['prov'] if d['prov'] > 0 else None,
        }
    return result


def normalize_county(name):
    """Normalize county name to our standard display form."""
    name = name.strip()
    for display, key in DISPLAY_TO_KEY.items():
        if name.lower() == display.lower():
            return COUNTY_DISPLAY[key]
    # Try direct match
    for key, display in COUNTY_DISPLAY.items():
        if name.lower() == display.lower():
            return display
    return name


def main():
    # data[year][county_display] = {...}
    data = {}

    # Step 1: Extract from county-level files
    for year in sorted(COUNTY_URLS.keys()):
        print("\n=== {} (county files) ===".format(year))
        data[year] = {}

        for county_key, url in COUNTY_URLS[year].items():
            display = COUNTY_DISPLAY[county_key]
            text = fetch(url)
            if not text:
                print("  {}: download failed".format(display))
                continue

            result = extract_from_file(text)
            if result and (result['registered_voters'] is not None or result['ballots_cast'] is not None):
                data[year][display] = result
                reg_s = "{:,}".format(result['registered_voters']) if result['registered_voters'] else "N/A"
                bal_s = "{:,}".format(result['ballots_cast']) if result['ballots_cast'] else "N/A"
                print("  {}: reg={}, ballots={}".format(display, reg_s, bal_s))
            else:
                print("  {}: no voter data".format(display))

    # Step 2: Fill gaps from consolidated statewide files
    for year, url in sorted(CONSOLIDATED.items()):
        print("\n=== {} (consolidated fill) ===".format(year))
        text = fetch(url)
        if not text:
            print("  Failed to download")
            continue

        consolidated = extract_consolidated(text)
        filled = 0

        for raw_county, cdata in consolidated.items():
            display = normalize_county(raw_county)

            if display not in data.get(year, {}):
                # Completely missing county — add it
                if cdata['registered_voters'] is not None or cdata['ballots_cast'] is not None:
                    data.setdefault(year, {})[display] = cdata
                    reg_s = "{:,}".format(cdata['registered_voters']) if cdata['registered_voters'] else "N/A"
                    bal_s = "{:,}".format(cdata['ballots_cast']) if cdata['ballots_cast'] else "N/A"
                    print("  ADDED {}: reg={}, ballots={}".format(display, reg_s, bal_s))
                    filled += 1
            else:
                # Fill partial gaps
                existing = data[year][display]
                if existing['registered_voters'] is None and cdata['registered_voters'] is not None:
                    existing['registered_voters'] = cdata['registered_voters']
                    print("  FILLED {} reg: {:,}".format(display, cdata['registered_voters']))
                    filled += 1
                if existing['ballots_cast'] is None and cdata['ballots_cast'] is not None:
                    existing['ballots_cast'] = cdata['ballots_cast']
                    existing['early_voting'] = cdata.get('early_voting')
                    existing['election_day'] = cdata.get('election_day')
                    existing['provisional'] = cdata.get('provisional')
                    print("  FILLED {} ballots: {:,}".format(display, cdata['ballots_cast']))
                    filled += 1

        if filled == 0:
            print("  No gaps to fill")

    # Step 3: Write output
    rows = []
    for year in sorted(data.keys()):
        for county in sorted(data[year].keys()):
            d = data[year][county]
            reg = d['registered_voters']
            bal = d['ballots_cast']
            turnout = ''
            if reg and bal and reg > 0:
                turnout = round(bal / reg * 100, 1)

            rows.append({
                'year': year,
                'election_date': ELECTION_DATES[year],
                'county': county,
                'num_precincts': d['num_precincts'],
                'registered_voters': reg if reg is not None else '',
                'ballots_cast': bal if bal is not None else '',
                'turnout_pct': turnout,
                'early_voting': d['early_voting'] if d['early_voting'] else '',
                'election_day': d['election_day'] if d['election_day'] else '',
                'provisional': d['provisional'] if d['provisional'] else '',
            })

    cols = ['year', 'election_date', 'county', 'num_precincts',
            'registered_voters', 'ballots_cast', 'turnout_pct',
            'early_voting', 'election_day', 'provisional']

    with open('az_county_election_turnout.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)

    print("\n\n=== FINAL SUMMARY ===")
    print("Total rows: {}".format(len(rows)))
    for year in sorted(data.keys()):
        counties = data[year]
        with_reg = sum(1 for c in counties.values() if c['registered_voters'] is not None)
        with_bal = sum(1 for c in counties.values() if c['ballots_cast'] is not None)
        total_reg = sum(c['registered_voters'] for c in counties.values() if c['registered_voters'])
        total_bal = sum(c['ballots_cast'] for c in counties.values() if c['ballots_cast'])
        print("{}: {}/15 counties | reg={:,} | ballots={:,}".format(
            year, len(counties), total_reg, total_bal))


if __name__ == '__main__':
    main()
