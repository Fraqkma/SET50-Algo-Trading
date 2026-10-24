"""Leakage-safe feature engineering for explicitly approved market data.

The feature layer is deliberately narrower than the research-data loader. A
caller must provide explicit PIT membership and identity context; this module
never reconstructs historical membership or security continuity.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd


STATUS_MAP = {
    "USE": "USE",
    "USE_WITH_FLAG": "USE_WITH_FLAG",
    "SOURCE_NEEDED": "SOURCE_NEEDED",
    "NEEDS_REVIEW": "NEEDS_REVIEW",
    "APPROVED": "USE",
    "APPROVED_WITH_KNOWN_GAP": "USE_WITH_FLAG",
    "REJECTED": "NEEDS_REVIEW",
}
CALCULABLE_STATUSES = {"USE", "USE_WITH_FLAG"}

ALLOWED_INPUT_COLUMNS = {
    "open", "high", "low", "close", "adjusted_close", "adj_close", "volume",
    "dividends", "stock_splits", "data_timestamp", "feature_timestamp",
    "information_cutoff", "security_id", "pit_membership", "data_status",
    "validity_status", "identity_status", "source_data", "corporate_action_metadata_status",
}
FORBIDDEN_INPUT_COLUMNS = {
    "target", "label", "future_return", "future_returns", "label_timestamp",
    "signal_timestamp", "execution_timestamp",
}
UNRESOLVED_IDENTITY_STATUSES = {
    "UNRESOLVED",
    "NEEDS_REVIEW",
    "UNKNOWN",
    "MAPPING_UNAVAILABLE",
    "REJECTED",
    "UNSUPPORTED_PREDECESSOR_SUCCESSOR",
}


@dataclass(frozen=True)
class FeatureContext:
    """Required point-in-time and provenance context for one feature frame."""

    security_id: str
    pit_membership: Any
    identity_status: Any
    data_status: Any
    information_cutoff: Any
    data_timestamp: Any | None = None
    feature_timestamp: Any | None = None
    source_data: Any | None = None
    validity_status: Any = "VALID"
    corporate_action_metadata_status: Any | None = None

    @classmethod
    def from_mapping(cls, values: Mapping[str, Any]) -> "FeatureContext":
        allowed = {
            "security_id", "pit_membership", "identity_status", "data_status",
            "information_cutoff", "data_timestamp", "feature_timestamp",
            "source_data", "validity_status", "corporate_action_metadata_status",
        }
        unknown = set(values) - allowed
        if unknown:
            raise ValueError(f"Unsupported FeatureContext fields: {sorted(unknown)}")
        required = {"security_id", "pit_membership", "identity_status", "data_status", "information_cutoff"}
        missing = required - set(values)
        if missing:
            raise ValueError(f"FeatureContext is missing required fields: {sorted(missing)}")
        return cls(**{key: values[key] for key in values})


def build_features(
    dataframe: pd.DataFrame,
    *,
    context: FeatureContext | Mapping[str, Any] | None = None,
    momentum_window: int = 20,
    short_window: int = 20,
    long_window: int = 50,
    volatility_window: int = 20,
    volume_window: int = 20,
) -> pd.DataFrame:
    """Build causal daily features from one explicitly eligible symbol."""
    if dataframe is None:
        raise ValueError("Input dataframe cannot be None.")
    feature_context = _coerce_context(context)
    windows = {
        "momentum_window": momentum_window, "short_window": short_window,
        "long_window": long_window, "volatility_window": volatility_window,
        "volume_window": volume_window,
    }
    if any(not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in windows.values()):
        raise ValueError("Feature windows must be positive integers.")

    frame = _prepare_frame(dataframe)
    index = frame.index
    statuses = _status_series(feature_context.data_status, index)
    pit_membership = _context_series(feature_context.pit_membership, index, "pit_membership")
    if _scalar_false_pit_membership(pit_membership):
        raise ValueError("PIT membership context does not confirm eligibility.")
    identity = _context_series(feature_context.identity_status, index, "identity_status")
    if identity.isna().any() or identity.astype(str).str.strip().eq("").any():
        raise ValueError("Identity context is required for every feature row.")
    identity_unresolved = identity.astype(str).str.strip().str.upper().isin(UNRESOLVED_IDENTITY_STATUSES)

    data_timestamp = _timestamp_series(
        feature_context.data_timestamp if feature_context.data_timestamp is not None else index,
        index, "data_timestamp",
    )
    feature_timestamp = _timestamp_series(
        feature_context.feature_timestamp if feature_context.feature_timestamp is not None else data_timestamp,
        index, "feature_timestamp",
    )
    information_cutoff = _timestamp_series(feature_context.information_cutoff, index, "information_cutoff")
    if ((data_timestamp > feature_timestamp) | (feature_timestamp > information_cutoff)).any():
        raise ValueError("Feature timestamps violate data_timestamp <= feature_timestamp <= information_cutoff.")

    columns = {str(column): str(column) for column in frame.columns}
    adjusted_close_column = columns.get("adjusted_close") or columns.get("adj_close")
    if adjusted_close_column is None:
        raise ValueError("Feature input must contain Adjusted Close; raw Close is not an approved substitute.")
    adjusted_close = pd.to_numeric(frame[adjusted_close_column], errors="coerce")
    raw_close = pd.to_numeric(frame[columns["close"]], errors="coerce") if "close" in columns else None
    calculable = statuses.isin(CALCULABLE_STATUSES)
    if raw_close is not None and (raw_close.isna() & calculable).any():
        raise ValueError("Close contains missing or non-numeric values; repair data before feature engineering.")
    if (adjusted_close.isna() & calculable).any():
        raise ValueError("Adjusted Close contains missing or non-numeric values; repair data before feature engineering.")

    volume_column = columns.get("volume")
    volume = None
    if volume_column is not None:
        volume = pd.to_numeric(frame[volume_column], errors="coerce")
        if (volume.isna() & calculable).any():
            raise ValueError("Volume contains missing or non-numeric values; do not fabricate volume.")

    features = frame.copy(deep=True)
    features["daily_return"] = adjusted_close.pct_change()
    features[f"momentum_{momentum_window}"] = adjusted_close.pct_change(periods=momentum_window)
    features[f"sma_{short_window}"] = adjusted_close.rolling(short_window, min_periods=short_window).mean()
    features[f"sma_{long_window}"] = adjusted_close.rolling(long_window, min_periods=long_window).mean()
    features[f"trend_{short_window}_{long_window}"] = (
        features[f"sma_{short_window}"] / features[f"sma_{long_window}"] - 1.0
    )
    features[f"volatility_{volatility_window}"] = features["daily_return"].rolling(
        volatility_window, min_periods=volatility_window
    ).std(ddof=0)
    feature_columns = [
        "daily_return", f"momentum_{momentum_window}", f"sma_{short_window}",
        f"sma_{long_window}", f"trend_{short_window}_{long_window}",
        f"volatility_{volatility_window}",
    ]
    if volume is not None:
        volume_mean_name = f"volume_sma_{volume_window}"
        features[volume_mean_name] = volume.rolling(volume_window, min_periods=volume_window).mean()
        features[f"volume_ratio_{volume_window}"] = volume / features[volume_mean_name]
        feature_columns.extend([volume_mean_name, f"volume_ratio_{volume_window}"])

    ineligible = pit_membership.astype(str).str.strip().str.upper().isin(
        {"FALSE", "0", "NO", "INELIGIBLE", "EXCLUDED"}
    )
    unavailable = ~calculable | ineligible | identity_unresolved
    if unavailable.any():
        features.loc[unavailable, feature_columns] = float("nan")

    action_status = feature_context.corporate_action_metadata_status
    if action_status is None:
        action_status = "AVAILABLE" if {"dividends", "stock_splits"}.intersection(frame.columns) else "UNAVAILABLE"
    metadata = {
        "security_id": feature_context.security_id,
        "pit_membership": pit_membership,
        "identity_status": identity,
        "data_status": statuses,
        "validity_status": _validity_series(statuses, pit_membership, identity_unresolved),
        "data_timestamp": data_timestamp,
        "feature_timestamp": feature_timestamp,
        "information_cutoff": information_cutoff,
        "source_data": _context_series(
            feature_context.source_data if feature_context.source_data is not None else "unspecified_input_source",
            index,
            "source_data",
        ),
        "price_representation": "adjusted_close",
        "volume_representation": "reported_raw" if volume is not None else "unavailable",
        "corporate_action_metadata_status": action_status,
    }
    for name, value in metadata.items():
        features[name] = value
    features["missing_data_status"] = _missing_data_status(
        features, feature_columns, statuses, identity_unresolved, ineligible
    )
    return features


def _coerce_context(context: FeatureContext | Mapping[str, Any] | None) -> FeatureContext:
    if context is None:
        raise ValueError("FeatureContext is required; PIT membership and identity context cannot be inferred.")
    if isinstance(context, FeatureContext):
        result = context
    elif isinstance(context, Mapping):
        result = FeatureContext.from_mapping(context)
    else:
        raise TypeError("context must be a FeatureContext or mapping.")
    if not str(result.security_id).strip():
        raise ValueError("FeatureContext.security_id is required.")
    return result


def _prepare_frame(dataframe: pd.DataFrame) -> pd.DataFrame:
    frame = dataframe.copy(deep=True)
    if "Date" in frame.columns and not isinstance(frame.index, pd.DatetimeIndex):
        frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
        frame = frame.set_index("Date")
    elif not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index, errors="raise")
    if frame.index.has_duplicates:
        raise ValueError("Feature input contains duplicate dates; no silent deduplication is allowed.")
    frame = frame.sort_index()
    canonical_names = {
        original: str(original).strip().lower().replace(" ", "_")
        for original in frame.columns
    }
    frame = frame.rename(columns=canonical_names)
    normalized_columns = set(frame.columns)
    forbidden = normalized_columns.intersection(FORBIDDEN_INPUT_COLUMNS)
    unknown = normalized_columns - ALLOWED_INPUT_COLUMNS
    if forbidden or unknown:
        names = sorted(forbidden or unknown)
        raise ValueError(f"Feature input contains unsupported target/label or schema columns: {names}")
    if "adj_close" in frame.columns and "adjusted_close" in frame.columns:
        raise ValueError("Feature input must provide one Adjusted Close representation, not both aliases.")
    if "adj_close" in frame.columns:
        frame = frame.rename(columns={"adj_close": "adjusted_close"})
    if frame.empty:
        raise ValueError("Feature input cannot be empty.")
    return frame


def _context_series(value: Any, index: pd.DatetimeIndex, name: str) -> pd.Series:
    if isinstance(value, pd.Series):
        if len(value) != len(index):
            raise ValueError(f"FeatureContext.{name} length does not match feature rows.")
        return pd.Series(value.to_numpy(copy=True), index=index, name=name)
    if isinstance(value, (list, tuple, pd.Index)):
        if len(value) != len(index):
            raise ValueError(f"FeatureContext.{name} length does not match feature rows.")
        return pd.Series(list(value), index=index, name=name)
    return pd.Series([value] * len(index), index=index, name=name)


def _timestamp_series(value: Any, index: pd.DatetimeIndex, name: str) -> pd.Series:
    series = _context_series(value, index, name)
    result = pd.to_datetime(series, errors="coerce")
    if result.isna().any():
        raise ValueError(f"FeatureContext.{name} contains invalid timestamps.")
    return result


def _status_series(value: Any, index: pd.DatetimeIndex) -> pd.Series:
    raw = _context_series(value, index, "data_status").astype(str).str.strip().str.upper()
    normalized = raw.map(STATUS_MAP)
    if normalized.isna().any():
        unknown = sorted(raw[normalized.isna()].unique())
        raise ValueError(f"Unsupported data status values: {unknown}")
    return normalized


def _scalar_false_pit_membership(series: pd.Series) -> bool:
    if len(series) == 0:
        return True
    values = series.astype(str).str.strip().str.upper()
    return values.isin({"FALSE", "0", "NO", "INELIGIBLE", "EXCLUDED"}).all()


def _validity_series(
    statuses: pd.Series,
    pit_membership: pd.Series,
    identity_unresolved: pd.Series,
) -> pd.Series:
    pit_invalid = pit_membership.astype(str).str.strip().str.upper().isin(
        {"FALSE", "0", "NO", "INELIGIBLE", "EXCLUDED"}
    )
    result = pd.Series("VALID", index=statuses.index)
    result.loc[statuses == "USE_WITH_FLAG"] = "FLAGGED"
    result.loc[statuses == "SOURCE_NEEDED"] = "SOURCE_NEEDED"
    result.loc[statuses == "NEEDS_REVIEW"] = "NEEDS_REVIEW"
    result.loc[pit_invalid] = "INELIGIBLE"
    result.loc[identity_unresolved] = "IDENTITY_UNRESOLVED"
    return result


def _missing_data_status(
    features: pd.DataFrame,
    feature_columns: list[str],
    statuses: pd.Series,
    identity_unresolved: pd.Series,
    ineligible: pd.Series,
) -> pd.Series:
    result = pd.Series("NONE", index=features.index)
    result.loc[statuses == "SOURCE_NEEDED"] = "SOURCE_NEEDED"
    result.loc[statuses == "NEEDS_REVIEW"] = "NEEDS_REVIEW"
    result.loc[ineligible] = "INELIGIBLE"
    result.loc[identity_unresolved] = "IDENTITY_UNRESOLVED"
    warmup = features[feature_columns].isna().any(axis=1)
    result.loc[(result == "NONE") & warmup] = "WARMUP_OR_UNAVAILABLE"
    return result
