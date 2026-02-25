#!/usr/bin/env python3
"""Generate figures for the appendix PDF."""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
})

OUTDIR = 'appendix_figures'
m = pd.read_csv('az_school_board_master.csv')
s = pd.read_csv('az_district_year_summary.csv')

# ── Figure 1: Districts and candidates per year ──
fig, ax1 = plt.subplots(figsize=(6, 3.5))
years = sorted(s['year'].unique().astype(int))
districts_per_year = [len(s[s['year']==y]) for y in years]
candidates_per_year = [len(m[(m['year']==y) & (m['ctds_id'].notna())]) for y in years]

x = np.arange(len(years))
w = 0.35
bars1 = ax1.bar(x - w/2, districts_per_year, w, label='District-year races', color='#2c7fb8')
bars2 = ax1.bar(x + w/2, candidates_per_year, w, label='Candidates', color='#7fcdbb')
ax1.set_xlabel('Election Year')
ax1.set_ylabel('Count')
ax1.set_title('Districts and Candidates by Election Cycle')
ax1.set_xticks(x)
ax1.set_xticklabels(years)
ax1.legend(loc='upper left')
for bar in bars1:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 8,
             str(int(bar.get_height())), ha='center', va='bottom', fontsize=8)
for bar in bars2:
    ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 8,
             str(int(bar.get_height())), ha='center', va='bottom', fontsize=8)
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig1_districts_candidates_by_year.pdf')
plt.close()
print('Figure 1 done')

# ── Figure 2: Contested vs uncontested by year ──
fig, ax = plt.subplots(figsize=(6, 3.5))
contested_by_year = []
uncontested_by_year = []
unknown_by_year = []
for y in years:
    sub = s[s['year']==y]
    c = sub['contested'].sum()
    u = (sub['contested'] == 0).sum()
    unk = sub['contested'].isna().sum()
    contested_by_year.append(c)
    uncontested_by_year.append(u)
    unknown_by_year.append(unk)

ax.bar(x, contested_by_year, w*2, label='Contested', color='#d95f02')
ax.bar(x, uncontested_by_year, w*2, bottom=contested_by_year, label='Uncontested', color='#7570b3')
bottoms = [c + u for c, u in zip(contested_by_year, uncontested_by_year)]
ax.bar(x, unknown_by_year, w*2, bottom=bottoms, label='Unknown', color='#cccccc')
ax.set_xlabel('Election Year')
ax.set_ylabel('Number of Races')
ax.set_title('Race Competitiveness by Election Cycle')
ax.set_xticks(x)
ax.set_xticklabels(years)
ax.legend(loc='upper left')
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig2_contested_by_year.pdf')
plt.close()
print('Figure 2 done')

# ── Figure 3: Distribution of candidates per seat ──
fig, ax = plt.subplots(figsize=(6, 3.5))
cps = s['candidates_per_seat'].dropna()
bins = np.arange(0.5, cps.max() + 1.5, 1)
ax.hist(cps, bins=bins, color='#2c7fb8', edgecolor='white', linewidth=0.5)
ax.set_xlabel('Candidates per Seat')
ax.set_ylabel('Number of District-Year Races')
ax.set_title('Distribution of Candidates per Seat')
ax.axvline(cps.median(), color='#d95f02', linestyle='--', linewidth=1.5, label=f'Median = {cps.median():.1f}')
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig3_candidates_per_seat.pdf')
plt.close()
print('Figure 3 done')

# ── Figure 4: Winner margin distribution ──
fig, ax = plt.subplots(figsize=(6, 3.5))
margins = s['winner_margin_pct'].dropna()
margins_clipped = margins[margins <= 50]
ax.hist(margins_clipped, bins=25, color='#2c7fb8', edgecolor='white', linewidth=0.5)
ax.set_xlabel('Winner Margin (%)')
ax.set_ylabel('Number of Races')
ax.set_title('Distribution of Winner Margin (Contested Races)')
ax.axvline(margins_clipped.median(), color='#d95f02', linestyle='--', linewidth=1.5,
           label=f'Median = {margins_clipped.median():.1f}%')
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig4_winner_margin.pdf')
plt.close()
print('Figure 4 done')

# ── Figure 5: Enrollment distribution ──
fig, ax = plt.subplots(figsize=(6, 3.5))
enr = s['total_enrollment'].dropna()
enr_pos = enr[enr > 0]
ax.hist(enr_pos, bins=40, color='#2c7fb8', edgecolor='white', linewidth=0.5)
ax.set_xlabel('Total Enrollment')
ax.set_ylabel('Number of District-Year Observations')
ax.set_title('Distribution of District Enrollment')
ax.axvline(enr_pos.median(), color='#d95f02', linestyle='--', linewidth=1.5,
           label=f'Median = {enr_pos.median():,.0f}')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
ax.legend()
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig5_enrollment_dist.pdf')
plt.close()
print('Figure 5 done')

# ── Figure 6: Letter grade distribution ──
fig, ax = plt.subplots(figsize=(5, 3.5))
grade_order = ['A', 'B', 'C', 'D', 'F']
grade_counts = s['lea_letter_grade'].dropna().value_counts()
grade_vals = [grade_counts.get(g, 0) for g in grade_order]
colors = ['#1a9850', '#91cf60', '#fee08b', '#fc8d59', '#d73027']
bars = ax.bar(grade_order, grade_vals, color=colors, edgecolor='white', linewidth=0.5)
for bar, val in zip(bars, grade_vals):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
            str(val), ha='center', va='bottom', fontsize=9)
ax.set_xlabel('ADE Letter Grade')
ax.set_ylabel('Number of District-Year Observations')
ax.set_title('Distribution of ADE A-F Letter Grades')
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig6_letter_grades.pdf')
plt.close()
print('Figure 6 done')

# ── Figure 7: Votes by enrollment (scatter) ──
fig, ax = plt.subplots(figsize=(6, 4))
both = s.dropna(subset=['total_enrollment', 'total_votes_cast'])
both = both[both['total_enrollment'] > 0]
ax.scatter(both['total_enrollment'], both['total_votes_cast'],
           alpha=0.4, s=20, color='#2c7fb8', edgecolors='none')
ax.set_xlabel('Total Enrollment')
ax.set_ylabel('Total Votes Cast')
ax.set_title('Voter Turnout vs. District Enrollment')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'{x:,.0f}'))
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig7_votes_vs_enrollment.pdf')
plt.close()
print('Figure 7 done')

# ── Figure 8: County breakdown ──
fig, ax = plt.subplots(figsize=(6, 4.5))
county_counts = m[m['ctds_id'].notna()].groupby('county').size().sort_values(ascending=True)
county_counts.plot.barh(ax=ax, color='#2c7fb8')
ax.set_xlabel('Number of Candidate Records')
ax.set_ylabel('')
ax.set_title('Candidate Records by County')
for i, (val, name) in enumerate(zip(county_counts.values, county_counts.index)):
    ax.text(val + 5, i, str(val), va='center', fontsize=8)
plt.tight_layout()
plt.savefig(f'{OUTDIR}/fig8_county_breakdown.pdf')
plt.close()
print('Figure 8 done')

print('\nAll figures generated.')
