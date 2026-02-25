#!/usr/bin/env python3
"""
OpenElections Gap-Fill Pipeline for Arizona School Board Elections (v2)

Downloads county-level precinct data from OpenElections, extracts school board
races, aggregates to district-level candidate totals, matches to CTDS IDs,
and outputs new rows ONLY for missing district-year slots.

Safety: Never overwrites existing data. Only fills gaps.
"""

import csv
import io
import re
import sys
import json
import urllib.request
from collections import defaultdict

MASTER_CSV = "az_school_board_master.csv"
CCD_CSV = "source_data/ccd/ccd_lea_029_2425_w_1a_073025.csv"
BASE_URL = "https://raw.githubusercontent.com/openelections/openelections-data-az/master"

ELECTION_DATES = {
    2014: "2014-11-04", 2016: "2016-11-08", 2018: "2018-11-06",
    2020: "2020-11-03", 2022: "2022-11-08", 2024: "2024-11-05",
}
DATE_PREFIXES = {
    2014: "20141104", 2016: "20161108", 2018: "20181106",
    2020: "20201103", 2022: "20221108", 2024: "20241105",
}
COUNTY_DISPLAY = {
    "apache": "Apache", "cochise": "Cochise", "coconino": "Coconino",
    "gila": "Gila", "graham": "Graham", "greenlee": "Greenlee",
    "la_paz": "La Paz", "maricopa": "Maricopa", "mohave": "Mohave",
    "navajo": "Navajo", "pima": "Pima", "pinal": "Pinal",
    "santa_cruz": "Santa Cruz", "yavapai": "Yavapai", "yuma": "Yuma",
}

def get_county_url(year, county_lower):
    prefix = DATE_PREFIXES[year]
    c = county_lower
    if year == 2024:
        if c == "la_paz": c = "la%20paz"
        elif c == "santa_cruz": c = "santa%20cruz"
        return f"{BASE_URL}/2024/General/{prefix}__az__general__{c}__precinct.csv"
    elif year == 2014:
        return f"{BASE_URL}/2014/{prefix}__az__general__{c}__precinct.csv"
    else:
        return f"{BASE_URL}/{year}/counties/{prefix}__az__general__{c}__precinct.csv"


