"""Small, fixed candle-only research selectors; none are approved live strategies."""

from __future__ import annotations

from typing import Mapping

import pandas as pd


def select_candidate(
    candidate_id: str,
    frames: Mapping[str, pd.DataFrame],
    as_of: pd.Timestamp,
    gate: object,
    top_n: int,
) -> list[str]:
    """Select eligible symbols using only rows at or before the signal date."""
    records: list[tuple[str, float]] = []
    for raw_symbol, frame in frames.items():
        symbol = str(raw_symbol).upper()
        if not gate.assess(symbol, as_of.date()).eligible:
            continue
        history = frame.loc[frame.index <= as_of]
        if history.empty or history.index[-1] != as_of:
            continue
        row = history.iloc[-1]
        score: float | None = None
        if candidate_id == "CANDIDATE_TREND20":
            if pd.notna(row.get("momentum_20")) and pd.notna(row.get("sma_20")) and row["momentum_20"] > 0 and row["close"] > row["sma_20"]:
                score = float(row["momentum_20"])
        elif candidate_id == "CANDIDATE_BREAKOUT20":
            if len(history) >= 21 and pd.notna(row.get("volume_ratio_20")):
                prior_high = pd.to_numeric(history["high"].iloc[-21:-1], errors="coerce").max()
                if pd.notna(prior_high) and row["close"] > prior_high and row["volume_ratio_20"] >= 1:
                    score = float(row["close"] / prior_high - 1)
        elif candidate_id == "CANDIDATE_MEANREV5":
            if len(history) >= 51 and pd.notna(row.get("sma_50")):
                ret5 = float(row["adjusted_close"] / history["adjusted_close"].iloc[-6] - 1)
                if ret5 < -0.05 and row["close"] > row["sma_50"]:
                    score = -ret5
        elif candidate_id == "CANDIDATE_REL_STRENGTH":
            if pd.notna(row.get("momentum_20")) and row["momentum_20"] > 0:
                score = float(row["momentum_20"])
        else:
            raise ValueError(f"Unknown candidate: {candidate_id}")
        if score is not None:
            records.append((symbol, score))
    records.sort(key=lambda item: (-item[1], item[0]))
    return [symbol for symbol, _ in records[:top_n]]
