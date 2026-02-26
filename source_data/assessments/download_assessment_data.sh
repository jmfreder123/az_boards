#!/bin/bash
#
# Arizona Department of Education (ADE) Assessment Data Download Script
#
# This script downloads state assessment results Excel files from the
# ADE Accountability & Research division. These files contain district-level
# (LEA) ELA and Math proficiency data.
#
# The files are organized with multiple tabs:
#   - By School
#   - By LEA (District/Charter Holder)
#   - By County
#   - By State Level
#
# Assessment History:
#   2015-2019: AzMERIT (Arizona's Measurement of Educational Readiness to Inform Teaching)
#   2019-2020: AzM2 (renamed AzMERIT)
#   2021-2022+: AASA (Arizona's Academic Standards Assessment) - same standards/cut scores
#   Note: 2019-2020 had no statewide testing due to COVID-19
#
# Sources:
#   - State Assessment Results: https://www.azed.gov/accountability-research/state-assessment-results
#   - Accountability & Research Data: https://www.azed.gov/accountability-research/data
#   - Public Data Sets: https://www.azed.gov/data/public-data-sets
#   - AZ Report Cards State Reports: https://azreportcards.azed.gov/state-reports
#
# Usage: Run this script from the directory where you want the files saved.
#        ./download_assessment_data.sh

set -e

OUTPUT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Downloading ADE assessment data files to: $OUTPUT_DIR"
echo ""

# User-Agent header to avoid being blocked
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

download_file() {
    local url="$1"
    local output_name="$2"
    local description="$3"

    echo "Downloading: $description"
    echo "  URL: $url"
    echo "  Output: $output_name"

    if curl -L -f -o "$OUTPUT_DIR/$output_name" \
        -H "User-Agent: $UA" \
        -H "Accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel,*/*" \
        "$url" 2>/dev/null; then
        local size=$(stat -f%z "$OUTPUT_DIR/$output_name" 2>/dev/null || stat -c%s "$OUTPUT_DIR/$output_name" 2>/dev/null)
        echo "  SUCCESS - Size: $size bytes"
    else
        echo "  FAILED - trying wget..."
        if wget -q -O "$OUTPUT_DIR/$output_name" \
            --header="User-Agent: $UA" \
            "$url" 2>/dev/null; then
            local size=$(stat -f%z "$OUTPUT_DIR/$output_name" 2>/dev/null || stat -c%s "$OUTPUT_DIR/$output_name" 2>/dev/null)
            echo "  SUCCESS (wget) - Size: $size bytes"
        else
            echo "  FAILED - Could not download. Try manually from the URL above."
            rm -f "$OUTPUT_DIR/$output_name"
        fi
    fi
    echo ""
}

echo "============================================================"
echo "SECTION 1: Known Direct File URLs (confirmed via search)"
echo "============================================================"
echo ""

# 2016 AzMERIT - confirmed URL from Google index
download_file \
    "https://www.azed.gov/sites/default/files/2017/06/2016-azmerit.xlsx?id=593f049b3217e112704d002d" \
    "2016-azmerit.xlsx" \
    "2016 AzMERIT Assessment Results (confirmed URL)"

# Spring 2024 AASA District SDF Layout - confirmed URL from Google index
download_file \
    "https://www.azed.gov/sites/default/files/2024/03/AZ%20SP24%20AASA%20Gr3-8%20District%20SDF%20Layout.xlsx" \
    "AZ_SP24_AASA_Gr3-8_District_SDF_Layout.xlsx" \
    "Spring 2024 AASA Gr3-8 District Student Data File Layout (confirmed URL)"

# AZELLA 2023 - confirmed URL from Google index
download_file \
    "https://azed.gov/sites/default/files/2024/01/Azella_2023_publish[1].xlsx" \
    "Azella_2023_publish.xlsx" \
    "AZELLA 2023 Results (confirmed URL)"

# Civics Assessment Results 2024 from AZ Report Cards
download_file \
    "https://azreportcards.azed.gov/Files/Civics_Assessment_Results_2024.xlsx" \
    "Civics_Assessment_Results_2024.xlsx" \
    "Civics Assessment Results 2024 (confirmed URL)"

