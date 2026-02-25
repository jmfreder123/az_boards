# Arizona School Board Elections & Accountability Data

This repository links Arizona school board election results (2014-2024) with district-level accountability metrics from the Arizona Department of Education (ADE), including A-F letter grades, dropout rates, enrollment, graduation rates, and superintendent characteristics.

## Files

### Analysis-Ready Files

| File | Rows | Unit of Analysis | Description |
|------|------|------------------|-------------|
| `az_school_board_master.csv` | 2,523 | Candidate | Every candidate in every school board election, with accountability and superintendent data broadcast-joined by district-year |
| `az_district_year_summary.csv` | 299 | District-Year | One row per district per election year, with derived analytical variables for competitiveness, voter engagement, and accountability |

### Source Files (`source_data/`)

| Path | Description |
|------|-------------|
| `source_data/elections/arizona_school_board_elections_summary.numbers` | Original Apple Numbers workbook (election results) |
| `source_data/elections/arizona_school_board_enhanced 3.numbers` | Enhanced Apple Numbers workbook |
| `source_data/ccd/ccd_lea_029_2425_w_1a_073025.csv` | NCES Common Core of Data, Arizona LEAs, 2024-2025 — used as the CTDS-to-NCES crosswalk |
| `source_data/ccd/ccd_lea_029_2425_w_1a_073025.sas7bdat` | Same CCD data in SAS format |
| `source_data/ccd/ccd_lea_029_2425_w_1a_073025 (1).zip` | Compressed CCD archive |
| `source_data/superintendent/School Board Data_2025-2026 (1).xlsx` | Hand-collected superintendent data (48 of ~208 districts filled so far) |

## Data Sources

- **Election results**: Arizona county election offices (2014-2024 general elections, some primaries)
- **A-F letter grades**: ADE A-F Accountability files (FY13-14, FY17-19, FY22-25). No grades published for FY15-16 or FY20-21 (COVID moratorium).
- **Dropout rates**: ADE Dropout Rate reports (FY13-25), filtered to Subgroup = "All"
- **Enrollment**: ADE October 1 Enrollment counts (FY14-26)
- **Graduation rates**: ADE 4-Year Cohort Graduation Rates (Cohort 2013-2025), filtered to Subgroup = "All"
- **Superintendent data**: Hand-collected from district websites, press releases, and LinkedIn (2025-2026 snapshot, in progress)
- **District identifiers**: NCES CCD 2024-2025 (CTDS Entity ID and NCES LEAID crosswalk)

## Key Identifiers

| ID | Description | Example |
|----|-------------|---------|
| `ctds_id` | ADE County-Type-District-School Entity ID | `4289` |
| `nces_leaid` | NCES national LEA identifier | `408580` |

The join key between election data and ADE accountability data is `ctds_id` + `year`.

## Coverage Notes

- **138 of 223 open regular school districts** (62%) in Arizona appear in the election data, based on cross-referencing with the NCES CCD 2024-2025 LEA file
- Not all districts appear in every cycle; 87 districts appear in 2+ cycles
- The summary file filters to **clean governing board races only** (excludes bonds, budget overrides, county superintendent races, and rows without a `ctds_id`)
- **A-F grades** have structural gaps in 2016 and 2020 (ADE did not publish grades those years)
- **Graduation rates** are only available for districts with high schools (~50% of districts)
- **Superintendent data** currently covers 48 districts; historical data back to 2013 is in progress

## District Coverage Detail

Arizona has 223 open regular public school districts (CCD LEA Type 1) plus 10 accommodation/regional/special-services districts and 14 specialized vocational-technical districts. The election dataset covers **138 regular districts**. The 85 districts absent from the election data tend to be smaller rural districts, though several mid-size districts (e.g., Casa Grande Elementary, Prescott, J O Combs, Chinle, Snowflake) are also missing.

### Districts Included in Election Data (138)