# ---------------------------------------------------------------------------
# HARD-CODED CTDS MATCHING FOR KNOWN PROBLEM CASES
# These are name fragments -> CTDS that the fuzzy matcher struggles with.
# ---------------------------------------------------------------------------
MANUAL_CTDS_MAP = {
    # Apache County
    "ST. JOHNS UNIFIED": "4153", "ST JOHNS UNIFIED": "4153", "ST. JOHN USD": "4153",
    "WINDOW ROCK UNIFIED": "4154", "WINDOW ROCK USD": "4154",
    "ROUND VALLEY UNIFIED": "4155", "ROUND VALLEY USD": "4155",
    "SANDERS UNIFIED": "4156", "SANDERS USD": "4156",
    "GANADO UNIFIED": "4157", "GANADO USD": "4157",
    "RED MESA UNIFIED": "4159", "RED MESA USD": "4159",
    "CONCHO ELEMENTARY": "4160", "CONCHO ESD": "4160",
    "ALPINE ELEMENTARY": "4161",
    "VERNON ELEMENTARY": "4162", "VERNON ESD": "4162",
    "MCNARY ELEMENTARY": "4163", "MC NARY ELEMENTARY": "4163", "MCNARY ESD": "4163",
    "CHINLE UNIFIED": "4158",
    # Cochise
    "TOMBSTONE UNIFIED": "4168", "USD 68": "4168",
    "BISBEE UNIFIED": "4169", "BISBEE USD": "4169",
    "WILLCOX UNIFIED": "4170", "WILLCOX USD": "4170",
    "SAN SIMON UNIFIED": "4172", "SAN SIMON USD": "4172",
    "ST. DAVID UNIFIED": "4173", "ST DAVID UNIFIED": "4173", "ST. DAVID USD": "4173",
    "DOUGLAS UNIFIED": "4174", "DOUGLAS USD": "4174",
    "SIERRA VISTA UNIFIED": "4175", "SIERRA VISTA USD": "4175",
    "APACHE ELEMENTARY": "4178",
    "PEARCE ELEMENTARY": "4186",
    "BENSON UNIFIED": "79226", "BENSON USD": "79226",
    # Coconino
    "FLAGSTAFF UNIFIED": "4192", "FLAGSTAFF USD": "4192",
    "PAGE UNIFIED": "4196", "PAGE USD": "4196",
    "TUBA CITY UNIFIED": "4197", "TUBA CITY USD": "4197",
    "SEDONA-OAK CREEK": "4467", "SEDONA OAK CREEK": "4467",
    "WILLIAMS UNIFIED": "4193",
    "GRAND CANYON UNIFIED": "4194",
    "FREDONIA-MOCCASIN UNIFIED": "4195",
    # Gila
    "GLOBE UNIFIED": "4208",
    "PAYSON UNIFIED": "4209",
    "SAN CARLOS UNIFIED": "4210",
    "HAYDEN-WINKELMAN UNIFIED": "4212", "HAYDEN WINKELMAN UNIFIED": "4212",
    "YOUNG ELEMENTARY": "4213", "YOUNG PUBLIC SCHOOL": "4213",
    "PINE-STRAWBERRY": "4214", "PINE STRAWBERRY": "4214",
    "TONTO BASIN": "4215",
    "WHITERIVER UNIFIED": "4394", "WHITERIVER USD": "4394",
    "MIAMI UNIFIED": "4211",
    "SAN CARLOS SCHOOL": "4210",
    # Graham
    "SAFFORD UNIFIED": "4218", "SAFFORD USD": "4218",
    "THATCHER UNIFIED": "4219", "THATCHER USD": "4219",
    "PIMA UNIFIED": "4220", "PIMA USD": "4220",
    "FORT THOMAS UNIFIED": "4221", "FT. THOMAS USD": "4221", "FT THOMAS USD": "4221",
    "BONITA ELEMENTARY": "4224", "BONITA ESD": "4224", "BONITA USD": "4224",
    "SOLOMON ELEMENTARY": "4222", "SOLOMON ESD": "4222",
    "PIMA USD": "4220",
    # Maricopa - all the ESD/USD/UHSD patterns
    "AGUA FRIA UNION": "4289", "AGUA FRIA UHSD": "4289",
    "ALHAMBRA ESD": "4280", "ALHAMBRA ELEMENTARY": "4280",
    "ARLINGTON ESD": "4274", "ARLINGTON ELEMENTARY": "4274",
    "AVONDALE ESD": "4272", "AVONDALE ELEMENTARY": "4272",
    "BALSZ ESD": "4268", "BALSZ ELEMENTARY": "4268",
    "BUCKEYE ESD": "4269", "BUCKEYE ELEMENTARY": "4269",
    "BUCKEYE UHSD": "4284", "BUCKEYE UNION": "4284",
    "CARTWRIGHT ESD": "4282", "CARTWRIGHT ELEMENTARY": "4282",
    "CAVE CREEK USD": "4244", "CAVE CREEK UNIFIED": "4244",
    "CHANDLER USD": "4242", "CHANDLER UNIFIED": "4242",
    "CREIGHTON ESD": "4263", "CREIGHTON ELEMENTARY": "4263",
    "DEER VALLEY USD": "4246", "DEER VALLEY UNIFIED": "4246",
    "DYSART USD": "4243", "DYSART UNIFIED": "4243",
    "FOUNTAIN HILLS USD": "4247", "FOUNTAIN HILLS UNIFIED": "4247",
    "FOWLER ESD": "4273", "FOWLER ELEMENTARY": "4273",
    "GILA BEND USD": "4238", "GILA BEND UNIFIED": "4238",
    "GILBERT USD": "4239", "GILBERT UNIFIED": "4239",
    "GLENDALE ESD": "4271", "GLENDALE ELEMENTARY": "4271",
    "GLENDALE UHSD": "4285", "GLENDALE UNION HIGH": "4285",
    "HIGLEY USD": "4248", "HIGLEY UNIFIED": "4248",
    "ISAAC ESD": "4259", "ISAAC ELEMENTARY": "4259",
    "KYRENE ESD": "4267", "KYRENE ELEMENTARY": "4267",
    "LAVEEN ESD": "4276", "LAVEEN ELEMENTARY": "4276",
    "LIBERTY ESD": "4266", "LIBERTY ELEMENTARY": "4266",
    "LITCHFIELD ESD": "4281", "LITCHFIELD ELEMENTARY": "4281",
    "LITTLETON ESD": "4278", "LITTLETON ELEMENTARY": "4278",
    "MADISON ESD": "4270", "MADISON ELEMENTARY": "4270",
    "MESA USD": "4235", "MESA UNIFIED": "4235",
    "MORRISTOWN ESD": "4251",
    "MURPHY ESD": "4265", "MURPHY ELEMENTARY": "4265",
    "NADABURG ESD": "4252", "NADABURG USD": "4252",
    "OSBORN ESD": "4262", "OSBORN ELEMENTARY": "4262",
    "PALO VERDE ESD": "4275",
    "PALOMA ESD": "4255",
    "PARADISE VALLEY USD": "4241", "PARADISE VALLEY UNIFIED": "4241",
    "PARADISE VLLY USD": "4241",
    "PENDERGAST ESD": "4283", "PENDERGAST ELEMENTARY": "4283",
    "PEORIA USD": "4237", "PEORIA UNIFIED": "4237",
    "PHOENIX ESD": "4256", "PHOENIX ELEMENTARY": "4256",
    "PHOENIX UHSD": "4286", "PHOENIX UNION HIGH": "4286", "PHOENIX UNION": "4286",
    "QUEEN CREEK USD": "4245", "QUEEN CREEK ESD": "4245", "QUEEN CREEK UNIFIED": "4245",
    "RIVERSIDE ESD": "4257", "RIVERSIDE ELEMENTARY": "4257",
    "ROOSEVELT ESD": "4279", "ROOSEVELT ELEMENTARY": "4279",
    "SADDLE MOUNTAIN USD": "4254", "SADDLE MTN USD": "4254",
    "SCOTTSDALE USD": "4240", "SCOTTSDALE UNIFIED": "4240",
    "SENTINEL ESD": "4250",
    "TEMPE ESD": "4258", "TEMPE SCHOOL": "4258",
    "TEMPE UHSD": "4287", "TEMPE UNION HIGH": "4287", "TEMPE UNION": "4287",
    "TOLLESON ESD": "4264", "TOLLESON ELEMENTARY": "4264",
    "TOLLESON UHSD": "4288", "TOLLESON UNION HIGH": "4288",
    "UNION ESD": "4277", "UNION ELEMENTARY": "4277",
    "WASHINGTON ESD": "4260", "WASHINGTON ELEMENTARY": "4260",
    "WICKENBURG USD": "4236", "WICKENBURG UNIFIED": "4236",
    "WILSON ESD": "4261", "WILSON ELEMENTARY": "4261",
    "MARICOPA UNIFIED": "4441",
    "J O COMBS UNIFIED": "4445",
    # Mohave
    "LAKE HAVASU UNIFIED": "4368", "LAKE HAVASU USD": "4368",
    "COLORADO CITY UNIFIED": "4370", "COLORADO CITY USD": "4370",
    "HACKBERRY ELEMENTARY": "4371", "HACKBERRY ESD": "4371",
    "TOPOCK ELEMENTARY": "4376", "TOPOCK ESD": "4376",
    "MOHAVE VALLEY ELEMENTARY": "4379",
    "VALENTINE ELEMENTARY": "4380", "VALENTINE ESD": "4380",
    "KINGMAN UNIFIED": "79598", "KINGMAN USD": "79598", "KUSD": "79598",
    "BULLHEAD CITY": "4378",
    "COLORADO RIVER UNION HIGH": "4381", "COLORADO RIVER UHSD": "4381",
    "CO RIVER UNION HS": "4381", "CRUHSD": "4381",
    "CCUSD": "4370",  # Colorado City USD
    "LHUSD": "4368",  # Lake Havasu USD
    "FMUSD": "4379",  # Mohave Valley (Fort Mohave?)
    "KINGMAN US DIST": "79598",
    "LAKE HAVASU US DIST": "4368",
    # Navajo
    "BLUE RIDGE UNIFIED": "4397", "BLUE RIDGE USD": "4397",
    "HEBER-OVERGAARD UNIFIED": "4392", "HEBER/OVERGAARD USD": "4392",
    "HEBER OVERGAARD": "4392",
    "KAYENTA UNIFIED": "4396", "KAYENTA USD": "4396",
    "PINON UNIFIED": "4390", "PINON USD": "4390",
    "SHOW LOW UNIFIED": "4393", "SHOW LOW USD": "4393",
    "WINSLOW UNIFIED": "4387", "WINSLOW USD": "4387",
    "SNOWFLAKE UNIFIED": "4391", "SNOWFLAKE USD": "4391",
    "HOLBROOK UNIFIED": "4389",
    "JOSEPH CITY UNIFIED": "4388",
    # Short forms used in Navajo 2020
    "BOARD MEMBER KAYENTA": "4396",
    "BOARD MEMBER PINON": "4390",
    "BOARD MEMBER SHOW LOW": "4393",
    "BOARD MEMBER WINSLOW": "4387",
    "BOARD MEMBER GLOBE": "4208",
    # Pima
    "TUCSON UNIFIED": "4403", "TUCSON USD": "4403",
    "MARANA UNIFIED": "4404", "MARANA USD": "4404",
    "FLOWING WELLS UNIFIED": "4405",
    "AMPHITHEATER UNIFIED": "4406",
    "SUNNYSIDE UNIFIED": "4407",
    "TANQUE VERDE UNIFIED": "4408",
    "AJO UNIFIED": "4409",
    "CATALINA FOOTHILLS UNIFIED": "4410", "CATALINA FOOTHILLS": "4410",
    "SAHUARITA UNIFIED": "4411",
    "BABOQUIVARI": "4412", "BABOQUIVARI SCHOOL": "4412",
    "VAIL UNIFIED": "4413",
    "CONTINENTAL ELEMENTARY": "4416",
    "ALTAR VALLEY": "4418", "ALTAR VALLEY ESD": "4418",
    # Pinal
    "APACHE JUNCTION UNIFIED": "4443",
    "CASA GRANDE UNION HIGH": "4453", "CASA GRANDE UHSD": "4453",
    "COOLIDGE UNIFIED": "4442",
    "ELOY ELEMENTARY": "4448",
    "FLORENCE UNIFIED": "4437",
    "SACATON ELEMENTARY": "4449",
    "SUPERIOR UNIFIED": "4440",
    "TOLTEC ELEMENTARY": "4450", "TOLTEC SCHOOL": "4450",
    "SANTA CRUZ VALLEY UNION HIGH": "4454",
    "ORACLE ELEMENTARY": "4444",
    "RAY UNIFIED": "4438",
    "STANFIELD ELEMENTARY": "4451",
    "PICACHO ELEMENTARY": "4452",
    # Santa Cruz
    "NOGALES UNIFIED": "4457", "NUSD": "4457", "BOARD MEMBER USD 1": "4457",
    "SANTA CRUZ VALLEY UNIFIED": "4458", "SCV": "4458",
    "SONOITA ELEMENTARY": "4461", "SCE": "4461",
    "SANTA CRUZ ELEMENTARY": "4459",
    # Yavapai
    "BAGDAD UNIFIED": "4468", "BAGDAD USD": "4468",
    "HUMBOLDT UNIFIED": "4469", "HUMBOLDT USD": "4469",
    "SELIGMAN UNIFIED": "4472", "SELIGMAN USD": "4472",
    "YARNELL ELEMENTARY": "4485", "YARNELL ESD": "4485",
    "PRESCOTT UNIFIED": "4466", "PRESCOTT USD": "4466",
    "CHINO VALLEY UNIFIED": "4474", "CHINO VALLEY USD": "4474",
    "CAMP VERDE UNIFIED": "4470", "CAMP VERDE USD": "4470",
    "MAYER UNIFIED": "4473", "MAYER USD": "4473",
    "CONGRESS ELEMENTARY": "4479", "CONGRESS ESD": "4479",
    "CANON ELEMENTARY": "4484", "CANON ESD": "4484",
    "KIRKLAND ELEMENTARY": "4480", "KIRKLAND ESD": "4480",
    "CLARKDALE-JEROME ELEMENTARY": "4486", "CLARKDALE-JEROME ESD": "4486",
    "COTTONWOOD-OAK CREEK ELEMENTARY": "4487", "COTTONWOOD-OAK CREEK ESD": "4487",
    "MINGUS UNION HIGH": "4488",
    "SEDONA-OAK CREEK JUSD": "4467", "SEDONA-OAK CREEK JOINT USD": "4467",
    # Yuma
    "YUMA ELEMENTARY": "4499",
    "SOMERTON ELEMENTARY": "4500",
    "CRANE ELEMENTARY": "4501",
    "GADSDEN ELEMENTARY": "4505", "GADSDEN ESD": "4505",
    "YUMA UNION HIGH": "4507", "YUMA UHSD": "4507",
    "MOHAWK VALLEY ELEMENTARY": "4503",
    "ANTELOPE UNION HIGH": "4506", "ANTELOPE UNION HSD": "4506",
}


