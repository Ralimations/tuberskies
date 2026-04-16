from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ChannelSnapshot:
    views: int
    subscribers: int
    watch_time_hours: int


def generate_analytics_data(days: int = 90, seed: int = 42) -> pd.DataFrame:
    """Generate deterministic mock YouTube analytics data for the dashboard."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=days, freq="D")
    baseline_views = np.linspace(1800, 3200, days)
    weekly_pattern = 260 * np.sin(np.arange(days) * (2 * np.pi / 7))
    retention_dips = np.where((np.arange(days) % 23) == 0, -8, 0)
    ctr_dips = np.where((np.arange(days) % 17) == 0, -1.1, 0)

    views = np.maximum(
        baseline_views + weekly_pattern + rng.normal(0, 180, days),
        200,
    ).round().astype(int)
    ctr = np.clip(
        6.1 + 0.5 * np.sin(np.arange(days) / 8) + ctr_dips + rng.normal(0, 0.25, days),
        2.0,
        12.0,
    ).round(2)
    retention = np.clip(
        47 + 4 * np.cos(np.arange(days) / 10) + retention_dips + rng.normal(0, 1.6, days),
        20.0,
        75.0,
    ).round(2)
    watch_time = np.clip((views * retention / 100) / 12, 25, None).round(1)
    subscribers = np.maximum((views / 165 + rng.normal(0, 1.1, days)), 1).round().astype(int)

    return pd.DataFrame(
        {
            "date": dates,
            "views": views,
            "ctr": ctr,
            "retention": retention,
            "watch_time_hours": watch_time,
            "subscribers_gained": subscribers,
        }
    )


def summarize_channel(df: pd.DataFrame) -> ChannelSnapshot:
    last_30 = df.tail(30)
    return ChannelSnapshot(
        views=int(last_30["views"].sum()),
        subscribers=int(last_30["subscribers_gained"].sum()),
        watch_time_hours=int(last_30["watch_time_hours"].sum()),
    )
