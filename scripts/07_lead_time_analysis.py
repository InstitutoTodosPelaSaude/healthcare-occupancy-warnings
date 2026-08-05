# %%
"""Step 07: early warning performance and lead time (Figure 5, Tables S5-S6).

For each epidemic wave, locates the first occupancy alert (weekly z-score
above 0.65 on a 6-week rolling baseline) and the laboratory surge peak, then
measures the lead time between them. Evaluation is restricted to
pathogen-source combinations with significant Granger causality in that wave;
the significance flags are read from the step 05 output rather than
hard-coded.

Outputs
    results/lead_time/weekly_zscores.tsv     (source of Table S5)
    results/lead_time/lead_time_table.tsv    (source of Table S6)
    results/lead_time/plots/figure5.{png,svg}
"""

import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import units
from src.paths import CONSOLIDATED_DATA, GRANGER_DIR, LEAD_TIME_DIR, ensure_dir

ensure_dir(LEAD_TIME_DIR, LEAD_TIME_DIR / "plots")

# Rolling window (in epidemiological weeks) for the occupancy z-score baseline
OCC_WINDOW = 6
# Alert threshold, as in the volatility index
THRESHOLD = 0.65
# Centred smoothing applied before locating the laboratory peak
SMOOTH_WIN = 2
# Dengue in wave 1 peaks locally before the December surge, which belongs to
# wave 2; restrict the wave 1 search to the pre-surge peak
DENV_W1_CUT = '2023-11-01'

WAVES = units.LEAD_TIME_WAVES

# internal key: (column, display label, source type, dataset role, group, colour)
PATHOGENS = {
    'SC2 (%)':  ('radim_posrate_sc2',     'SC2 (%)',  'private', 'exploratory', 'SC2',  '#2ECC71'),
    'SC2 (#)':  ('sivep_cases_sc2',       'SC2 (#)',  'public',  'validation',  'SC2',  '#27AE60'),
    'Denv (%)': ('radim_posrate_denv',    'Denv (%)', 'private', 'exploratory', 'Denv', '#9B59B6'),
    'Denv (#)': ('infodengue_cases_denv', 'Denv (#)', 'public',  'validation',  'Denv', '#6C3483'),
    'RV (%)':   ('radim_posrate_vrisp',   'RV (%)',   'private', 'exploratory', 'RV',   '#555555'),
    'RV (#)':   ('sivep_vrisp_cases',     'RV (#)',   'public',  'validation',  'RV',   '#2d2d2d'),
}

WAVE_COLORS = {'Wave 1': '#2E86AB', 'Wave 2': '#F18F01', 'Wave 3': '#C73E1D'}
ALERT_COLOR = '#bc4749'


def smooth(arr, win):
    return pd.Series(arr).rolling(window=win, center=True, min_periods=1).mean().values


def normalise(arr):
    """Min-max rescale to 0-1, as used for the Figure 5 panels."""
    mn, mx = np.nanmin(arr), np.nanmax(arr)
    return (arr - mn) / (mx - mn) if mx > mn else np.zeros_like(arr.astype(float))


# %%
# ------------- Granger significance, derived from step 05 -------------
granger = pd.read_csv(GRANGER_DIR / "granger_results_by_wave.tsv", sep="\t")
significant = granger[granger['p_value'] < 0.05]

# A pathogen group counts as significant in a wave when at least one of its
# indicators reaches p < 0.05; both the (%) and (#) variants are then evaluated.
granger_sig = {}
for wave_index, wave_label in enumerate(WAVES, start=1):
    groups = {
        units.GRANGER_TARGET_TO_GROUP[target]
        for target in significant[significant['wave'] == f'wave{wave_index}']['target']
    }
    granger_sig[wave_label] = [
        key for key, meta in PATHOGENS.items() if meta[4] in groups
    ]
    print(f"{wave_label}: significant groups {sorted(groups)}")

# %%
# ------------------------- Occupancy alert signal -------------------------
df = pd.read_csv(CONSOLIDATED_DATA, sep='\t')
df['epidemiological_weeks'] = pd.to_datetime(df['epidemiological_weeks'])
df = df.sort_values('epidemiological_weeks').reset_index(drop=True)
df_occ = df.dropna(subset=['detecta_percentage_mean']).copy().reset_index(drop=True)

df_occ['occ_rolling_mean'] = df_occ['detecta_percentage_mean'].rolling(
    window=OCC_WINDOW, min_periods=3).mean()
df_occ['occ_rolling_std'] = df_occ['detecta_percentage_mean'].rolling(
    window=OCC_WINDOW, min_periods=3).std()