def normalize_race_name(text):
    """Normalize a race/office name for matching."""
    t = text.upper().strip()
    # Remove common prefixes
    for prefix in [
        'GOVERNING BOARD - ', 'GOVERNING BOARD, ', 'GOVERNING BOARD ',
        'GOVERNING BOARD 2-YEAR TERM - ', 'GOVERNING BOARD 2-YEAR TERM ',
        'BOARD MEMBER - ', 'BOARD MEMBER ', 'BD MEMBER ', 'BRD MEMBER ',
        'SCHOOL BOARD MEMBER ', 'FLORENCE BOARD MEMBER ',
    ]:
        if t.startswith(prefix):
            t = t[len(prefix):]

    # Remove common suffixes
    for suffix in [
        ' BOARD MEMBER', ' - BOARD MEMBER',
        '-GBM-4YR', '-GBM-2YR', '-GBM',
        ' GOV BRD - 4YR', ' GOV BRD - 2YR', ' GOV BRD',
        ': 4-YEAR TERM', ': 2-YEAR TERM', ': 4YR', ': 2YR',
    ]:
        if t.endswith(suffix):
            t = t[:-len(suffix)]

    # Remove "(ELECT N)", "(SELECT N)", "(vote for N)" patterns
    t = re.sub(r'\s*\(ELECT\s+\d+\)', '', t)
    t = re.sub(r'\s*\(SELECT\s+\d+\)', '', t)
    t = re.sub(r'\s*\(VOTE\s+(?:FOR\s+)?\d+\)', '', t)
    t = re.sub(r'\s*VACANCY$', '', t)

    # Clean up school district naming variations
    t = re.sub(r'\bSCH\.?\s*DIST\.?\s*', 'SCHOOL DISTRICT ', t)
    t = re.sub(r'\bS\.D\.\s*', 'SCHOOL DISTRICT ', t)
    t = re.sub(r'\bELEM\.?\s*', 'ELEMENTARY ', t)
    t = re.sub(r'\bSCHOOL DISTRICT\b', '', t)  # Remove after expanding for cleaner matching

    # Remove "No." and "#" district numbers
    t = re.sub(r'\s*#\s*0*(\d+)', r' #\1', t)  # Normalize #043 -> #43
    t = re.sub(r'\s*NO\.?\s*0*(\d+)', r' #\1', t)  # No. 43 -> #43
    t = re.sub(r'\s*DIST\.?\s*0*(\d+)', r' #\1', t)  # Dist. 43 -> #43

    # Remove trailing numbers that look like district numbers
    t = re.sub(r'\s+#?\d+\s*$', '', t)

    t = re.sub(r'\s+', ' ', t).strip()
    return t


