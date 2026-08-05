"""Core library for the healthcare occupancy analysis.

Handles the hourly-to-daily-to-weekly aggregation of the occupancy panel,
the moving-average / z-score computations behind the volatility index, and
the plots derived from them.
"""

from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from scipy.interpolate import make_interp_spline

# Volatility thresholds used throughout the manuscript.
# Weekly z-scores at or above HIGH_VOLATILITY_CUTOFF fire an occupancy alert.
MODERATE_VOLATILITY_CUTOFF = 0
HIGH_VOLATILITY_CUTOFF = 0.65

# Absolute occupancy thresholds used for the per-unit status maps.
AMBER_OCCUPANCY_CUTOFF = 45
RED_OCCUPANCY_CUTOFF = 50


def preprocess_data(raw_data, dates_to_remove):
    """Turn one unit's raw hourly TSV into a daily mean occupancy series.

    Returns (unit_name, week_days, daily_mean) where daily_mean is a
    single-column frame named after the unit and indexed by date.
    """

    # 1. Date format
    dates = raw_data['Date']
    dates = [datetime.strptime(date, '%d/%m/%Y') for date in dates]
    dates = [date.strftime('%Y-%m-%d') for date in dates]
    raw_data['Date'] = dates

    # 2. Drop the excluded dates (outage periods)
    raw_data = raw_data.loc[~raw_data['Date'].isin(dates_to_remove)]

    # 3. Unit name and weekdays
    local = raw_data["Local"].unique()
    week_days = raw_data["Day"]

    # 4. Standardize missing values
    raw_data.set_index("Date", inplace=True)
    raw_data = raw_data.replace("-", np.nan)
    raw_data = raw_data.replace("NA", np.nan)

    # 5. Keep only the hourly columns
    data_cleaned = raw_data.drop(["Local", "Day"], axis=1, inplace=False)
    data_cleaned = data_cleaned.apply(pd.to_numeric, errors="coerce")

    # 6. Daily mean across the hourly readings
    data_cleaned = data_cleaned.T
    data_cleaned = pd.DataFrame(data_cleaned.mean())

    # 7. Name the column after the unit
    data_cleaned = data_cleaned.rename(columns={data_cleaned.columns[0]: str(local[0])})

    return local, week_days, data_cleaned


def get_gold_standard_data(gold_standard_list, dates_to_remove, monitores_dir):
    """Load every monitored unit and merge them into one daily occupancy panel."""

    dfs = []

    for file_name in gold_standard_list:
        file_path = f"{monitores_dir}/{file_name}"
        data = pd.read_csv(file_path, sep="\t")

        local, week_days, mean_by_day = preprocess_data(data, dates_to_remove)
        print("Merging data from: " + str(local[0]))

        dfs.append(mean_by_day)

    merged_data = pd.concat(dfs, axis=1, join='inner')
    merged_data.index = pd.to_datetime(merged_data.index).date

    return merged_data, week_days


def moving_average_or_zscores(merged_data, window=7):
    """Rolling mean and standard deviation of daily occupancy, per unit."""

    merged_data = merged_data.apply(pd.to_numeric, errors="coerce")
    moving_average = merged_data.transform(
        lambda x: x.rolling(window=window, min_periods=1).mean()
    )
    moving_stds = merged_data.transform(
        lambda x: x.rolling(window=window, min_periods=1).std()
    )

    print("Z-scores with moving average. Window size: ", window)

    return moving_stds, moving_average


def concat_means(merged_data, moving_stds, moving_average):
    """Collapse the per-unit panel into the network-wide mean series.

    Returns a frame with percentage_mean, moving_stds_mean,
    moving_average_mean and moving_zscore.
    """

    percentage_mean = pd.DataFrame(merged_data.mean(axis=1))
    moving_stds_mean = pd.DataFrame(moving_stds.mean(axis=1))
    moving_average_mean = pd.DataFrame(moving_average.mean(axis=1))
    moving_z_scores = (percentage_mean - moving_average_mean) / moving_stds_mean

    merged_means = pd.concat(
        [percentage_mean, moving_stds_mean, moving_average_mean, moving_z_scores],
        axis=1,
    )
    merged_means.columns = [
        'percentage_mean',
        'moving_stds_mean',
        'moving_average_mean',
        'moving_zscore',
    ]
    merged_means.index = merged_data.index

    return merged_means


def get_weekly_data_from_daily(daily_data):
    """Aggregate daily values into epidemiological weeks (Sunday to Saturday).

    The resulting index is the Saturday that closes each week.
    """

    daily_data.index = pd.to_datetime(daily_data.index)

    adjusted_dayofweek = (daily_data.index.dayofweek + 1) % 7

    saturday_of_week = (
        daily_data.index
        - pd.to_timedelta(adjusted_dayofweek, unit="d")
        + pd.DateOffset(days=6)
    )

    daily_data.index = saturday_of_week

    return daily_data.groupby(daily_data.index).mean()


