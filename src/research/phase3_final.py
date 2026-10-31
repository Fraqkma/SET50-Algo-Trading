"""Causal, source-gated Phase 3 research helpers.

This module contains diagnostics only. It does not create orders or portfolio
fills.
"""

from __future__ import annotations

from math import ceil
from typing import Iterable, Sequence

import numpy as np
import pandas as pd


HORIZONS = (1, 2, 3, 5)


def prepare_daily_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return causal features for one approved symbol's daily OHLCV frame.

    Current-day fields are used only after that session's bar is complete.
    Rolling references for activity and prior highs exclude the signal row.
    """
    required = {"open", "high", "low", "close", "volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"daily frame is missing columns: {sorted(missing)}")
    result = frame.copy().sort_index()
    if result.index.has_duplicates:
        raise ValueError("daily frame index contains duplicate dates")

    for column in required:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    raw_close = result["close"]
    adj_close = pd.to_numeric(result.get("adjusted_close", raw_close), errors="coerce")
    result["adjusted_close"] = adj_close
    adjustment = adj_close / raw_close
    result["adjusted_open"] = result["open"] * adjustment
    adjusted_high = result["high"] * adjustment
    adjusted_low = result["low"] * adjustment
    result["adjusted_prior20_high"] = adjusted_high.shift(1).rolling(20, min_periods=20).max()

    true_range = pd.concat(
        [adjusted_high - adjusted_low,
         (adjusted_high - adj_close.shift(1)).abs(),
         (adjusted_low - adj_close.shift(1)).abs()],
        axis=1,
    ).max(axis=1)
    atr10_pct = true_range.rolling(10, min_periods=10).mean() / adj_close
    result["atr10_pct"] = atr10_pct
    result["prior20_atr10_pct"] = atr10_pct.shift(10).rolling(20, min_periods=20).mean()
    result["prior20_high"] = result["high"].shift(1).rolling(20, min_periods=20).max()
    result["volume_ratio20"] = result["volume"] / result["volume"].shift(1).rolling(20, min_periods=20).mean()
    result["momentum20"] = adj_close / adj_close.shift(20) - 1
    result["return1"] = adj_close.pct_change()
    return result


def rolling_benchmark_drawdowns(
    frame: pd.DataFrame,
    window_sessions: int = 21,
    prior_regime_sessions: int = 63,
) -> pd.DataFrame:
    """Compute exact close-only rolling MDDs and strictly prior regimes."""
    if window_sessions < 2 or prior_regime_sessions < 1:
        raise ValueError("window and regime lengths must be positive")
    if not {"Date", "Close"}.issubset(frame.columns):
        raise ValueError("benchmark frame must contain Date and Close")
    data = frame[["Date", "Close"]].copy()
    data["Date"] = pd.to_datetime(data["Date"], errors="raise").dt.normalize()
    data["Close"] = pd.to_numeric(data["Close"], errors="raise")
    data = data.sort_values("Date", kind="stable").reset_index(drop=True)
    if data["Date"].duplicated().any() or not np.isfinite(data["Close"]).all() or (data["Close"] <= 0).any():
        raise ValueError("benchmark dates/prices are duplicated or invalid")

    rows: list[dict[str, object]] = []
    for end in range(window_sessions - 1, len(data)):
        start = end - window_sessions + 1
        closes = data.loc[start:end, "Close"].to_numpy(dtype=float)
        drawdowns = closes / np.maximum.accumulate(closes) - 1.0
        prior_start = start - prior_regime_sessions - 1
        if prior_start >= 0:
            prior_return = float(data.loc[start - 1, "Close"] / data.loc[prior_start, "Close"] - 1.0)
            regime = "BEAR" if prior_return < 0 else "NONNEGATIVE"
        else:
            prior_return = None
            regime = "UNKNOWN"
        rows.append({
            "window_start": data.loc[start, "Date"].date().isoformat(),
            "window_end": data.loc[end, "Date"].date().isoformat(),
            "sessions": window_sessions,
            "benchmark_mdd": max(0.0, -float(np.min(drawdowns))),
            "benchmark_return": float(closes[-1] / closes[0] - 1.0),
            "prior_regime_return": prior_return,
            "prior_regime": regime,
        })
    return pd.DataFrame(rows)


def summarize_risk_envelope(windows: pd.DataFrame) -> dict[str, object]:
    """Summarize empirical MDD thresholds and a provisional half-threshold buffer."""
    if windows.empty or "benchmark_mdd" not in windows:
        raise ValueError("no complete benchmark windows")
    quantile_levels = (0.0, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 1.0)
    values = windows["benchmark_mdd"].to_numpy(dtype=float)
    scenarios: list[dict[str, object]] = []
    for q in quantile_levels:
        mdd = float(np.quantile(values, q))
        nearest = windows.iloc[int(np.argmin(np.abs(values - mdd)))]
        threshold = 1.5 * mdd
        buffer = 0.5 * threshold
        scenarios.append({
            "quantile": q,
            "benchmark_mdd": mdd,
            "strict_portfolio_mdd_threshold": threshold,
            "provisional_research_buffer": buffer,
            "remaining_threshold_margin_after_buffer": threshold - buffer,
            "representative_window_start": nearest["window_start"],
            "representative_window_end": nearest["window_end"],
            "representative_benchmark_return": float(nearest["benchmark_return"]),
        })
    by_regime = {}
    for regime, group in windows.groupby("prior_regime", dropna=False):
        by_regime[str(regime)] = {
            "windows": int(len(group)),
            "mdd_mean": float(group["benchmark_mdd"].mean()),
            "mdd_median": float(group["benchmark_mdd"].median()),
            "mdd_p90": float(group["benchmark_mdd"].quantile(0.90)),
            "mdd_max": float(group["benchmark_mdd"].max()),
        }
    return {
        "window_count": int(len(windows)),
        "window_sessions": int(windows["sessions"].iloc[0]),
        "mdd_scenarios": scenarios,
        "regime_sensitivity": by_regime,
        "overlapping_windows_are_not_independent": True,
        "risk_buffer_policy": "50% of 1.5x historical benchmark MDD; provisional research reference only",
    }


def two_way_pigeonhole_bootstrap(
    differences: Sequence[float],
    dates: Sequence[str],
    symbols: Sequence[str],
    *,
    replications: int = 10_000,
    seed: int = 20_261_030,
) -> dict[str, object]:
    """Bootstrap a mean with independent date and symbol cluster weights."""
    values = np.asarray(differences, dtype=float)
    date_labels = np.asarray(dates, dtype=str)
    symbol_labels = np.asarray(symbols, dtype=str)
    if not (len(values) == len(date_labels) == len(symbol_labels)):
        raise ValueError("differences, dates and symbols must have equal length")
    valid = np.isfinite(values) & (date_labels != "") & (symbol_labels != "")
    values, date_labels, symbol_labels = values[valid], date_labels[valid], symbol_labels[valid]
    if not len(values):
        return {"n": 0, "mean": None, "ci95": None, "p_two_sided_centered": None}
    unique_dates, date_index = np.unique(date_labels, return_inverse=True)
    unique_symbols, symbol_index = np.unique(symbol_labels, return_inverse=True)
    observed = float(values.mean())
    if len(values) < 2 or len(unique_dates) < 2 or len(unique_symbols) < 2:
        return {"n": int(len(values)), "mean": observed, "ci95": None, "p_two_sided_centered": None,
                "warning": "insufficient independent clusters"}
    rng = np.random.default_rng(seed)
    bootstrap = np.empty(replications, dtype=float)
    date_probability = np.full(len(unique_dates), 1 / len(unique_dates))
    symbol_probability = np.full(len(unique_symbols), 1 / len(unique_symbols))
    chunk_size = 512
    for start in range(0, replications, chunk_size):
        stop = min(start + chunk_size, replications)
        count = stop - start
        date_counts = rng.multinomial(len(unique_dates), date_probability, size=count)
        symbol_counts = rng.multinomial(len(unique_symbols), symbol_probability, size=count)
        weights = date_counts[:, date_index] * symbol_counts[:, symbol_index]
        totals = weights.sum(axis=1)
        numerators = weights @ values
        bootstrap[start:stop] = np.divide(numerators, totals, out=np.full(count, np.nan), where=totals > 0)
    bootstrap = bootstrap[np.isfinite(bootstrap)]
    if not len(bootstrap):
        return {"n": int(len(values)), "mean": observed, "ci95": None, "p_two_sided_centered": None,
                "warning": "bootstrap produced no weighted replicates"}
    p_value = (np.count_nonzero(np.abs(bootstrap - observed) >= abs(observed)) + 1) / (len(bootstrap) + 1)
    return {
        "n": int(len(values)), "mean": observed,
        "ci95": [float(v) for v in np.quantile(bootstrap, [0.025, 0.975])],
        "p_two_sided_centered": float(p_value),
        "replications": int(len(bootstrap)), "date_clusters": int(len(unique_dates)),
        "symbol_clusters": int(len(unique_symbols)),
    }


def holm_adjust(p_values: dict[str, float | None]) -> dict[str, float | None]:
    """Apply Holm step-down correction to finite p-values."""
    usable = sorted((key, float(value)) for key, value in p_values.items() if value is not None and np.isfinite(value))
    adjusted: dict[str, float | None] = {key: None for key in p_values}
    running = 0.0
    count = len(usable)
    for rank, (key, p_value) in enumerate(usable):
        running = max(running, min(1.0, p_value * (count - rank)))
        adjusted[key] = running
    return adjusted


def kish_effective_clusters(labels: Iterable[str]) -> float:
    """Return inverse-Herfindahl effective cluster count for labels."""
    series = pd.Series(list(labels), dtype="string").dropna()
    if series.empty:
        return 0.0
    shares = series.value_counts(normalize=True).to_numpy(dtype=float)
    return float(1.0 / np.square(shares).sum())


def g1_promotion_gate(
    *, matched_events: int, symbols: int, dates: int, ci95: Sequence[float] | None,
    holm_adjusted_p: float | None,
) -> bool:
    """Require adequate breadth, positive clustered effect, and Holm significance."""
    return bool(
        matched_events >= 30 and symbols >= 10 and dates >= 20
        and ci95 is not None and len(ci95) == 2 and ci95[0] > 0
        and holm_adjusted_p is not None and np.isfinite(holm_adjusted_p)
        and holm_adjusted_p < 0.05
    )