def match_to_ctds(office, district, county):
    """
    Match an OpenElections race to a CTDS ID.
    Returns CTDS string or None.
    """
    # Build the text to match from
    texts_to_try = []

    if district and district.strip():
        texts_to_try.append(district.strip())
    texts_to_try.append(office.strip())
    if district and district.strip():
        texts_to_try.append(office.strip() + " - " + district.strip())

    for text in texts_to_try:
        upper = text.upper().strip()

        # Try exact match against manual map
        for key, ctds in MANUAL_CTDS_MAP.items():
            if key in upper:
                return ctds

        # Normalize and try again
        norm = normalize_race_name(text)
        for key, ctds in MANUAL_CTDS_MAP.items():
            if key in norm:
                return ctds

    # Also try combining office+district with pipe delimiter removed
    combined = (office + " " + district).upper().replace("|", " ").strip()
    combined = re.sub(r'\s+', ' ', combined)
    for key, ctds in MANUAL_CTDS_MAP.items():
        if key in combined:
            return ctds

    # Try the full office string after normalizing
    norm_combined = normalize_race_name(combined)
    for key, ctds in MANUAL_CTDS_MAP.items():
        if key in norm_combined:
            return ctds

    return None


def is_school_board_race(office, district=""):
    """Check if a race is a school board governing board member election."""
    combined = (office + " " + district).upper()

    # Exclude non-board-member entries (questions, bonds, overrides, etc.)
    if any(k in combined for k in [
        'QUESTION', 'PROPOSITION', 'BOND', 'OVERRIDE', 'BUDGET',
        'SALE', 'LEASE', 'JTED', 'CAPITAL IMPROV', 'REORGANIZATION',
        'DISTRICT ADDITIONAL ASSISTANCE', 'MAIN. & OPERATIONS',
        'RECALL', 'REFERENDUM',
    ]):
        return False

    # School board patterns
    board_keywords = [
        'GOVERNING BOARD', 'GBM', 'GOV BRD', 'BOARD MEMBER',
        'BD MEMBER', 'BRD MEMBER', 'SCHOOL BOARD',
    ]
    district_keywords = ['ESD', 'USD', 'UHSD', 'SCHOOL DIST', 'S.D.', 'UNIFIED']

    if any(p in combined for p in board_keywords):
        # Exclude non-school boards (fire, water, sanitary, hospital, college, etc.)
        if any(k in combined for k in [
            'FIRE', 'WATER', 'SANITARY', 'HOSPITAL', 'COMMUNITY COLLEGE',
            'CAWCD', 'DWID', 'SANITATION', 'DOMESTIC WATER',
            'PIMA COMMUNITY', 'PINAL COUNTY COMM', 'COCHISE COLLEGE',
            'NORTHLAND PIONEER', 'EAST VALLEY INSTITUTE',
            'CENTRAL ARIZONA VALLEY INSTITUTE', 'MCCD',
            'ARIZONA CITY', 'POMERENE WATER', 'RIM TRAIL',
        ]):
            return False
        return True

    # Races named after the district (e.g., "CAMP VERDE USD #28")
    if any(k in combined for k in district_keywords):
        if any(k in combined for k in ['ELECT', 'SELECT', 'VOTE FOR', '4-YEAR', '2-YEAR', '4YR', '2YR']):
            return True
        # Also match standalone district names used as office names
        if match_to_ctds(office, district, '') is not None:
            return True

    # Handle pipe-delimited format: "School Board Member | KUSD #20"
    combined_pipe = (office + " " + district).upper().replace("|", " ")
    if any(k in combined_pipe for k in district_keywords):
        if match_to_ctds(office, district, '') is not None:
            return True

    return False


