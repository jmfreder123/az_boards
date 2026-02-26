#!/usr/bin/env python3
"""
Arizona Department of Education (ADE) Assessment Data Downloader

Downloads state assessment results Excel files from ADE.
These files contain district-level (LEA) ELA and Math proficiency data
with tabs for: School, LEA, County, and State level breakdowns.

Assessment History:
  2015-2019: AzMERIT
  2019-2020: AzM2 (renamed)
  2020-2021: No statewide testing (COVID-19)
  2021-2022+: AASA (same standards/cut scores)

Data Sources:
  - https://www.azed.gov/accountability-research/data
  - https://www.azed.gov/accountability-research/state-assessment-results
  - https://azreportcards.azed.gov/state-reports

Usage:
  python3 download_assessment_data.py
"""

import os
import sys
import urllib.request
import urllib.error
import ssl

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*',
}

# Confirmed URLs (found via Google indexing)
CONFIRMED_URLS = [
    {
        'url': 'https://www.azed.gov/sites/default/files/2017/06/2016-azmerit.xlsx',
        'filename': '2016-azmerit.xlsx',
        'description': '2016 AzMERIT Assessment Results (Fall 2015 + Spring 2016)',
    },
    {
        'url': 'https://www.azed.gov/sites/default/files/2024/03/AZ%20SP24%20AASA%20Gr3-8%20District%20SDF%20Layout.xlsx',
        'filename': 'AZ_SP24_AASA_Gr3-8_District_SDF_Layout.xlsx',
        'description': 'Spring 2024 AASA District Student Data File Layout',
    },
    {
        'url': 'https://azed.gov/sites/default/files/2024/01/Azella_2023_publish%5B1%5D.xlsx',
        'filename': 'Azella_2023_publish.xlsx',
        'description': 'AZELLA 2023 English Learner Assessment Results',
    },
    {
        'url': 'https://azreportcards.azed.gov/Files/Civics_Assessment_Results_2024.xlsx',
        'filename': 'Civics_Assessment_Results_2024.xlsx',
        'description': 'Civics Assessment Results 2024 (from AZ Report Cards)',
    },
]

# Guessed URLs based on known patterns
# The accountability-research/data page lists:
#   "Assessments 2025 (Updated 10/10/25)"
#   "Assessments 2024 (Updated 9/23/2024)"
#   "Assessments 2023 (Updated 10/06/2023)"
#   "Assessments 2022 (Updated 10/16/2023)"
#   "Assessments 2021 (Updated 2/1/2023)"
# The state-assessment-results page lists AzMERIT files for 2015-2019.

GUESSED_URLS = []

# AzMERIT era files (2015-2019) - based on confirmed 2016-azmerit.xlsx pattern
azmerit_patterns = [
    # 2015
    ('2016/09', '2015-azmerit.xlsx', '2015 AzMERIT Results'),
    ('2016/06', '2015-azmerit.xlsx', '2015 AzMERIT Results'),
    ('2015/09', '2015-azmerit.xlsx', '2015 AzMERIT Results'),
    ('2016/03', '2015-azmerit.xlsx', '2015 AzMERIT Results'),
    # 2017
    ('2018/06', '2017-azmerit.xlsx', '2017 AzMERIT Results'),
    ('2017/09', '2017-azmerit.xlsx', '2017 AzMERIT Results'),
    ('2017/10', '2017-azmerit.xlsx', '2017 AzMERIT Results'),
    ('2018/01', '2017-azmerit.xlsx', '2017 AzMERIT Results'),
    # 2018
    ('2019/06', '2018-azmerit.xlsx', '2018 AzMERIT Results'),
    ('2018/09', '2018-azmerit.xlsx', '2018 AzMERIT Results'),
    ('2018/10', '2018-azmerit.xlsx', '2018 AzMERIT Results'),
    ('2019/01', '2018-azmerit.xlsx', '2018 AzMERIT Results'),
    # 2019
    ('2020/01', '2019-azmerit.xlsx', '2019 AzMERIT/AzM2 Results'),
    ('2019/09', '2019-azmerit.xlsx', '2019 AzMERIT/AzM2 Results'),
    ('2019/10', '2019-azmerit.xlsx', '2019 AzMERIT/AzM2 Results'),
    ('2020/06', '2019-azmerit.xlsx', '2019 AzMERIT/AzM2 Results'),
]

for date_path, filename, desc in azmerit_patterns:
    GUESSED_URLS.append({
        'url': f'https://www.azed.gov/sites/default/files/{date_path}/{filename}',
        'filename': filename,
        'description': desc,
    })

# Also try with "AzMERIT" capitalization variants and "MSAA" combined files
for year in range(2015, 2020):
    upload_year = year + 1
    for month in ['06', '09', '10', '01']:
        yr = upload_year if month in ['06', '09', '10'] else upload_year
        for name_pattern in [
            f'{year}-AzMERIT.xlsx',
            f'AzMERIT%20{year}.xlsx',
            f'AzMERIT_{year}.xlsx',
            f'AzMERIT-MSAA-ACT-SAT-{year}.xlsx',
            f'{year}%20AzMERIT.xlsx',
        ]:
            GUESSED_URLS.append({
                'url': f'https://www.azed.gov/sites/default/files/{yr}/{month}/{name_pattern}',
                'filename': f'{year}-azmerit-{month}.xlsx',
                'description': f'{year} AzMERIT Results (pattern: {name_pattern})',
            })