df_occ['z_occupancy'] = (
    (df_occ['detecta_percentage_mean'] - df_occ['occ_rolling_mean'])
    / df_occ['occ_rolling_std']
)
df_occ['alert_fired'] = (df_occ['z_occupancy'] > THRESHOLD).astype(int)

# %%
# ------------- Weekly z-scores for every series (Table S5) -------------
zscore_out = df_occ[['epidemiological_weeks', 'detecta_percentage_mean',
                     'occ_rolling_mean', 'occ_rolling_std',
                     'z_occupancy', 'alert_fired']].copy()

for key, (col, label, _source, _role, _group, _color) in PATHOGENS.items():
    series = df_occ[col].ffill()
    mov_avg = series.rolling(window=OCC_WINDOW, min_periods=3).mean()
    mov_std = series.rolling(window=OCC_WINDOW, min_periods=3).std()
    zscore_out[f'zscore_{label}'] = ((series - mov_avg) / mov_std).round(4)

zscore_out = zscore_out.rename(columns={
    'epidemiological_weeks': 'epi_week',
    'detecta_percentage_mean': 'occupancy_%',
    'occ_rolling_mean': 'occupancy_rolling_mean',
    'occ_rolling_std': 'occupancy_rolling_std',
    'z_occupancy': 'zscore_occupancy',
})
zscore_out['epi_week'] = zscore_out['epi_week'].dt.strftime('%Y-%m-%d')
zscore_out = zscore_out.round(4)
zscore_out.to_csv(LEAD_TIME_DIR / 'weekly_zscores.tsv', sep='\t', index=False)

# %%
# --------------------- Lead time per wave and indicator ---------------------
rows = []

for wave, (wave_start, wave_end) in WAVES.items():
    mask = (
        (df_occ['epidemiological_weeks'] >= wave_start)
        & (df_occ['epidemiological_weeks'] <= wave_end)
    )
    df_w = df_occ[mask].copy().reset_index(drop=True)
    weeks = df_w['epidemiological_weeks']

    first_alert = df_w[df_w['alert_fired'] == 1]['epidemiological_weeks'].iloc[0]
    n_alert_weeks = int(df_w['alert_fired'].sum())

    for key, (col, label, source, role, _group, _color) in PATHOGENS.items():
        series = df_w[col].ffill().values.astype(float)
        smoothed = smooth(series, SMOOTH_WIN)

        if wave == 'Wave 1' and 'Denv' in key:
            local_mask = (weeks <= DENV_W1_CUT).values
            restricted = smoothed.copy()
            restricted[~local_mask] = np.nan
            peak_idx = np.nanargmax(restricted)
        else:
            peak_idx = np.nanargmax(smoothed)

        peak_week = weeks.iloc[peak_idx]
        lead_wks = round((peak_week - first_alert).days / 7, 1)

        rows.append({
            'wave': wave,
            'display_label': label,
            'source_type': source,
            'dataset_role': role,
            'granger_significant': key in granger_sig[wave],
            'first_alert_date': first_alert.strftime('%Y-%m-%d'),
            'n_alert_weeks': n_alert_weeks,
            'lab_peak_date': peak_week.strftime('%Y-%m-%d'),
            'lab_peak_value': round(float(series[peak_idx]), 4),
            'lead_time_weeks': lead_wks,
            'detected_before_peak': lead_wks > 0,
        })

lead_df = pd.DataFrame(rows)
lead_df.to_csv(LEAD_TIME_DIR / 'lead_time_table.tsv', sep='\t', index=False)

print(lead_df[['wave', 'display_label', 'granger_significant', 'first_alert_date',
               'lab_peak_date', 'lead_time_weeks', 'detected_before_peak']]
      .to_string(index=False))


# %%
# ------------------------------- Figure 5 -------------------------------
def format_week_axis(ax, interval=3):
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(
        mdates.WeekdayLocator(byweekday=mdates.SA, interval=interval)
    )
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=90, ha='center', fontsize=7)


fig = plt.figure(figsize=(18, 7))
gs = GridSpec(1, 3, figure=fig, wspace=0.2)