echo "============================================================"
echo "SECTION 2: Guessed URLs - AzMERIT era (2015-2019)"
echo "  Based on pattern: sites/default/files/YYYY/MM/YYYY-azmerit.xlsx"
echo "  These are on the state-assessment-results page"
echo "============================================================"
echo ""

# Try the AzMERIT naming pattern for 2015
download_file \
    "https://www.azed.gov/sites/default/files/2016/09/2015-azmerit.xlsx" \
    "2015-azmerit.xlsx" \
    "2015 AzMERIT Results (guessed URL pattern 1)"

download_file \
    "https://www.azed.gov/sites/default/files/2016/06/2015-azmerit.xlsx" \
    "2015-azmerit-alt.xlsx" \
    "2015 AzMERIT Results (guessed URL pattern 2)"

# 2017 AzMERIT
download_file \
    "https://www.azed.gov/sites/default/files/2018/06/2017-azmerit.xlsx" \
    "2017-azmerit.xlsx" \
    "2017 AzMERIT Results (guessed URL pattern 1)"

download_file \
    "https://www.azed.gov/sites/default/files/2017/09/2017-azmerit.xlsx" \
    "2017-azmerit-alt.xlsx" \
    "2017 AzMERIT Results (guessed URL pattern 2)"

# 2018 AzMERIT
download_file \
    "https://www.azed.gov/sites/default/files/2019/06/2018-azmerit.xlsx" \
    "2018-azmerit.xlsx" \
    "2018 AzMERIT Results (guessed URL pattern 1)"

download_file \
    "https://www.azed.gov/sites/default/files/2018/09/2018-azmerit.xlsx" \
    "2018-azmerit-alt.xlsx" \
    "2018 AzMERIT Results (guessed URL pattern 2)"

# 2019 AzMERIT / AzM2
download_file \
    "https://www.azed.gov/sites/default/files/2020/01/2019-azmerit.xlsx" \
    "2019-azmerit.xlsx" \
    "2019 AzMERIT Results (guessed URL pattern 1)"

download_file \
    "https://www.azed.gov/sites/default/files/2019/09/2019-azmerit.xlsx" \
    "2019-azmerit-alt.xlsx" \
    "2019 AzMERIT Results (guessed URL pattern 2)"

echo "============================================================"
echo "SECTION 3: Guessed URLs - AASA era (2021-2024)"
echo "  These are listed on the accountability-research/data page"
echo "  Naming convention unknown - trying several patterns"
echo "============================================================"
echo ""

# Assessments 2021 (Updated 2/1/2023 per search results)
for pattern in \
    "https://www.azed.gov/sites/default/files/2023/02/Assessments%202021.xlsx" \
    "https://www.azed.gov/sites/default/files/2022/09/Assessments%202021.xlsx" \
    "https://www.azed.gov/sites/default/files/2021/09/Assessments%202021.xlsx" \
    "https://www.azed.gov/sites/default/files/2021/10/Assessments%202021.xlsx" \
    "https://www.azed.gov/sites/default/files/2022/10/Assessments%202021.xlsx" \
    "https://www.azed.gov/sites/default/files/2023/02/Assessments_2021.xlsx" \
    "https://www.azed.gov/sites/default/files/2021/09/2021-aasa.xlsx" \
    "https://www.azed.gov/sites/default/files/2021/10/2021-aasa.xlsx" \
    "https://www.azed.gov/sites/default/files/2022/09/2021-assessments.xlsx"; do
    filename=$(echo "$pattern" | sed 's/.*\///' | sed 's/%20/_/g')
    download_file "$pattern" "2021_attempt_${filename}" "Assessments 2021 (trying pattern)"
done

# Assessments 2022 (Updated 10/16/2023 per search results)
for pattern in \
    "https://www.azed.gov/sites/default/files/2023/10/Assessments%202022.xlsx" \
    "https://www.azed.gov/sites/default/files/2022/09/Assessments%202022.xlsx" \
    "https://www.azed.gov/sites/default/files/2022/10/Assessments%202022.xlsx" \
    "https://www.azed.gov/sites/default/files/2023/10/Assessments_2022.xlsx" \
    "https://www.azed.gov/sites/default/files/2022/09/2022-aasa.xlsx" \
    "https://www.azed.gov/sites/default/files/2022/10/2022-assessments.xlsx"; do
    filename=$(echo "$pattern" | sed 's/.*\///' | sed 's/%20/_/g')
    download_file "$pattern" "2022_attempt_${filename}" "Assessments 2022 (trying pattern)"
