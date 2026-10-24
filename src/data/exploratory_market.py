"""Read-only, provenance-preserving exploratory daily market view.

This module is intentionally separate from formal eligibility/backtest inputs.
It never rewrites source files, fills missing values, or maps one security to
another.  The only date boundaries applied are the verified identity boundaries
documented in reports/historical_security_identity_audit.json.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


OHLCV = ("Open", "High", "Low", "Close", "Volume")
IDENTITY_STARTS = {
    # Verified new-security boundaries; prevents vendor backfills from joining
    # predecessor prices to the current security under the same display symbol.
    "TRUE": pd.Timestamp("2023-03-03"),
    "GULF": pd.Timestamp("2025-04-03"),
    "SCB": pd.Timestamp("2022-04-27"),
    "TIDLOR": pd.Timestamp("2025-05-16"),
    "MRDIYT": pd.Timestamp("2025-11-05"),
    "BANPU": pd.Timestamp("2026-08-04"),
}
IDENTITY_NOTES = {
    "TRUE": "Only the new TRUE security from 2023-03-03; TRUEE/DTAC are not spliced.",
    "GULF": "Only the post-amalgamation GULF series from 2025-04-03; GULFI/INTUCH are separate.",
    "SCB": "Only SCB X observations from 2022-04-27; predecessor SCBB is not joined.",
    "TIDLOR": "Only TIDLOR observations from its 2025-05-16 listing; NTL is not joined.",
    "MRDIYT": "Observations begin at the verified 2025-11-05 listing date.",
    "BANPU": "Only the post-amalgamation/relisting BANPU security from 2026-08-04; BANPUU is separate.",
    "TTB": "Ticker continuity from TMB is identity-audit approved; no price adjustment is applied.",
}


@dataclass(frozen=True)
class Source:
    symbol: str
    path: Path
    source_type: str
    source_label: str
    priority: int
    approved_from: pd.Timestamp | None = None
    approved_to: pd.Timestamp | None = None


def _symbols_from_csv(path: Path, category: str) -> str:
    name = path.stem.upper()
    if category in {"approved_raw", "pilot_availability", "pilot_depth"}:
        return name.removesuffix("_BK")
    if category == "pilot_daily":
        return name.removesuffix("_2010_2026")
    if category == "legacy_pilot":
        return name.split("_")[0]
    return name


def discover_sources(root: str | Path) -> list[Source]:
    """Discover daily OHLCV paths and explicit approved date boundaries."""
    project = Path(root)
    manifest_path = project / "data/processed/approved_market_data_manifest.csv"
    manifest = pd.read_csv(manifest_path, dtype=str).fillna("") if manifest_path.exists() else pd.DataFrame()
    approvals = {row.set_symbol: row for row in manifest.itertuples(index=False)}
    sources: list[Source] = []
    locations = (
        ("approved_raw", project / "data/raw/market_data", "raw_yahoo"),
        ("pilot_daily", project / "data/pilot/historical_daily", "yahoo_staging"),
        ("pilot_availability", project / "data/pilot/historical_set50_availability", "yahoo_historical_availability_staging"),
        ("pilot_depth", project / "data/pilot/historical_depth_experiment", "yahoo_historical_depth_staging"),
        ("legacy_pilot", project / "data/pilot/historical_acquisition", "legacy_yahoo_staging"),
    )
    for category, directory, source_type in locations:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*.csv")):
            symbol = _symbols_from_csv(path, category)
            approval = approvals.get(symbol) if category == "approved_raw" else None
            sources.append(Source(
                symbol=symbol,
                path=path,
                source_type=("approved_yahoo" if approval and approval.approval_status.startswith("APPROVED") else source_type),
                source_label=path.relative_to(project).as_posix(),
                priority=0 if approval and approval.approval_status.startswith("APPROVED") else {
                    "approved_raw": 1, "pilot_daily": 2, "pilot_availability": 3,
                    "pilot_depth": 4, "legacy_pilot": 5,
                }[category],
                approved_from=pd.Timestamp(approval.approved_from) if approval and approval.approved_from else None,
                approved_to=pd.Timestamp(approval.approved_to) if approval and approval.approved_to else None,
            ))
    return sources


def _read_daily(source: Source) -> tuple[pd.DataFrame, dict[str, object]]:
    """Read source rows and summarize quality without repairing observations."""
    try:
        raw = pd.read_csv(source.path)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        return pd.DataFrame(), {"read_error": str(exc)}
    rename = {str(c).strip().lower().replace(" ", "_"): c for c in raw.columns}
    date_column = rename.get("date", rename.get("datetime"))
    summary: dict[str, object] = {"rows": len(raw), "duplicate_dates": 0, "missing_trading_day_gaps": 0,
                                  "invalid_ohlc": 0, "volume_available": "volume" in rename,
                                  "volume_non_null_rows": 0, "missing_close_rows": len(raw), "read_error": ""}
    if date_column is None or "close" not in rename:
        summary["read_error"] = "missing Date/Close column"
        return pd.DataFrame(), summary
    frame = pd.DataFrame({"Date": pd.to_datetime(raw[date_column], errors="coerce")})
    for col in OHLCV:
        key = col.lower()
        frame[col] = pd.to_numeric(raw[rename[key]], errors="coerce") if key in rename else float("nan")
    summary["volume_non_null_rows"] = int(frame["Volume"].notna().sum())
    summary["missing_close_rows"] = int(frame["Close"].isna().sum())
    frame = frame.dropna(subset=["Date"])
    summary["duplicate_dates"] = int(frame["Date"].duplicated(keep=False).sum())
    valid_dates = frame["Date"].drop_duplicates().sort_values()
    if len(valid_dates) > 1:
        gaps = valid_dates.diff().dt.days
        # Large weekday gaps are a conservative gap flag, not an exchange calendar.
        summary["missing_trading_day_gaps"] = int((gaps > 4).sum())
    summary["invalid_ohlc"] = int(((frame["High"] < frame[["Open", "Close"]].max(axis=1)) |
                                      (frame["Low"] > frame[["Open", "Close"]].min(axis=1)) |
                                      (frame[["Open", "High", "Low", "Close"]] <= 0).any(axis=1)).sum())
    complete_ohlc = frame[["Open", "High", "Low", "Close"]].notna().all(axis=1)
    invalid_ohlc = ((frame["High"] < frame[["Open", "Close"]].max(axis=1)) |
                    (frame["Low"] > frame[["Open", "Close"]].min(axis=1)) |
                    (frame[["Open", "High", "Low", "Close"]] <= 0).any(axis=1))
    frame["ohlc_status"] = "INCOMPLETE"
    frame.loc[complete_ohlc, "ohlc_status"] = "VALID"
    frame.loc[complete_ohlc & invalid_ohlc, "ohlc_status"] = "INVALID"
    frame["Date"] = frame["Date"].dt.normalize()
    frame["source_type"] = source.source_type
    frame["source_file"] = source.source_label
    return frame, summary


def inventory_sources(root: str | Path) -> pd.DataFrame:
    """Return per-file OHLCV dates, quality, volume and approval scope."""
    rows: list[dict[str, object]] = []
    project = Path(root)
    for source in discover_sources(project):
        frame, quality = _read_daily(source)
        usable = frame.dropna(subset=["Close"]) if "Close" in frame else pd.DataFrame(columns=["Date", "Close"])
        rows.append({
            "symbol": source.symbol, "source_type": source.source_type,
            "path": source.source_label, "first_date": usable["Date"].min().date().isoformat() if not usable.empty else "",
            "last_date": usable["Date"].max().date().isoformat() if not usable.empty else "",
            "rows": int(len(frame)), "usable_close_rows": int(len(usable)),
            "duplicate_dates": quality.get("duplicate_dates", 0),
            "missing_trading_day_gaps_gt4_calendar_days": quality.get("missing_trading_day_gaps", 0),
            "invalid_ohlc": quality.get("invalid_ohlc", 0),
            "volume_available": quality.get("volume_available", False),
            "volume_non_null_rows": quality.get("volume_non_null_rows", 0),
            "missing_close_rows": quality.get("missing_close_rows", len(frame)),
            "approved_from": source.approved_from.date().isoformat() if source.approved_from is not None else "",
            "approved_to": source.approved_to.date().isoformat() if source.approved_to is not None else "",
            "identity_note": IDENTITY_NOTES.get(source.symbol, "Exact source symbol retained; no cross-symbol price mapping."),
            "notes": quality.get("read_error", ""),
        })
    return pd.DataFrame(rows)


def build_exploratory_view(root: str | Path, symbols: Iterable[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build unique symbol/date rows; disputed values are reported and omitted.

    Source precedence is approved manifest rows in their approved window, then
    raw acquisition outside that window, full-history Yahoo staging, the later
    historical-membership availability experiment, the historical-depth
    experiment, and legacy Yahoo staging.
    Exact symbol identity is always retained.
    """
    project = Path(root)
    selected = {s.upper() for s in symbols} if symbols is not None else None
    sources = discover_sources(project)
    by_symbol: dict[str, list[tuple[Source, pd.DataFrame]]] = {}
    conflicts: list[dict[str, object]] = []
    for source in sources:
        if selected is not None and source.symbol not in selected:
            continue
        frame, _ = _read_daily(source)
        if frame.empty:
            continue
        frame = frame.copy()
        frame["symbol"] = source.symbol
        frame["_priority"] = source.priority
        # Manifest approval is bounded; outside it this raw file remains useful
        # exploratory history but is not given approved-source priority.
        if source.source_type == "approved_yahoo":
            in_scope = frame["Date"].between(source.approved_from, source.approved_to)
            frame.loc[~in_scope, "_priority"] = 1
        by_symbol.setdefault(source.symbol, []).append((source, frame))

    all_rows = pd.concat([part for parts in by_symbol.values() for _, part in parts], ignore_index=True) if by_symbol else pd.DataFrame()
    if not all_rows.empty:
        keys = ["symbol", "Date"]
        value_counts = all_rows.groupby(keys, sort=False)[list(OHLCV)].nunique(dropna=False)
        conflicting_index = value_counts.index[value_counts.gt(1).any(axis=1)]
        if len(conflicting_index):
            conflict_keys = set(conflicting_index.tolist())
            conflict_rows = all_rows.set_index(keys).loc[list(conflict_keys)].reset_index()
            for (symbol, date), group in conflict_rows.groupby(keys, sort=True):
                conflicts.append({"symbol": symbol, "Date": date, "source_count": len(group),
                                  "sources": " | ".join(sorted(group["source_file"].unique())),
                                  "decision": "excluded_conflicting_date"})
            bad = pd.MultiIndex.from_frame(all_rows[keys]).isin(conflicting_index)
            all_rows = all_rows.loc[~bad]
        all_rows = all_rows.sort_values(["_priority", "Date"], kind="stable").drop_duplicates(keys, keep="first")
        for symbol, boundary in IDENTITY_STARTS.items():
            mask = all_rows["symbol"].eq(symbol) & all_rows["Date"].lt(boundary)
            all_rows = all_rows.loc[~mask]
        approved_scopes = {(s.symbol, s.source_label, s.approved_from, s.approved_to) for ss in by_symbol.values() for s, _ in ss if s.approved_from is not None}
        all_rows["approval_scope"] = "exploratory_unapproved"
        for symbol, path, start, end in approved_scopes:
            mask = all_rows["symbol"].eq(symbol) & all_rows["source_file"].eq(path) & all_rows["Date"].between(start, end)
            all_rows.loc[mask, "approval_scope"] = "within_manifest"
        bars = all_rows[["symbol", "Date", *OHLCV, "ohlc_status", "source_type", "source_file", "approval_scope"]]
    else:
        bars = pd.DataFrame(columns=["symbol", "Date", *OHLCV, "ohlc_status", "source_type", "source_file", "approval_scope"])
    if not bars.empty:
        bars = bars.sort_values(["symbol", "Date"]).reset_index(drop=True)
    return bars, pd.DataFrame(conflicts, columns=["symbol", "Date", "source_count", "sources", "decision"])