| CTDS ID | District Name |
|---------|---------------|
| 4289 | Agua Fria Union High School District |
| 4409 | Ajo Unified District |
| 4280 | Alhambra Elementary District |
| 4161 | Alpine Elementary District |
| 4418 | Altar Valley Elementary District |
| 4406 | Amphitheater Unified District |
| 4178 | Apache Elementary District |
| 4443 | Apache Junction Unified District |
| 4274 | Arlington Elementary District |
| 4272 | Avondale Elementary District |
| 4412 | Baboquivari Unified School District #40 |
| 4468 | Bagdad Unified District |
| 4268 | Balsz Elementary District |
| 79226 | Benson Unified School District |
| 4169 | Bisbee Unified District |
| 4397 | Blue Ridge Unified School District No. 32 |
| 4224 | Bonita Elementary District |
| 4269 | Buckeye Elementary District |
| 4284 | Buckeye Union High School District |
| 4282 | Cartwright Elementary District |
| 4453 | Casa Grande Union High School District |
| 4410 | Catalina Foothills Unified District |
| 4244 | Cave Creek Unified District |
| 4242 | Chandler Unified District #80 |
| 4370 | Colorado City Unified District |
| 4160 | Concho Elementary District |
| 4416 | Continental Elementary District |
| 4442 | Coolidge Unified District |
| 4501 | Crane Elementary District |
| 4263 | Creighton Elementary District |
| 4246 | Deer Valley Unified District |
| 4174 | Douglas Unified District |
| 4243 | Dysart Unified District |
| 4448 | Eloy Elementary District |
| 4192 | Flagstaff Unified District |
| 4437 | Florence Unified School District |
| 4405 | Flowing Wells Unified District |
| 4221 | Fort Thomas Unified District |
| 4247 | Fountain Hills Unified District |
| 4273 | Fowler Elementary District |
| 4505 | Gadsden Elementary District |
| 4157 | Ganado Unified School District |
| 4238 | Gila Bend Unified District |
| 4239 | Gilbert Unified District |
| 4271 | Glendale Elementary District |
| 4285 | Glendale Union High School District |
| 4208 | Globe Unified District |
| 4371 | Hackberry School District |
| 4212 | Hayden-Winkelman Unified District |
| 4392 | Heber-Overgaard Unified District |
| 4248 | Higley Unified School District |
| 4469 | Humboldt Unified District |
| 4259 | Isaac Elementary District |
| 4396 | Kayenta Unified School District #27 |
| 79598 | Kingman Unified School District |
| 4267 | Kyrene Elementary District |
| 4368 | Lake Havasu Unified District |
| 4276 | Laveen Elementary District |
| 4266 | Liberty Elementary District |
| 4281 | Litchfield Elementary District |
| 4278 | Littleton Elementary District |
| 4270 | Madison Elementary District |
| 4404 | Marana Unified District |
| 4441 | Maricopa Unified School District |
| 4163 | Mcnary Elementary District |
| 4235 | Mesa Unified District |
| 4379 | Mohave Valley Elementary District |
| 4251 | Morristown Elementary District |
| 4265 | Murphy Elementary District |
| 4252 | Nadaburg Unified School District |
| 4457 | Nogales Unified District |
| 4262 | Osborn Elementary District |
| 4196 | Page Unified School District #8 |
| 4275 | Palo Verde Elementary District |
| 4255 | Paloma School District |
| 4241 | Paradise Valley Unified District |
| 4209 | Payson Unified District |
| 4186 | Pearce Elementary District |
| 4283 | Pendergast Elementary District |
| 4237 | Peoria Unified School District |
| 4256 | Phoenix Elementary District |
| 4286 | Phoenix Union High School District |
| 4220 | Pima Unified District |
| 4214 | Pine Strawberry Elementary District |
| 4390 | Pinon Unified District |
| 4245 | Queen Creek Unified District |
| 4159 | Red Mesa Unified District |
| 4257 | Riverside Elementary District |
| 4279 | Roosevelt Elementary District |
| 4155 | Round Valley Unified District |
| 4449 | Sacaton Elementary District |
| 4254 | Saddle Mountain Unified School District |
| 4218 | Safford Unified District |
| 4411 | Sahuarita Unified District |
| 4210 | San Carlos Unified District |
| 4172 | San Simon Unified District |
| 4156 | Sanders Unified District |
| 4458 | Santa Cruz Valley Unified District |
| 4454 | Santa Cruz Valley Union High School District |
| 4240 | Scottsdale Unified District |
| 4467 | Sedona-Oak Creek JUSD #9 |
| 4472 | Seligman Unified District |
| 4250 | Sentinel Elementary District |
| 4393 | Show Low Unified District |
| 4175 | Sierra Vista Unified District |
| 4500 | Somerton Elementary District |
| 4461 | Sonoita Elementary District |
| 4173 | St David Unified District |
| 4153 | St Johns Unified District |
| 4407 | Sunnyside Unified District |
| 4440 | Superior Unified School District |
| 4408 | Tanque Verde Unified District |
| 4258 | Tempe School District |
| 4287 | Tempe Union High School District |
| 4219 | Thatcher Unified District |
| 4264 | Tolleson Elementary District |
| 4288 | Tolleson Union High School District |
| 4450 | Toltec School District |
| 4168 | Tombstone Unified District |
| 4215 | Tonto Basin Elementary District |
| 4376 | Topock Elementary District |
| 4197 | Tuba City Unified School District #15 |
| 4403 | Tucson Unified District |
| 4277 | Union Elementary District |
| 4413 | Vail Unified District |
| 4380 | Valentine Elementary District |
| 4162 | Vernon Elementary District |
| 4260 | Washington Elementary School District |
| 4394 | Whiteriver Unified District |
| 4236 | Wickenburg Unified District |
| 4170 | Willcox Unified District |
| 4261 | Wilson Elementary District |
| 4154 | Window Rock Unified District |
| 4387 | Winslow Unified District |
| 4485 | Yarnell Elementary District |
| 4213 | Young Elementary District |
| 4499 | Yuma Elementary District |
| 4507 | Yuma Union High School District |