def plot_combined_data(datasets,
                       windows,
                       path_output,
                       column_data="moving_average_mean",
                       title_name='Moving average',
                       period='days',
                       output_file_name=None):
    """Overlay the same metric computed at several rolling-window lengths."""

    sns.set_theme(style="white", context="talk")
    plt.figure(figsize=(14, 7), facecolor='white')

    for merged_means, window in zip(datasets, windows):
        sns.lineplot(
            data=merged_means,
            x=merged_means.index,
            y=column_data,
            label=f'{window} days',
        )

    plt.title(f"{title_name}")
    plt.xlabel(None)
    plt.ylabel('Occupancy (%)')

    for position in ['top', 'right']:
        plt.gca().spines[position].set_visible(False)
    for position in ['bottom', 'left']:
        plt.gca().spines[position].set_linewidth(0.5)

    if period == 'days':
        # Label every seventh tick to keep the daily axis readable
        ticks = datasets[0].index
        tick_labels = [str(tick) if i % 7 == 0 else '' for i, tick in enumerate(ticks)]
        plt.xticks(ticks, labels=tick_labels, rotation=90, fontsize=10)

    if period == 'weeks':
        plt.xticks(datasets[0].index, rotation=90, fontsize=10)

    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), frameon=False)

    if output_file_name:
        plt.savefig(f'{path_output}/plots/{output_file_name}.svg',
                    facecolor='white', bbox_inches='tight')
        plt.savefig(f'{path_output}/plots/{output_file_name}.png',
                    facecolor='white', bbox_inches='tight')
    plt.tight_layout()
    plt.close()


def plot_combined_test(datasets,
                       windows,
                       path_output,
                       column_data="moving_average_mean",
                       title_name='Moving average (weeks)',
                       period='weeks',
                       output_file_name=None):
    """Same as plot_combined_data, with cubic-spline smoothing on weekly data."""

    sns.set_theme(style="white", context="talk")
    plt.figure(figsize=(14, 5), facecolor='white')

    for merged_means, window in zip(datasets, windows):
        x = merged_means.index
        y = merged_means[column_data]

        # Seconds since epoch, to keep the spline fit away from int64 overflow
        x_numeric = x.astype('int64') // 10**9

        if len(x) > 3:
            x_smooth_numeric = np.linspace(x_numeric.min(), x_numeric.max(), 300)
            spline = make_interp_spline(x_numeric, y, k=3)
            y_smooth = spline(x_smooth_numeric)
            x_smooth = pd.to_datetime(x_smooth_numeric, unit='s')
        else:
            # Too few points to smooth: fall back to the raw series
            x_smooth, y_smooth = x, y

        sns.lineplot(x=x_smooth, y=y_smooth, label=f'{window} days')

    plt.title(title_name)
    plt.xlabel(None)
    plt.ylabel('Occupancy (%)')

    for position in ['top', 'right']:
        plt.gca().spines[position].set_visible(False)
    for position in ['bottom', 'left']:
        plt.gca().spines[position].set_linewidth(0.5)

    plt.xticks(datasets[0].index, rotation=90, fontsize=10)
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1), frameon=False)

    if output_file_name:
        plt.savefig(f'{path_output}/plots/{output_file_name}.svg',
                    facecolor='white', bbox_inches='tight')
        plt.savefig(f'{path_output}/plots/{output_file_name}.png',
                    facecolor='white', bbox_inches='tight')

    plt.tight_layout()
    plt.close()


def metrics_by_unit(merged_data, moving_average, moving_stds):
    """Per-unit weekly occupancy, z-score and colour-coded status."""

    metrics = {}

    for col in merged_data.columns:
        new_df = pd.DataFrame({
            'percentage': merged_data[col],
            'moving_average': moving_average[col],
            'moving_stds': moving_stds[col],
        })
        new_df['moving_zscore'] = (
            (merged_data[col] - moving_average[col]) / moving_stds[col]
        )
        metrics[col] = new_df

    for key, df in metrics.items():
        metrics[key] = get_weekly_data_from_daily(df)
        conditions = [
            (metrics[key]['percentage'] > RED_OCCUPANCY_CUTOFF)
            | (metrics[key]['moving_zscore'] >= HIGH_VOLATILITY_CUTOFF),
            (metrics[key]['percentage'] >= AMBER_OCCUPANCY_CUTOFF)
            | (metrics[key]['moving_zscore'] > MODERATE_VOLATILITY_CUTOFF),
            (metrics[key]['percentage'] < AMBER_OCCUPANCY_CUTOFF)
            & (metrics[key]['moving_zscore'] <= MODERATE_VOLATILITY_CUTOFF),
        ]
        choices = ['red', 'orange', 'green']
        metrics[key]['status'] = np.select(conditions, choices, default='lightgray')

    return metrics