def is_metadata_row(candidate):
    """Check if this is a metadata/aggregate row to skip."""
    upper = candidate.upper().strip()
    skip_values = {
        'REGISTERED VOTERS', 'BALLOTS CAST', 'BALLOTS CAST BLANK',
        'TOTAL VOTES', 'UNDER VOTE', 'OVER VOTE', 'UNDERVOTE', 'OVERVOTE',
        'WRITE-IN TOTALS', 'WRITE-INS', 'WRITE IN', 'WRITE-IN',
        'NUMBER OF PRECINCTS', 'NUMBER OF PRECINCTS FOR RACE',
        'NUMBER OF PRECINCTS REPORTING', 'TIMES COUNTED',
        'NO OFFICIAL CANDIDATE',
    }
    if upper in skip_values:
        return True
    if upper.startswith('TOTAL') or upper.startswith('UNDER ') or upper.startswith('OVER '):
        return True
    if upper.startswith('WRITE-IN') or upper.startswith('WRITE IN'):
        return True
    if 'TURNOUT' in upper or 'REGISTERED' in upper:
        return True
    return False


def download_file(url):
    """Download a file, return text content or None on failure."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            text = raw.decode('utf-8', errors='replace')
            # Normalize line endings
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            return text
    except Exception as e:
        return None


def extract_records(csv_text, county_name, year, county_lower):
    """
    Universal extraction function that auto-detects the CSV format
    and extracts school board race records.
    Returns list of dicts with standardized fields.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    fields = reader.fieldnames
    if not fields:
        return []

    fields_lower = [f.lower() for f in fields]
    records = []

    # Detect format based on column names
    if 'contest_name' in fields_lower:
        # 2014 Maricopa format
        for row in reader:
            contest = row.get('contest_name', '')
            candidate = row.get('choice_name', '')
            votes = row.get('vote_total', '0')
            if not is_school_board_race(contest):
                continue
            if is_metadata_row(candidate):
                continue
            try:
                v = int(float(votes))
            except (ValueError, TypeError):
                v = 0
            if v <= 0:
                continue
            records.append({
                'county': county_name, 'office': contest, 'district': '',
                'candidate': candidate, 'party': '',
                'total_votes': v, 'early_voting': '', 'election_day': '', 'provisional': '',
            })

    elif 'contesttitle' in fields_lower:
        # 2014 Yavapai format
        for row in reader:
            contest = row.get('contesttitle', '')
            candidate = row.get('candidate name', '')
            votes = row.get('votes', '0')
            votetype = row.get('votetype', '')
            if not is_school_board_race(contest):
                continue
            if is_metadata_row(candidate):
                continue
            try:
                v = int(float(votes))
            except (ValueError, TypeError):
                v = 0
            if v <= 0:
                continue
            records.append({
                'county': county_name, 'office': contest, 'district': '',
                'candidate': candidate, 'party': row.get('party name', ''),
                'total_votes': v,
                'early_voting': v if votetype == 'C' else 0,  # C = cumulative/early
                'election_day': v if votetype in ('E', 'P') else 0,  # E=election day, P=polling
                'provisional': v if votetype == 'A' else 0,  # A = provisional/absentee
            })

    elif 'race' in fields_lower and 'race_id' in fields_lower:
        # 2014 standard format (Pima, Coconino, Gila, Apache, etc.)
        for row in reader:
            race = row.get('race', '')
            candidate = row.get('candidate', '')
            count = row.get('count', '0')
            cand_id = row.get('candidate_id', '')
            try:
                if int(cand_id) >= 999990:
                    continue
            except (ValueError, TypeError):
                pass
            if not is_school_board_race(race):
                continue
            if is_metadata_row(candidate):
                continue
            try:
                v = int(float(count))
            except (ValueError, TypeError):
                v = 0
            if v <= 0:
                continue
            records.append({
                'county': county_name, 'office': race, 'district': '',
                'candidate': candidate, 'party': '',
                'total_votes': v, 'early_voting': '', 'election_day': '', 'provisional': '',
            })

    elif 'contest_name' in [f.lower() for f in fields]:
        # 2014 Pinal format (contest_name, choice_name columns)
        cn_field = [f for f in fields if f.lower() == 'contest_name'][0]
        ch_field = [f for f in fields if f.lower() == 'choice_name'][0]
        vt_field = [f for f in fields if f.lower() == 'vote_total'][0]
        for row in reader:
            contest = row.get(cn_field, '')
            candidate = row.get(ch_field, '')
            votes = row.get(vt_field, '0')
            if not is_school_board_race(contest):
                continue
            if is_metadata_row(candidate):
                continue
            try:
                v = int(float(votes))
            except (ValueError, TypeError):
                v = 0
            if v <= 0:
                continue
            records.append({
                'county': county_name, 'office': contest, 'district': '',
                'candidate': candidate, 'party': row.get('party_name', ''),
                'total_votes': v,
                'early_voting': row.get('early_votes', ''),
                'election_day': row.get('polling_place_votes', ''),
                'provisional': row.get('provisional_votes', ''),
            })

    elif 'office' in fields_lower:
        # 2016-2024 standard format
        for row in reader:
            office = row.get('office', '')
            district = row.get('district', '')
            candidate = row.get('candidate', '')
            party = row.get('party', '')
            votes = row.get('votes', '0')
            if not is_school_board_race(office, district):
                continue
            if is_metadata_row(candidate):
                continue
            try:
                v = int(float(votes))
            except (ValueError, TypeError):
                v = 0
            if v <= 0:
                continue
            records.append({
                'county': county_name, 'office': office, 'district': district,
                'candidate': candidate, 'party': party,
                'total_votes': v,
                'early_voting': row.get('early_voting', ''),
                'election_day': row.get('election_day', ''),
                'provisional': row.get('provisional', ''),
            })

    else:
        print(f"  WARNING: Unknown CSV format. Columns: {fields}")
        return []

    return records