def daily_returns(bars: pd.DataFrame, symbols: Iterable[str] | None = None) -> pd.DataFrame:
    """Calculate close-to-close returns per exact security without filling gaps."""
    frame = bars.copy()
    if symbols is not None:
        frame = frame[frame["symbol"].isin([s.upper() for s in symbols])]
    frame = frame.sort_values(["symbol", "Date"])
    frame["return"] = frame.groupby("symbol", sort=False)["Close"].pct_change(fill_method=None)
    return frame


def normalize_closes(closes: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    """Normalize each symbol from its first available close, preserving NaNs."""
    first = closes.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else float("nan"))
    return closes.divide(first, axis="columns").multiply(base)


def return_correlation(returns: pd.DataFrame, min_overlap: int = 30) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pairwise return correlation and N matrix using only paired dates."""
    symbols = list(returns.columns)
    corr = pd.DataFrame(float("nan"), index=symbols, columns=symbols)
    counts = pd.DataFrame(0, index=symbols, columns=symbols, dtype="int64")
    for a in symbols:
        for b in symbols:
            if a == b:
                valid_count = int(returns[a].notna().sum())
                counts.loc[a, b] = valid_count
                if valid_count >= min_overlap:
                    corr.loc[a, b] = 1.0
                continue
            pair = returns[[a, b]].dropna()
            counts.loc[a, b] = len(pair)
            if len(pair) >= min_overlap:
                corr.loc[a, b] = pair[a].corr(pair[b])
    return corr, counts


def rolling_pair_correlation(a: pd.Series, b: pd.Series, window: int = 20) -> pd.Series:
    """Rolling correlation aligned on shared dates; incomplete windows remain NaN."""
    pair = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    result = pair["a"].rolling(window=window, min_periods=window).corr(pair["b"])
    return result.reindex(a.index)


def breadth_summary(bars: pd.DataFrame, symbols: Iterable[str]) -> tuple[dict[str, tuple[int, int]], pd.DataFrame]:
    """Descriptive breadth and trend metrics; denominators use available rows."""
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        frame = bars[bars["symbol"].eq(symbol)].sort_values("Date").copy()
        close = frame["Close"]
        ret = close.pct_change(fill_method=None)
        sma20, sma50 = close.rolling(20, min_periods=20).mean(), close.rolling(50, min_periods=50).mean()
        latest = close.last_valid_index()
        if latest is None:
            continue
        i = frame.index.get_loc(latest)
        rows.append({
            "symbol": symbol, "Date": frame.loc[latest, "Date"], "Close": close.loc[latest],
            "return_1d": ret.loc[latest], "return_5d": close.pct_change(5, fill_method=None).loc[latest],
            "return_20d": close.pct_change(20, fill_method=None).loc[latest],
            "return_60d": close.pct_change(60, fill_method=None).loc[latest],
            "above_sma20": close.loc[latest] > sma20.loc[latest] if pd.notna(sma20.loc[latest]) else pd.NA,
            "above_sma50": close.loc[latest] > sma50.loc[latest] if pd.notna(sma50.loc[latest]) else pd.NA,
            "sma20_above_sma50": sma20.loc[latest] > sma50.loc[latest] if pd.notna(sma20.loc[latest]) and pd.notna(sma50.loc[latest]) else pd.NA,
            "distance_sma20": close.loc[latest] / sma20.loc[latest] - 1 if pd.notna(sma20.loc[latest]) else float("nan"),
            "distance_sma50": close.loc[latest] / sma50.loc[latest] - 1 if pd.notna(sma50.loc[latest]) else float("nan"),
            "volatility_20d": ret.iloc[i - 19:i + 1].std() * (252 ** 0.5) if i >= 20 else float("nan"),
            "volume": frame.loc[latest, "Volume"],
            "volume_ratio_20d": frame.loc[latest, "Volume"] / frame["Volume"].iloc[i - 19:i + 1].mean()
                if i >= 19 and frame["Volume"].iloc[i - 19:i + 1].notna().sum() == 20 and pd.notna(frame.loc[latest, "Volume"]) else float("nan"),
        })
    metrics = pd.DataFrame(rows).set_index("symbol") if rows else pd.DataFrame()
    breadth: dict[str, tuple[int, int]] = {}
    for key in ("above_sma20", "above_sma50", "return_20d", "return_5d"):
        col = metrics[key] if not metrics.empty else pd.Series(dtype=float)
        valid = col.dropna()
        predicate = valid.gt(0) if key.startswith("return") else valid.astype(bool)
        breadth[key] = (int(predicate.sum()), len(valid))
    return breadth, metrics