def viz_metrics_by_city_sns(merged_means_weekly, city_name=None, output_file_name=None):
    """City-level occupancy with its moving average and weekly z-score bars.

    `output_file_name` is a path stem: `.svg` and `.png` are appended.
    """

    sns.set_theme(style="white", context="talk")

    # Reindex onto a gap-free weekly axis so missing weeks stay visible
    full_date_range = pd.date_range(
        start=merged_means_weekly.index.min(),
        end=merged_means_weekly.index.max(),
        freq='7D',
    )
    merged_means_weekly = merged_means_weekly.reindex(full_date_range)
    x_labels = merged_means_weekly.index.strftime('%Y-%m-%d')

    fig, axes = plt.subplots(
        2, 1, figsize=(14, 7), sharex=True, gridspec_kw={'height_ratios': [4, 1]}
    )

    # Top panel: occupancy and its 42-day moving average
    y1 = merged_means_weekly['percentage_mean']
    y2 = merged_means_weekly['moving_average_mean']

    valid_mask = ~y1.isna()
    x_numeric = np.arange(len(x_labels))

    spline1 = make_interp_spline(x_numeric[valid_mask], y1[valid_mask], k=3)
    spline2 = make_interp_spline(x_numeric[valid_mask], y2[valid_mask], k=3)

    x_smooth_numeric = np.linspace(x_numeric.min(), x_numeric.max(), 300)
    y1_smooth = spline1(x_smooth_numeric)
    y2_smooth = spline2(x_smooth_numeric)

    sns.lineplot(ax=axes[0], x=x_smooth_numeric, y=y1_smooth,
                 color='#3893e7', label='Occupancy data', linewidth=2)
    sns.lineplot(ax=axes[0], x=x_smooth_numeric, y=y2_smooth,
                 color='blue', label='Moving average (42 days)', linewidth=2)

    axes[0].set_ylabel('Occupancy (%)')
    axes[0].legend(loc='upper right', frameon=False)

    # Bottom panel: weekly z-scores, colour-coded by volatility level
    colors = merged_means_weekly['moving_zscore'].apply(
        lambda x: '#ff5c33' if x >= HIGH_VOLATILITY_CUTOFF
        else '#ffbb33' if x >= MODERATE_VOLATILITY_CUTOFF
        else '#79d2a6'
    )
    axes[1].bar(x_numeric, merged_means_weekly['moving_zscore'],
                color=colors, width=0.8)
    axes[1].set_ylabel('Z-Score')
    axes[1].set_yticks([-1, 0, 1])

    for ax in axes:
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_linewidth(0.5)
        ax.spines['left'].set_linewidth(0.5)

    axes[1].set_xticks(x_numeric)
    axes[1].set_xticklabels(x_labels, rotation=90, fontsize=10)
    axes[0].set_xlim([x_numeric.min() - 0.5, x_numeric.max() + 0.5])
    axes[1].set_xlim([x_numeric.min() - 0.5, x_numeric.max() + 0.5])

    fig.suptitle(f'Occupancy average in {city_name}', fontsize=18)
    plt.tight_layout()

    if output_file_name:
        plt.savefig(f'{output_file_name}.svg', bbox_inches='tight')
        plt.savefig(f'{output_file_name}.png', dpi=600, bbox_inches='tight')

    plt.close()


def plot_zscores_barplot_by_unit(metrics, week_date, output_file_name=None):
    """Horizontal bar plot of per-unit z-scores for a single week.

    `output_file_name` is a path stem: `.svg` and `.png` are appended.
    """

    unit_names = []
    z_scores = []
    reference_week = str(week_date)

    for unit, df in metrics.items():
        if len(df) > 0 and week_date in df.index:
            unit_names.append(unit)
            z_scores.append(df['moving_zscore'][week_date])

    colors = [
        'rgba(0, 128, 0, 0.7)' if x < MODERATE_VOLATILITY_CUTOFF else
        'rgba(255, 165, 0, 0.7)' if x < HIGH_VOLATILITY_CUTOFF else
        'rgba(255, 0, 0, 0.7)'
        for x in z_scores
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=z_scores,
        y=unit_names,
        orientation='h',
        marker_color=colors,
        text=[f'{x:.2f}' for x in z_scores],
        textposition='outside',
    ))

    # Threshold reference lines
    for cutoff, color in ((MODERATE_VOLATILITY_CUTOFF, 'orange'),
                          (HIGH_VOLATILITY_CUTOFF, 'red')):
        fig.add_shape(
            type='line',
            x0=cutoff, y0=-0.5,
            x1=cutoff, y1=len(unit_names) - 0.5,
            line=dict(color=color, width=1.5, dash='dash'),
        )

    fig.update_layout(
        title=f'Occupancy status by unit (week of {reference_week})',
        xaxis_title='Z-Score',
        yaxis_title=None,
        yaxis=dict(tickfont=dict(size=14), type='category'),
        xaxis=dict(tickfont=dict(size=14), zeroline=True, range=[-2, 2]),
        template='plotly_white',
        width=570,
        height=500,
        title_font=dict(size=18),
        xaxis_title_font=dict(size=16),
        yaxis_title_font=dict(size=16),
    )

    if output_file_name:
        fig.write_image(f"{output_file_name}.png", scale=2)
        fig.write_image(f"{output_file_name}.svg")