def aggregate_to_candidates(precinct_records):
    """Aggregate precinct records to candidate-level totals."""
    agg = defaultdict(lambda: {'total_votes': 0, 'early_voting': 0, 'election_day': 0, 'provisional': 0})

    for r in precinct_records:
        key = (r['county'], r['office'], r['district'], r['candidate'], r['party'])
        agg[key]['total_votes'] += r['total_votes']
        for field in ['early_voting', 'election_day', 'provisional']:
            try:
                val = int(float(r[field])) if r[field] else 0
                agg[key][field] += val
            except (ValueError, TypeError):
                pass

    results = []
    for (county, office, district, candidate, party), vals in sorted(agg.items()):
        results.append({
            'county': county, 'office': office, 'district': district,
            'candidate': candidate, 'party': party,
            'total_votes': vals['total_votes'],
            'early_voting': vals['early_voting'] if vals['early_voting'] > 0 else '',
            'election_day': vals['election_day'] if vals['election_day'] > 0 else '',
            'provisional': vals['provisional'] if vals['provisional'] > 0 else '',
        })
    return results


def main():
    print("=" * 70)
    print("OpenElections Gap-Fill Pipeline v2")
    print("=" * 70)

    # Load existing data
    print("\n[1] Loading existing data...")
    existing_rows = []
    existing_pairs = set()
    with open(MASTER_CSV) as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            existing_rows.append(r)
            if r['ctds_id']:
                ctds = str(int(float(r['ctds_id'])))
                year = str(int(float(r['year'])))
                existing_pairs.add((ctds, year))

    print(f"  Existing rows: {len(existing_rows)}, district-year pairs: {len(existing_pairs)}")

    # Build CCD lookup
    ccd_districts = {}
    with open(CCD_CSV) as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['FIPST'] == '04' and r['LEA_TYPE'] == '1':
                ctds = r['ST_LEAID'].replace('AZ-', '')
                ccd_districts[ctds] = {'lea_name': r['LEA_NAME'], 'leaid': r['LEAID']}

    # Build district info from existing master
    ctds_county = {}
    ctds_names = defaultdict(set)
    for r in existing_rows:
        if r['ctds_id'] and r['county']:
            ctds = str(int(float(r['ctds_id'])))
            ctds_county[ctds] = r['county']
            ctds_names[ctds].add(r['school_district'])

    # Find gaps
    print("\n[2] Computing gaps...")
    all_ctds = set(ctds_county.keys())
    gaps_by_county_year = defaultdict(set)
    for ctds in all_ctds:
        county = ctds_county.get(ctds)
        if not county:
            continue
        county_lower = county.lower().replace(' ', '_')
        for year in [2014, 2016, 2018, 2020, 2022, 2024]:
            if (ctds, str(year)) not in existing_pairs:
                gaps_by_county_year[(county_lower, year)].add(ctds)

    total_gaps = sum(len(v) for v in gaps_by_county_year.values())
    print(f"  Total gaps: {total_gaps} across {len(gaps_by_county_year)} county-year files")

    # Process each county-year
    print("\n[3] Downloading and processing...")
    new_rows = []
    filled_pairs = set()
    match_details = []  # For logging

    for (county_lower, year), needed_ctds in sorted(gaps_by_county_year.items()):
        county_display = COUNTY_DISPLAY.get(county_lower, county_lower.title())
        url = get_county_url(year, county_lower)

        print(f"\n  --- {county_display} {year} (need {len(needed_ctds)} districts) ---")

        csv_text = download_file(url)
        if not csv_text:
            print(f"  SKIP: Could not download")
            continue

        # Extract school board records
        precinct_records = extract_records(csv_text, county_display, year, county_lower)
        if not precinct_records:
            print(f"  No school board races found")
            continue

        print(f"  {len(precinct_records)} precinct records -> ", end="")

        # Aggregate to candidates
        candidates = aggregate_to_candidates(precinct_records)
        print(f"{len(candidates)} candidates")

        # Match to CTDS
        matched = defaultdict(list)
        unmatched = []

        for cand in candidates:
            ctds = match_to_ctds(cand['office'], cand['district'], county_display)

            if ctds and ctds in needed_ctds:
                matched[ctds].append(cand)
            elif ctds and (ctds, str(year)) in existing_pairs:
                pass  # Already have this district-year, skip
            elif ctds is None:
                unmatched.append(cand)

        if matched:
            print(f"  MATCHED {len(matched)} districts: {sorted(matched.keys())}")
            for ctds in sorted(matched.keys()):
                ccd_name = ccd_districts.get(ctds, {}).get('lea_name', '?')
                n_cands = len(matched[ctds])
                print(f"    {ctds} ({ccd_name}): {n_cands} candidates")

        if unmatched:
            unique_unmatched = set((u['office'], u['district']) for u in unmatched)
            print(f"  UNMATCHED {len(unique_unmatched)} races:")
            for off, dist in sorted(unique_unmatched):
                print(f"    ? {off}" + (f" | {dist}" if dist else ""))

        # Create master rows
        for ctds, cand_list in matched.items():
            if (ctds, str(year)) in existing_pairs:
                continue  # Safety check

            ccd_info = ccd_districts.get(ctds, {})
            leaid = ccd_info.get('leaid', '')
            lea_name = ccd_info.get('lea_name', '')

            # Use existing school_district name (longest version)
            if ctds_names.get(ctds):
                school_district = sorted(ctds_names[ctds], key=len)[-1]
            else:
                school_district = lea_name

            for cand in cand_list:
                row = {field: '' for field in fieldnames}
                row['year'] = f"{year}.0"
                row['election_date'] = ELECTION_DATES[year]
                row['election_type'] = 'general'
                row['county'] = county_display
                row['school_district'] = school_district
                row['ctds_id'] = f"{ctds}.0"
                row['nces_leaid'] = f"{leaid}.0" if leaid else ''
                row['ccd_lea_name'] = lea_name
                row['district'] = ''
                if cand['district']:
                    row['office'] = cand['office'] + " - " + cand['district']
                else:
                    row['office'] = cand['office']
                row['candidate'] = cand['candidate']
                row['party'] = cand['party'] if cand['party'] else ''
                row['total_votes'] = f"{cand['total_votes']}.0"
                row['early_voting'] = f"{cand['early_voting']}.0" if cand['early_voting'] else ''
                row['election_day'] = f"{cand['election_day']}.0" if cand['election_day'] else ''
                row['provisional'] = f"{cand['provisional']}.0" if cand['provisional'] else ''
                row['winner'] = ''
                row['num_precincts'] = ''
                new_rows.append(row)

            filled_pairs.add((ctds, str(year)))
            match_details.append({
                'ctds': ctds, 'year': year, 'county': county_display,
                'lea_name': lea_name, 'n_candidates': len(cand_list),
            })

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"  New candidate rows: {len(new_rows)}")
    print(f"  District-years filled: {len(filled_pairs)} / {total_gaps}")
    print(f"  Remaining gaps: {total_gaps - len(filled_pairs)}")

    year_counts = defaultdict(int)
    for ctds, year in filled_pairs:
        year_counts[year] += 1
    print("\n  By year:")
    for y in sorted(year_counts.keys()):
        print(f"    {y}: {year_counts[y]} districts filled")

    # Save staging file
    staging_file = "openelections_new_rows.csv"
    with open(staging_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(new_rows)
    print(f"\n  Saved to {staging_file}")

    # Save log
    with open("openelections_match_log.json", 'w') as f:
        json.dump(match_details, f, indent=2)

    return new_rows, filled_pairs, fieldnames


if __name__ == '__main__':
    main()