for col_idx, (wave_label, (wave_start, wave_end)) in enumerate(WAVES.items()):
    mask = (
        (df_occ['epidemiological_weeks'] >= wave_start)
        & (df_occ['epidemiological_weeks'] <= wave_end)
    )
    df_w = df_occ[mask].copy().reset_index(drop=True)
    weeks = df_w['epidemiological_weeks']
    sig_paths = granger_sig[wave_label]

    ax = fig.add_subplot(gs[0, col_idx])

    # Alert weeks
    for _, row in df_w[df_w['alert_fired'] == 1].iterrows():
        ax.axvspan(row['epidemiological_weeks'] - pd.Timedelta(days=3),
                   row['epidemiological_weeks'] + pd.Timedelta(days=3),
                   alpha=0.18, color=ALERT_COLOR, zorder=1)

    for key, (col, label, _source, _role, _group, color) in PATHOGENS.items():
        raw = df_w[col].ffill().values.astype(float)
        if np.all(np.isnan(raw)):
            continue

        curve = smooth(normalise(raw), win=SMOOTH_WIN)
        is_sig = key in sig_paths

        ax.plot(weeks, curve,
                color=color if is_sig else '#cccccc',
                lw=1.9 if is_sig else 0.9,
                linestyle='-' if is_sig else '--',
                alpha=1.0 if is_sig else 0.6,
                zorder=4 if is_sig else 2,
                label=label if is_sig else f'{label} (n.s.)')

        if is_sig:
            # Peak marker, matching the lead time table
            peak_row = lead_df[(lead_df['wave'] == wave_label)
                               & (lead_df['display_label'] == label)].iloc[0]
            peak_week = pd.to_datetime(peak_row['lab_peak_date'])
            peak_pos = int((weeks == peak_week).idxmax())

            ax.axvline(peak_week, color=color, lw=1.0, linestyle=':',
                       alpha=0.5, zorder=3)
            ax.scatter(peak_week, curve[peak_pos] + 0.09, color=color, s=100,
                       zorder=7, marker='^', edgecolors='white', lw=0.8)
            ax.vlines(peak_week, curve[peak_pos], curve[peak_pos] + 0.09,
                      color=color, lw=0.8, alpha=0.7, zorder=6)

    first_alert = pd.to_datetime(
        lead_df[lead_df['wave'] == wave_label]['first_alert_date'].iloc[0]
    )
    ax.axvline(first_alert, color=ALERT_COLOR, lw=2.5, linestyle='--', zorder=5)
    ax.text(first_alert, 1.10, 'First\nalert', ha='center', fontsize=7.5,
            color=ALERT_COLOR, fontweight='bold', va='bottom')

    ax.set_ylabel('Lab indicator (normalized)', fontsize=8, color='#333')
    ax.tick_params(axis='y', labelsize=7)
    ax.set_ylim(-0.05, 1.35)
    ax.set_title(wave_label, fontsize=12, fontweight='bold',
                 color=WAVE_COLORS[wave_label], pad=6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    format_week_axis(ax, interval=3)

    # Lead time per pathogen, printed below the panel (Figure 5 legend)
    sig_rows = lead_df[(lead_df['wave'] == wave_label)
                       & lead_df['granger_significant']]
    lead_text = "   ".join(
        f"{r['display_label']}: {r['lead_time_weeks']:.0f}w"
        for _, r in sig_rows.iterrows()
    )
    ax.text(0.5, -0.42, f"Lead time — {lead_text}", transform=ax.transAxes,
            ha='center', va='top', fontsize=8, color='#333')

    if col_idx == 0:
        handles, _ = ax.get_legend_handles_labels()
        extra = [
            mpatches.Patch(color=ALERT_COLOR, alpha=0.3,
                           label=f'Alert week (z > {THRESHOLD})'),
            Line2D([0], [0], color=ALERT_COLOR, lw=2, ls='--', label='First alert'),
            Line2D([0], [0], marker='^', color='gray', markersize=9, lw=0,
                   label='Laboratory peak'),
            Line2D([0], [0], color='#ccc', lw=1.0, ls='--', label='Not significant'),
        ]
        ax.legend(handles=extra + handles, fontsize=6, loc='upper left',
                  framealpha=0.85, ncol=2, title='Lab indicators',
                  title_fontsize=6.5)
    else:
        handles, _ = ax.get_legend_handles_labels()
        ax.legend(handles=handles, fontsize=6, loc='upper right',
                  framealpha=0.85, ncol=2, title='Lab indicators',
                  title_fontsize=6.5)

plt.savefig(LEAD_TIME_DIR / 'plots' / 'figure5.png', dpi=300, bbox_inches='tight')
plt.savefig(LEAD_TIME_DIR / 'plots' / 'figure5.svg', bbox_inches='tight')
plt.close('all')

print(f"\nFigure 5 and lead time tables written to {LEAD_TIME_DIR}")
