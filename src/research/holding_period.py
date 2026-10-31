"""Small deterministic helpers for descriptive, fixed-horizon research."""
from __future__ import annotations

from collections import Counter
from typing import Sequence

import numpy as np


def horizon_index(entry_index: int, sessions: int) -> int:
    """Return the close index after ``sessions`` observed trading sessions.

    The entry session is session one. Indices refer to observed eligible rows,
    never calendar-day arithmetic.
    """
    if entry_index < 0 or sessions < 1:
        raise ValueError("entry_index must be nonnegative and sessions positive")
    return entry_index + sessions - 1


def align_directional_return(gross: float, net: float, direction: int) -> tuple[float, float]:
    """Direction-align gross outcome while keeping execution costs adverse."""
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or +1")
    costs = gross - net
    aligned_gross = direction * gross
    return aligned_gross, aligned_gross - costs


def first_passage(values: Sequence[float | None], threshold: float) -> dict[str, object]:
    """Find first observed close crossing or return an explicit censor state."""
    for index, value in enumerate(values, start=1):
        if value is None or not np.isfinite(value):
            return {"status": "INSUFFICIENT_DATA", "session": None, "observed_sessions": index - 1}
        crossed = value >= threshold if threshold >= 0 else value <= threshold
        if crossed:
            return {"status": "HIT", "session": index, "observed_sessions": index}
    return {"status": "RIGHT_CENSORED", "session": None, "observed_sessions": len(values)}


def _classify_passage(path: Sequence[float | None], threshold: float,
                      competing_threshold: float | None) -> tuple[str, int | None]:
    missing = False
    for index, value in enumerate(path, start=1):
        if value is None or not np.isfinite(value):
            missing = True
            break
        target_hit = value >= threshold if threshold >= 0 else value <= threshold
        competing_hit = (competing_threshold is not None and
            (value >= competing_threshold if competing_threshold >= 0 else value <= competing_threshold))
        if target_hit:
            return "HIT", index
        if competing_hit:
            return "COMPETING_THRESHOLD_FIRST", index
    return ("INSUFFICIENT_DATA" if missing else "RIGHT_CENSORED"), None


def cluster_bootstrap(values: Sequence[float], dates: Sequence[str], symbols: Sequence[str], *,
                      replications: int = 10_000, seed: int = 20261101) -> dict[str, object]:
    """Two-way date/symbol pigeonhole bootstrap of an event- or pair-level mean."""
    x = np.asarray(values, dtype=float)
    d = np.asarray(dates, dtype=str)
    s = np.asarray(symbols, dtype=str)
    valid = np.isfinite(x) & (d != "") & (s != "")
    x, d, s = x[valid], d[valid], s[valid]
    if len(x) == 0:
        return {"n": 0, "mean": None, "ci95": None}
    if len(np.unique(d)) < 2 or len(np.unique(s)) < 2:
        return {"n": len(x), "mean": float(x.mean()), "ci95": None,
                "warning": "fewer than two date or symbol clusters"}
    di, d = np.unique(d, return_inverse=True)
    si, s = np.unique(s, return_inverse=True)
    rng = np.random.default_rng(seed)
    samples = np.empty(replications, dtype=float)
    pd = np.full(len(di), 1 / len(di))
    ps = np.full(len(si), 1 / len(si))
    for start in range(0, replications, 512):
        end = min(start + 512, replications)
        dc = rng.multinomial(len(di), pd, size=end - start)
        sc = rng.multinomial(len(si), ps, size=end - start)
        weights = dc[:, d] * sc[:, s]
        totals = weights.sum(axis=1)
        samples[start:end] = np.divide(weights @ x, totals,
            out=np.full(end - start, np.nan), where=totals > 0)
    samples = samples[np.isfinite(samples)]
    mean = float(x.mean())
    p_value = float((np.count_nonzero(np.abs(samples - mean) >= abs(mean)) + 1) /
                    (len(samples) + 1)) if len(samples) else None
    return {"n": len(x), "mean": mean,
            "ci95": [float(v) for v in np.quantile(samples, [.025, .975])],
            "p_two_sided_centered": p_value, "replications": len(samples),
            "date_clusters": len(di), "symbol_clusters": len(si)}


def holm_adjust(p_values: dict[str, float | None]) -> dict[str, float | None]:
    """Holm step-down adjustment, preserving missing p-values."""
    usable = sorted((k, float(v)) for k, v in p_values.items() if v is not None and np.isfinite(v))
    out: dict[str, float | None] = {k: None for k in p_values}
    running = 0.0
    for rank, (key, value) in enumerate(usable):
        running = max(running, min(1.0, value * (len(usable) - rank)))
        out[key] = running
    return out


def passage_counts(rows: Sequence[dict[str, object]], threshold: float,
                   horizons: Sequence[int], *, competing_threshold: float | None = None,
                   replications: int = 2_000, seed: int = 20261101) -> dict[str, object]:
    """Summarize first passage and retain the opposite boundary as a competing event."""
    by_session = Counter()
    statuses = Counter()
    times: list[int] = []
    cohort_dates: list[str] = []
    cohort_symbols: list[str] = []
    classified: list[tuple[str, int | None]] = []
    for row in rows:
        path = list(row["net_path"])
        cohort_dates.append(str(row.get("date", "")))
        cohort_symbols.append(str(row.get("symbol", "")))
        status, hit_session = _classify_passage(path, threshold, competing_threshold)
        classified.append((status, hit_session))
        if status == "HIT":
            statuses["HIT"] += 1
            times.append(int(hit_session))
        elif status == "COMPETING_THRESHOLD_FIRST":
            statuses["COMPETING_THRESHOLD_FIRST"] += 1
        elif status == "INSUFFICIENT_DATA":
            statuses["INSUFFICIENT_DATA"] += 1
        else:
            statuses["RIGHT_CENSORED"] += 1
    for h in horizons:
        by_session[str(h)] = sum(t <= h for t in times)
    exact_counts = Counter(times)
    observed_max = max((len(row["net_path"]) for row in rows), default=0)
    exact_by_session = {str(session): exact_counts.get(session, 0)
                        for session in range(1, observed_max + 1)}
    fractions = {k: (v / len(rows) if rows else None) for k, v in by_session.items()}
    bands = {}
    if all(cohort_dates) and all(cohort_symbols):
        # The values are target-first cumulative-incidence indicators by H.
        for h in horizons:
            flags = []
            for status, session in classified:
                flags.append(1.0 if status == "HIT" and session <= h else 0.0)
            boot = cluster_bootstrap(flags, cohort_dates, cohort_symbols,
                                     replications=replications, seed=seed + int(h))
            bands[str(h)] = boot.get("ci95")
    return {"threshold": threshold, "cohort_n": len(rows),
            "first_hit_count_by_session": dict(by_session),
            "first_hit_fraction_by_session": fractions,
            "first_hit_count_at_each_session": exact_by_session,
            "first_hit_fraction_at_each_session": {
                key: (value / len(rows) if rows else None)
                for key, value in exact_by_session.items()},
            "first_hit_fraction_ci95_two_way_cluster": bands,
            "status_counts": dict(statuses),
            "competing_threshold": competing_threshold,
            "median_hit_session_among_hits": float(np.median(times)) if times else None,
            "unhit_events_retained_as_censored": statuses.get("RIGHT_CENSORED", 0)}
