"""Generate a deterministic, read-only SET50 intraday-source research report.

No credentials, network probes, collector, or market-data files are used.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
AUDIT_DATE = "2026-09-14"
SYMBOLS = ["BDMS", "BGRIM", "CENTEL", "COM7", "GLOBAL", "GULF", "HMPRO", "IVL", "KKP", "KTB", "LH", "MRDIYT", "MTC", "OSP", "PTTGC", "RATCH", "SCGP", "THAI", "TIDLOR", "TOP"]

SOURCES = [
    {"source": "SET Intraday Trading Data (Tick Data) / SMART Marketplace", "provider_type": "OFFICIAL", "set_coverage": "VERIFIED_SET", "set50_probe_status": "EXPECTED_ALL_SET_SYMBOLS_SUBJECT_TO_LICENSE", "one_min": "DERIVE_FROM_TICKS", "five_min": "DERIVE_FROM_TICKS", "fifteen_min": "DERIVE_FROM_TICKS", "tick": "YES", "bid_ask": "YES", "depth": "UNKNOWN_BID_OFFER_LEVELS_REQUIRE_FILE_SPEC", "historical_lookback": "Since Sep 2012 for SET tick data", "timeliness": "Historical by request; EOD subscription; real-time/delay snapshot product separately", "access": "Authenticated download/API; paid subscription/request", "free_tier": "NO_PUBLIC_FREE_TIER", "rate_limits": "UNKNOWN_UNTIL_PRODUCT_TERMS", "price_semantics": "RAW_TICK_SEMANTICS_TO_CONFIRM", "timezone": "SET exchange timestamps; exact timezone/file convention must be confirmed", "automation": "YES_FOR_LICENSED_API_DOWNLOAD", "license": "Personal/internal use only; no redistribution unless separately licensed", "classification": "A_PRIMARY_INTRADAY_COLLECTION", "recommended_use": "Primary source for bar construction, execution/liquidity and quote diagnostics"},
    {"source": "EODHD", "provider_type": "THIRD_PARTY", "set_coverage": "VERIFIED_BK_EXCHANGE_LISTING", "set50_probe_status": "PER_SYMBOL_INTRADAY_COVERAGE_UNVERIFIED", "one_min": "POSSIBLE_TICKER_DEPENDENT", "five_min": "POSSIBLE_TICKER_DEPENDENT", "fifteen_min": "NOT_DOCUMENTED_FOR_BK", "tick": "API_PRODUCT_EXISTS_BUT_BK_SCOPE_UNVERIFIED", "bid_ask": "NOT_VERIFIED_FOR_BK", "depth": "NO_EVIDENCE", "historical_lookback": "Ticker/exchange dependent; 5m often since Oct 2020 for non-US markets", "timeliness": "Live/delayed product varies", "access": "REST/API token", "free_tier": "EOD only, 20 calls/day; intraday subscription required", "rate_limits": "1,000 requests/minute; intraday consumes 5 calls", "price_semantics": "ADJUSTMENT_SEMANTICS_REQUIRE_CONFIRMATION", "timezone": "BK page documents Asia/Bangkok for exchange metadata", "automation": "YES_SUBJECT_TO_PLAN_TERMS", "license": "Terms/redistribution must be verified before use", "classification": "C_CROSS_CHECK_ONLY", "recommended_use": "Future limited coverage probe and bar cross-check, never assumed primary"},
    {"source": "Twelve Data", "provider_type": "THIRD_PARTY", "set_coverage": "THAILAND_MARKET_CLAIMED; PER_SYMBOL_VERIFY", "set50_probe_status": "UNVERIFIED", "one_min": "YES_API_INTERVAL; INSTRUMENT_AVAILABILITY_VARIES", "five_min": "YES_API_INTERVAL; INSTRUMENT_AVAILABILITY_VARIES", "fifteen_min": "YES_API_INTERVAL; INSTRUMENT_AVAILABILITY_VARIES", "tick": "NO_DOCUMENTED_SET_TICK_FEED", "bid_ask": "QUOTE_ENDPOINT_NOT_EQUIVALENT_TO_HISTORICAL_BBO", "depth": "NO_EVIDENCE", "historical_lookback": "Few months to years by symbol/interval", "timeliness": "Real-time/delayed depends on instrument and plan", "access": "REST and WebSocket with API key", "free_tier": "LIMITED_CREDITS", "rate_limits": "PLAN/CREDIT_DEPENDENT", "price_semantics": "Intraday documented as unadjusted", "timezone": "Intraday timezone parameter documented; actual exchange field requires probe", "automation": "YES_SUBJECT_TO_PLAN_TERMS", "license": "Plan/data-rights review required", "classification": "C_CROSS_CHECK_ONLY", "recommended_use": "Small lawful metadata and coverage probe after account approval"},
    {"source": "Yahoo Finance / yfinance", "provider_type": "THIRD_PARTY", "set_coverage": "DAILY_BK_EXISTING_PIPELINE_ONLY", "set50_probe_status": "INTRADAY_UNVERIFIED_AND_UNLICENSED_FOR_COLLECTION", "one_min": "UNRELIABLE_UNSUPPORTED_FOR_RESEARCH_COLLECTION", "five_min": "UNRELIABLE_UNSUPPORTED_FOR_RESEARCH_COLLECTION", "fifteen_min": "UNRELIABLE_UNSUPPORTED_FOR_RESEARCH_COLLECTION", "tick": "NO", "bid_ask": "NO_RELIABLE_HISTORICAL_BBO", "depth": "NO", "historical_lookback": "Not guaranteed", "timeliness": "Variable/delayed", "access": "Web interface; documented CSV download requires Gold", "free_tier": "Viewing may be available; no approved collection tier", "rate_limits": "UNDOCUMENTED", "price_semantics": "VARIABLE; NOT_SUFFICIENTLY_DOCUMENTED_FOR_EXECUTION", "timezone": "NOT_SUFFICIENTLY_DOCUMENTED", "automation": "NOT_RECOMMENDED", "license": "Instrument-specific licensing restrictions", "classification": "D_NOT_SUITABLE", "recommended_use": "Do not use for continuous intraday collection"},
    {"source": "TradingView", "provider_type": "THIRD_PARTY_DISPLAY/BROKER_ROUTE", "set_coverage": "SET_DISPLAY_AND_BROKER_ENTITLEMENT_EVIDENCE", "set50_probe_status": "SYMBOL_AND_ENTITLEMENT_DEPENDENT", "one_min": "DISPLAY_AVAILABLE_IF_ENTITLED_NOT_API_PROMISED", "five_min": "DISPLAY_AVAILABLE_IF_ENTITLED_NOT_API_PROMISED", "fifteen_min": "DISPLAY_AVAILABLE_IF_ENTITLED_NOT_API_PROMISED", "tick": "NO_PUBLIC_DATA_EXPORT_API_EVIDENCE", "bid_ask": "NOT_FOR_RESEARCH_FEED", "depth": "NOT_FOR_RESEARCH_FEED", "historical_lookback": "PLAN/EXCHANGE_DEPENDENT", "timeliness": "Real-time requires exchange/broker entitlement", "access": "Web interface/broker integration", "free_tier": "Delayed display may be available", "rate_limits": "NOT_APPLICABLE_NO_APPROVED_COLLECTION_API", "price_semantics": "DISPLAY_SEMANTICS_INSUFFICIENT", "timezone": "CHART_SETTING_NOT_SUFFICIENT", "automation": "NO_APPROVED_AUTOMATION_ROUTE", "license": "Display agreement; no redistribution", "classification": "D_NOT_SUITABLE", "recommended_use": "Manual visual cross-check only"},
    {"source": "Alpha Vantage", "provider_type": "THIRD_PARTY", "set_coverage": "GLOBAL_CLAIM_ONLY", "set50_probe_status": "UNVERIFIED", "one_min": "API_INTERVAL_BUT_SET_COVERAGE_UNVERIFIED", "five_min": "API_INTERVAL_BUT_SET_COVERAGE_UNVERIFIED", "fifteen_min": "API_INTERVAL_BUT_SET_COVERAGE_UNVERIFIED", "tick": "NO_SET_EVIDENCE", "bid_ask": "US_FOCUSED_DOCUMENTATION", "depth": "NO", "historical_lookback": "Provider claim varies by symbol/plan", "timeliness": "Plan/symbol dependent", "access": "REST API key", "free_tier": "FREE_KEY_LIMITED", "rate_limits": "PLAN_DEPENDENT", "price_semantics": "Raw or adjusted parameter, if coverage exists", "timezone": "SET_CONVENTION_UNVERIFIED", "automation": "YES_IF_COVERAGE_AND_TERMS_CONFIRMED", "license": "Plan terms required", "classification": "D_NOT_SUITABLE", "recommended_use": "No SET collection absent documented per-symbol coverage"},
    {"source": "Polygon", "provider_type": "THIRD_PARTY", "set_coverage": "NOT_SUPPORTED_BY_DOCUMENTED_STOCK_PRODUCT", "set50_probe_status": "NOT_APPLICABLE", "one_min": "US_STOCKS_ONLY_DOCUMENTATION", "five_min": "US_STOCKS_ONLY_DOCUMENTATION", "fifteen_min": "US_STOCKS_ONLY_DOCUMENTATION", "tick": "US_ONLY_DOCUMENTATION", "bid_ask": "US_ONLY_DOCUMENTATION", "depth": "US_ONLY_DOCUMENTATION", "historical_lookback": "Not relevant for SET", "timeliness": "Not relevant for SET", "access": "REST/WebSocket", "free_tier": "NOT_RELEVANT", "rate_limits": "NOT_RELEVANT", "price_semantics": "Not relevant for SET", "timezone": "US ET documentation", "automation": "NOT_FOR_SET", "license": "Not relevant for SET", "classification": "D_NOT_SUITABLE", "recommended_use": "Exclude"},
    {"source": "Tiingo", "provider_type": "THIRD_PARTY", "set_coverage": "NOT_SUPPORTED_BY_DOCUMENTED_EQUITY_UNIVERSE", "set50_probe_status": "NOT_APPLICABLE", "one_min": "NO_SET_EVIDENCE", "five_min": "NO_SET_EVIDENCE", "fifteen_min": "NO_SET_EVIDENCE", "tick": "NO_SET_EVIDENCE", "bid_ask": "US/CRYPTO_PRODUCT_FOCUSED", "depth": "NO_SET_EVIDENCE", "historical_lookback": "Not relevant for SET", "timeliness": "Not relevant for SET", "access": "REST/WebSocket token", "free_tier": "NOT_RELEVANT", "rate_limits": "ACCOUNT_DEPENDENT", "price_semantics": "Not relevant for SET", "timezone": "Not relevant for SET", "automation": "NOT_FOR_SET", "license": "Internal/personal use; no redistribution", "classification": "D_NOT_SUITABLE", "recommended_use": "Exclude"},
    {"source": "Finnhub", "provider_type": "THIRD_PARTY", "set_coverage": "PRESS_RELEASE_SYMBOLS_SEEN; MARKET_DATA_COVERAGE_UNVERIFIED", "set50_probe_status": "UNVERIFIED", "one_min": "UNVERIFIED", "five_min": "UNVERIFIED", "fifteen_min": "UNVERIFIED", "tick": "UNVERIFIED", "bid_ask": "UNVERIFIED", "depth": "UNVERIFIED", "historical_lookback": "UNVERIFIED", "timeliness": "UNVERIFIED", "access": "API account", "free_tier": "PLAN_DEPENDENT", "rate_limits": "PLAN_DEPENDENT", "price_semantics": "UNVERIFIED", "timezone": "UNVERIFIED", "automation": "DO_NOT_USE_UNTIL_VENDOR_CONFIRMS_SET_FEED", "license": "PLAN TERMS REQUIRED", "classification": "D_NOT_SUITABLE", "recommended_use": "Exclude pending explicit vendor confirmation"},
    {"source": "Stooq", "provider_type": "THIRD_PARTY", "set_coverage": "UNVERIFIED", "set50_probe_status": "UNVERIFIED", "one_min": "NO_EVIDENCE", "five_min": "NO_EVIDENCE", "fifteen_min": "NO_EVIDENCE", "tick": "NO", "bid_ask": "NO", "depth": "NO", "historical_lookback": "UNVERIFIED", "timeliness": "NOT_REALTIME", "access": "File/web interface", "free_tier": "PUBLIC_ACCESS_NOT_APPROVAL", "rate_limits": "UNVERIFIED", "price_semantics": "UNVERIFIED", "timezone": "UNVERIFIED", "automation": "NOT_RECOMMENDED", "license": "UNVERIFIED", "classification": "D_NOT_SUITABLE", "recommended_use": "Exclude"},
]


def storage_rows() -> list[dict]:
    # 390 possible active minutes/session, 21 sessions/month, 252/year; no bars
    # are fabricated for gaps. 100 compressed-columnar bytes/observed bar is a
    # planning assumption, not a provider claim.
    records = []
    bars_per_day = {"1m": 390, "5m": 78, "15m": 26}
    periods = {"1_month": 21, "3_months": 63, "1_year": 252}
    for symbols in (20, 50):
        for frequency, bars in bars_per_day.items():
            for retention, days in periods.items():
                rows = symbols * bars * days
                records.append({"symbols": symbols, "frequency": frequency, "retention": retention, "estimated_observed_rows": rows, "estimated_compressed_storage_mb": round(rows * 100 / 1_000_000, 2), "assumption": "100 bytes/observed bar; no synthetic gap bars"})
    return records


def payload() -> dict:
    return {
        "status": "READ_ONLY_INTRADAY_SOURCE_RESEARCH",
        "audit_date": AUDIT_DATE,
        "probe_universe": SYMBOLS,
        "network_probes_performed": False,
        "sources": SOURCES,
        "storage_estimates": storage_rows(),
        "minimum_practical_dataset": {"universe": "Current 20 approved daily symbols initially", "resolution": "5-minute OHLCV from licensed official tick data, plus available best bid/offer snapshots", "retention": "At least 12 months; retain raw licensed daily files where permitted", "rationale": "5-minute bars materially improve liquidity/timing diagnostics at lower operational volume than 1-minute bars; raw ticks preserve optional later aggregation."},
        "future_schema": [
            {"field": "timestamp", "availability": "REQUIRED"}, {"field": "symbol", "availability": "REQUIRED"}, {"field": "open", "availability": "BAR_ONLY"}, {"field": "high", "availability": "BAR_ONLY"}, {"field": "low", "availability": "BAR_ONLY"}, {"field": "close", "availability": "BAR_ONLY"}, {"field": "volume", "availability": "SOURCE_DEPENDENT"}, {"field": "turnover", "availability": "SOURCE_DEPENDENT"}, {"field": "vwap", "availability": "DERIVED_OR_SOURCE_DEPENDENT"}, {"field": "bid", "availability": "QUOTE_SOURCE_DEPENDENT"}, {"field": "ask", "availability": "QUOTE_SOURCE_DEPENDENT"}, {"field": "bid_size", "availability": "QUOTE_SOURCE_DEPENDENT"}, {"field": "ask_size", "availability": "QUOTE_SOURCE_DEPENDENT"}, {"field": "source", "availability": "REQUIRED"}, {"field": "retrieved_at", "availability": "REQUIRED"}, {"field": "timezone", "availability": "REQUIRED"}, {"field": "adjustment_status", "availability": "REQUIRED"}
        ],
        "validation_checklist": ["duplicate timestamps", "missing bars without fabricated sessions", "out-of-session bars", "invalid OHLC", "zero/negative volume anomalies", "timezone errors", "symbol mapping", "corporate-action boundaries", "delayed-feed identification", "stale quote detection", "abnormal spreads", "source outages"],
        "collector_ready": False,
        "daily_dataset_modified": False,
        "market_data_downloaded": False,
    }


def write_outputs(data: dict) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "intraday_data_source_research.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    source_fields = list(data["sources"][0])
    with (REPORT_DIR / "intraday_data_source_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=source_fields)
        writer.writeheader()
        writer.writerows(data["sources"])
    storage_fields = list(data["storage_estimates"][0])
    with (REPORT_DIR / "intraday_data_storage_estimate.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=storage_fields)
        writer.writeheader()
        writer.writerows(data["storage_estimates"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = payload()
    if args.write:
        write_outputs(data)
    print(json.dumps({"sources": len(data["sources"]), "probe_symbols": len(data["probe_universe"]), "collector_ready": data["collector_ready"]}, indent=2))


if __name__ == "__main__":
    main()
