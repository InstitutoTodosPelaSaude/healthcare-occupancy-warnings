# %%
"""Step 04: Dynamic Time Warping between occupancy and laboratory indicators.

Each series is independently min-max rescaled to 0-1 so the comparison
reflects the shape of the temporal pattern rather than its magnitude, then
aligned against mean occupancy with DTW (Euclidean inner distance).

This produces Figure 3 and the DTW distances quoted in its legend.

Outputs
    results/dtw/dtw_distances.tsv
    results/dtw/plots/dtw_alignments.{png,svg}
"""

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dtaidistance import dtw
from scipy.interpolate import make_interp_spline
from sklearn.preprocessing import MinMaxScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.paths import CONSOLIDATED_DATA_INTERMEDIATE, DTW_DIR, ensure_dir

ensure_dir(DTW_DIR, DTW_DIR / "plots")

# %%
consolidated = pd.read_csv(CONSOLIDATED_DATA_INTERMEDIATE, sep="\t")
consolidated['epidemiological_weeks'] = pd.to_datetime(
    consolidated['epidemiological_weeks']
)

OCCUPANCY = 'occupancy_percentage_mean'

# Panel order follows Figure 3: SARS-CoV-2 (A, B), DENV (C, D), RV (E, F),
# alternating private positivity rate and public case counts.
COMPARISONS = [
    ('exploratory_posrate_sc2', 'SC2 positivity (%) - private labs'),
    ('validation_cases_sc2', 'SC2 cases (#) - SIVEP-SRAG'),
    ('exploratory_posrate_denv', 'DENV positivity (%) - private labs'),
    ('validation_cases_denv', 'DENV cases (#) - InfoDengue'),
    ('exploratory_posrate_vrisp', 'RV positivity (%) - private labs'),
    ('validation_vrisp_cases_norm', 'RV cases (#) - SIVEP-SRAG'),
]

targets = [name for name, _ in COMPARISONS] + [OCCUPANCY]

# %%
scaler = MinMaxScaler()
scaled = consolidated[targets].copy()
scaled[targets] = scaler.fit_transform(scaled[targets])

base_occupancy = scaled[OCCUPANCY].dropna().values


def smooth_curve(y, k=3):
    """Cubic-spline smoothing for display only; DTW runs on the raw series."""
    x = np.arange(len(y))
    mask = ~np.isnan(y)
    if mask.sum() < k + 1:
        return x, y
    spline = make_interp_spline(x[mask], y[mask], k=k)
    x_smooth = np.linspace(x.min(), x.max(), 300)
    return x_smooth, spline(x_smooth)


# %%
fig, axes = plt.subplots(len(COMPARISONS), 1, figsize=(6, 14), sharex=True)

MAIN_LINE_WIDTH = 0.7
# Vertical offset that separates the two curves within each panel
PANEL_SHIFT = 1.2

distances = []

for ax, (target, label) in zip(axes, COMPARISONS):
    compare = scaled[target].dropna().values
    path = dtw.warping_path(compare, base_occupancy)
    distance = dtw.distance(compare, base_occupancy)
    distances.append({'indicator': target, 'label': label,
                      'dtw_distance': distance})

    occupancy_shifted = base_occupancy - PANEL_SHIFT

    x_base, y_base = smooth_curve(occupancy_shifted)
    x_comp, y_comp = smooth_curve(compare)

    ax.plot(x_comp, y_comp, color='black', label=label, linewidth=MAIN_LINE_WIDTH)
    ax.plot(x_base, y_base, color='#3893e7', label='Occupancy',
            linewidth=MAIN_LINE_WIDTH)

    # Grey warping path between the two series
    for (ix, jx) in path:
        ax.plot([ix, jx], [compare[ix], occupancy_shifted[jx]],
                color='gray', linewidth=0.3, alpha=0.5)

    ax.legend(loc='upper right', fontsize=10)
    ax.text(0.01, 0.95, f'DTW distance = {distance:.2f}',
            transform=ax.transAxes, fontsize=10, va='top', ha='left', color='black')

    ax.set_yticks([])
    ax.set_title("")
    ax.grid(False)
    for spine in ('right', 'top', 'left'):
        ax.spines[spine].set_visible(False)

plt.xlabel("Epidemiological weeks (Index)", fontsize=12)
plt.tight_layout()
plt.savefig(DTW_DIR / "plots" / "dtw_alignments.svg",
            format="svg", bbox_inches="tight", dpi=300)
plt.savefig(DTW_DIR / "plots" / "dtw_alignments.png",
            format="png", bbox_inches="tight", dpi=300)
plt.close('all')

# %%
distances_df = pd.DataFrame(distances)
distances_df.to_csv(DTW_DIR / "dtw_distances.tsv", sep="\t", index=False)
print(distances_df.to_string(index=False))