### Regular Districts Not in Election Data (75)

These districts had no school board election results captured in the original source data across any of the 6 election cycles (2014-2024). Many are small rural districts with one or two schools, though some mid-size districts are also absent.

**Recoverable from OpenElections:** An audit of the [OpenElections Arizona data](https://github.com/openelections/openelections-data-az) county-level precinct files (2014-2024) found governing board races for at least **27** of these 75 districts. The largest coverage gap is **Yavapai County**, where Prescott, Chino Valley, Camp Verde, Mayer, Congress, Canon, Kirkland, and Clarkdale-Jerome all have board races in OpenElections but were not in the original source workbook. Other recoverable districts include Chinle (Apache), Williams/Grand Canyon/Fredonia-Moccasin/Ash Fork (Coconino), Miami (Gila), Blue Elementary (Greenlee), Quartzsite/Bouse/Salome/Bicentennial (La Paz), Colorado River Union HS (Mohave), Snowflake (Navajo), Mohawk Valley (Yuma), Solomon (Graham), and Antelope Union HS (Yuma). Several additional districts may be recoverable from generic "Board Member" entries in 2020 and 2024 county files that require precinct-level matching to identify the district.

| CTDS ID | District Name | Schools |
|---------|---------------|---------|
| 4249 | Aguila Elementary District | 2 |
| 4506 | Antelope Union High School District | 2 |
| 4187 | Ash Creek Elementary District | 1 |
| 4471 | Ash Fork Joint Unified District | 3 |
| 4481 | Beaver Creek Elementary District | 1 |
| 4515 | Bicentennial Union High School District | 1 |
| 4231 | Blue Elementary District | 1 |
| 4513 | Bouse Elementary District | 1 |
| 4171 | Bowie Unified District | 2 |
| 4378 | Bullhead City School District | 6 |
| 4470 | Camp Verde Unified District | 5 |
| 4484 | Canon Elementary District | 1 |
| 4446 | Casa Grande Elementary District | 14 |
| 4395 | Cedar Unified District | 2 |
| 4198 | Chevelon Butte School District | 0 |
| 4158 | Chinle Unified District | 8 |
| 4474 | Chino Valley Unified District | 4 |
| 4486 | Clarkdale-Jerome Elementary District | 1 |
| 4177 | Cochise Elementary District | 1 |
| 4381 | Colorado River Union High School District | 3 |
| 4479 | Congress Elementary District | 1 |
| 4487 | Cottonwood-Oak Creek Elementary District | 6 |
| 4483 | Crown King Elementary District | 1 |
| 4179 | Double Adobe Elementary District | 1 |
| 4228 | Duncan Unified District | 2 |
| 4232 | Eagle Elementary District | 0 |
| 4185 | Elfrida Elementary District | 1 |
| 4415 | Empire Elementary District | 0 |
| 4195 | Fredonia-Moccasin Unified District | 2 |
| 4194 | Grand Canyon Unified District | 2 |
| 4482 | Hillside Elementary District | 1 |
| 4389 | Holbrook Unified District | 5 |
| 4502 | Hyder Elementary District | 1 |
| 4445 | J O Combs Unified School District | 10 |
| 4388 | Joseph City Unified District | 3 |
| 4480 | Kirkland Elementary District | 1 |
| 4223 | Klondyke Elementary District | 0 |
| 4374 | Littlefield Unified District | 2 |
| 4199 | Maine Consolidated School District | 1 |
| 4439 | Mammoth-San Manuel Unified District | 3 |
| 4473 | Mayer Unified School District | 2 |
| 4181 | McNeal Elementary District | 1 |
| 4211 | Miami Unified District | 5 |
| 4488 | Mingus Union High School District | 2 |
| 4253 | Mobile Elementary District | 1 |
| 4503 | Mohawk Valley Elementary District | 1 |
| 4230 | Morenci Unified District | 3 |
| 4176 | Naco Elementary District | 1 |
| 4444 | Oracle Elementary District | 1 |
| 4373 | Owens School District No.6 | 1 |
| 4180 | Palominas Elementary School District 49 | 3 |
| 4510 | Parker Unified School District | 6 |
| 4460 | Patagonia Elementary District | 1 |
| 4462 | Patagonia Union High School District | 1 |
| 4369 | Peach Springs Unified District | 3 |
| 4452 | Picacho Elementary District | 1 |
| 4188 | Pomerene Elementary District | 1 |
| 4466 | Prescott Unified District | 9 |
| 4511 | Quartzsite Elementary District | 2 |
| 4438 | Ray Unified District | 2 |
| 4447 | Red Rock Elementary District | 1 |
| 4417 | Redington Elementary District | 0 |
| 4514 | Salome Consolidated Elementary District | 1 |
| 4414 | San Fernando Elementary District | 1 |
| 4459 | Santa Cruz Elementary District | 1 |
| 4478 | Skull Valley Elementary District | 1 |
| 4391 | Snowflake Unified District | 7 |
| 4222 | Solomon Elementary District | 1 |
| 4451 | Stanfield Elementary District | 1 |
| 4190 | Valley Union High School District | 1 |
| 4504 | Wellton Elementary District | 1 |
| 4512 | Wenden Elementary District | 1 |
| 4193 | Williams Unified District | 2 |
| 4475 | Williamson Valley Elementary School District | 0 |
| 4377 | Yucca Elementary District | 1 |

### Accommodation, Regional, and Special-Services Districts Not in Election Data (10)

These districts operate differently from regular school districts and typically do not hold standard governing board elections.

| CTDS ID | District Name |
|---------|---------------|
| 1001687 | Cochise County Accommodation School District |
| 10386 | Coconino County Accommodation School District |
| 4167 | Fort Huachuca Accommodation District |
| 4217 | Graham County Special Services |
| 87600 | Gila County Regional School District |
| 4234 | Maricopa County Regional School District |
| 4435 | Mary C O'Brien Accommodation District |
| 4386 | Navajo County Accommodation District #99 |
| 4401 | Pima County Accommodation School District |
| 79379 | Yavapai Accommodation School District |

See `DATA_DICTIONARY.md` for full column definitions.