done

# Assessments 2023 (Updated 10/06/2023 per search results)
for pattern in \
    "https://www.azed.gov/sites/default/files/2023/10/Assessments%202023.xlsx" \
    "https://www.azed.gov/sites/default/files/2023/09/Assessments%202023.xlsx" \
    "https://www.azed.gov/sites/default/files/2023/10/Assessments_2023.xlsx" \
    "https://www.azed.gov/sites/default/files/2023/09/2023-aasa.xlsx" \
    "https://www.azed.gov/sites/default/files/2023/10/2023-assessments.xlsx"; do
    filename=$(echo "$pattern" | sed 's/.*\///' | sed 's/%20/_/g')
    download_file "$pattern" "2023_attempt_${filename}" "Assessments 2023 (trying pattern)"
done

# Assessments 2024 (Updated 9/23/2024 per search results)
for pattern in \
    "https://www.azed.gov/sites/default/files/2024/09/Assessments%202024.xlsx" \
    "https://www.azed.gov/sites/default/files/2024/09/Assessments_2024.xlsx" \
    "https://www.azed.gov/sites/default/files/2024/09/2024-aasa.xlsx" \
    "https://www.azed.gov/sites/default/files/2024/09/2024-assessments.xlsx" \
    "https://www.azed.gov/sites/default/files/2024/10/Assessments%202024.xlsx"; do
    filename=$(echo "$pattern" | sed 's/.*\///' | sed 's/%20/_/g')
    download_file "$pattern" "2024_attempt_${filename}" "Assessments 2024 (trying pattern)"
done

# Assessments 2025 (Updated 10/10/25 per search results)
for pattern in \
    "https://www.azed.gov/sites/default/files/2025/10/Assessments%202025.xlsx" \
    "https://www.azed.gov/sites/default/files/2025/10/Assessments_2025.xlsx" \
    "https://www.azed.gov/sites/default/files/2025/10/2025-aasa.xlsx"; do
    filename=$(echo "$pattern" | sed 's/.*\///' | sed 's/%20/_/g')
    download_file "$pattern" "2025_attempt_${filename}" "Assessments 2025 (trying pattern)"
done

echo "============================================================"
echo "SECTION 4: AZ Report Cards - Guessed file patterns"
echo "============================================================"
echo ""

for year in 2024 2023 2022 2021 2020 2019 2018 2017 2016 2015; do
    for pattern in \
        "https://azreportcards.azed.gov/Files/Assessment_Results_${year}.xlsx" \
        "https://azreportcards.azed.gov/Files/AASA_Results_${year}.xlsx" \
        "https://azreportcards.azed.gov/Files/AzMERIT_Results_${year}.xlsx" \
        "https://azreportcards.azed.gov/Files/Statewide_Assessment_Results_${year}.xlsx"; do
        filename=$(echo "$pattern" | sed 's/.*\///')
        download_file "$pattern" "$filename" "AZ Report Cards - $filename"
    done
done

echo "============================================================"
echo "Download attempts complete!"
echo "============================================================"
echo ""
echo "Successfully downloaded files:"
ls -la "$OUTPUT_DIR"/*.xlsx 2>/dev/null || echo "  No files downloaded."
echo ""
echo "If downloads failed, visit these pages in a browser to find the correct links:"
echo "  1. https://www.azed.gov/accountability-research/data"
echo "     (Assessments 2021-2025 xlsx files)"
echo "  2. https://www.azed.gov/accountability-research/state-assessment-results"
echo "     (AzMERIT 2015-2019 xlsx files)"
echo "  3. https://azreportcards.azed.gov/state-reports"
echo "     (Assessment results by school/LEA/state)"
echo "  4. https://www.azed.gov/data/public-data-sets"
echo "     (Master list of all public data)"
echo ""
echo "For the AASA District Data Files (student-level, requires ADEConnect):"
echo "  - https://www.azed.gov/assessment/aasa-district-data-file-spring-2024"
echo "  - https://www.azed.gov/assessment/aasa-district-data-file-spring-2023"