# AASA era files (2021-2025) - from accountability-research/data page
# Known update dates help narrow down the upload path
aasa_file_info = [
    (2021, '2023/02', 'Updated 2/1/2023'),
    (2021, '2022/09', ''),
    (2021, '2021/09', ''),
    (2021, '2021/10', ''),
    (2022, '2023/10', 'Updated 10/16/2023'),
    (2022, '2022/09', ''),
    (2022, '2022/10', ''),
    (2023, '2023/10', 'Updated 10/06/2023'),
    (2023, '2023/09', ''),
    (2024, '2024/09', 'Updated 9/23/2024'),
    (2024, '2024/10', ''),
    (2025, '2025/10', 'Updated 10/10/25'),
    (2025, '2025/09', ''),
]

for year, date_path, note in aasa_file_info:
    for name_pattern in [
        f'Assessments%20{year}.xlsx',
        f'Assessments_{year}.xlsx',
        f'Assessments{year}.xlsx',
        f'{year}-assessments.xlsx',
        f'{year}-aasa.xlsx',
        f'AASA_{year}.xlsx',
        f'AASA%20{year}.xlsx',
        f'Assessment%20Results%20{year}.xlsx',
        f'State%20Assessment%20{year}.xlsx',
    ]:
        GUESSED_URLS.append({
            'url': f'https://www.azed.gov/sites/default/files/{date_path}/{name_pattern}',
            'filename': f'{year}-assessments.xlsx',
            'description': f'Assessments {year} {note}'.strip(),
        })

# AZ Report Cards patterns
for year in range(2015, 2026):
    for name_pattern in [
        f'Assessment_Results_{year}.xlsx',
        f'AASA_Results_{year}.xlsx',
        f'AzMERIT_Results_{year}.xlsx',
        f'Statewide_Assessment_Results_{year}.xlsx',
        f'ELA_Assessment_Results_{year}.xlsx',
        f'Math_Assessment_Results_{year}.xlsx',
    ]:
        GUESSED_URLS.append({
            'url': f'https://azreportcards.azed.gov/Files/{name_pattern}',
            'filename': name_pattern,
            'description': f'AZ Report Cards - {name_pattern}',
        })


def download_file(url, filename, description):
    """Attempt to download a file. Returns True on success."""
    filepath = os.path.join(OUTPUT_DIR, filename)

    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        print(f"  SKIP (already exists): {filename}")
        return True

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        # Create SSL context that doesn't verify (some gov sites have cert issues)
        ctx = ssl.create_default_context()

        response = urllib.request.urlopen(req, timeout=30, context=ctx)

        content_type = response.headers.get('Content-Type', '')

        # Check if we got an actual file (not an HTML error page)
        if 'text/html' in content_type:
            # Read a small portion to check
            data = response.read(500)
            if b'<html' in data.lower() or b'<!doctype' in data.lower():
                return False
            # If it doesn't look like HTML, save it
            remaining = response.read()
            with open(filepath, 'wb') as f:
                f.write(data)
                f.write(remaining)
        else:
            with open(filepath, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)

        size = os.path.getsize(filepath)
        if size < 1000:
            os.remove(filepath)
            return False

        print(f"  SUCCESS: {filename} ({size:,} bytes)")
        return True

    except (urllib.error.HTTPError, urllib.error.URLError, Exception):
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


def main():
    print(f"Arizona Department of Education - Assessment Data Downloader")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"=" * 70)

    successful = []
    failed_confirmed = []

    # First try confirmed URLs
    print(f"\n--- Confirmed URLs (found via Google indexing) ---\n")
    for item in CONFIRMED_URLS:
        print(f"Trying: {item['description']}")
        print(f"  URL: {item['url']}")
        if download_file(item['url'], item['filename'], item['description']):
            successful.append(item)
        else:
            failed_confirmed.append(item)
            print(f"  FAILED")

    # Then try guessed URLs (only for years we haven't already downloaded)
    downloaded_years = set()
    for item in successful:
        for year in range(2015, 2026):
            if str(year) in item['filename']:
                downloaded_years.add(year)

    print(f"\n--- Trying guessed URL patterns ---\n")
    tried_files = set()
    for item in GUESSED_URLS:
        # Skip if we already have this year's data
        year_match = None
        for year in range(2015, 2026):
            if str(year) in item['filename']:
                year_match = year
                break

        if year_match and year_match in downloaded_years:
            continue

        # Skip if we already tried this filename
        if item['filename'] in tried_files:
            # But still try the URL since filename may be reused for different URL patterns
            pass

        result = download_file(item['url'], item['filename'], item['description'])
        if result:
            successful.append(item)
            if year_match:
                downloaded_years.add(year_match)
            print(f"  Found: {item['description']}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"DOWNLOAD SUMMARY")
    print(f"{'=' * 70}")

    if successful:
        print(f"\nSuccessfully downloaded {len(successful)} file(s):")
        for item in successful:
            filepath = os.path.join(OUTPUT_DIR, item['filename'])
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  {item['filename']} ({size:,} bytes) - {item['description']}")
    else:
        print(f"\nNo files were downloaded.")

    # Years we still need
    all_years = set(range(2015, 2025))
    missing_years = all_years - downloaded_years
    if missing_years:
        print(f"\nMissing years: {sorted(missing_years)}")
        print(f"\nTo manually download, visit these pages in a web browser:")
        print(f"  1. https://www.azed.gov/accountability-research/data")
        print(f"     -> 'Assessments 2021' through 'Assessments 2025' links")
        print(f"  2. https://www.azed.gov/accountability-research/state-assessment-results")
        print(f"     -> AzMERIT 2015-2019 links")
        print(f"  3. https://azreportcards.azed.gov/state-reports")
        print(f"     -> State-level assessment results")
        print(f"  4. https://www.azed.gov/data/public-data-sets")
        print(f"     -> Master list of all public datasets")

    print(f"\nNote: If all downloads fail, the azed.gov site may be blocking")
    print(f"automated requests. Please visit the URLs above in a web browser")
    print(f"and download the files manually.")


if __name__ == '__main__':
    main()
