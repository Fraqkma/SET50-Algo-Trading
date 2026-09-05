"""Entry point for the SET50 historical data pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.data.loader import load_market_data
from src.data.validator import validate_market_data
from src.data.yahoo_loader import download_set50_data


def _validate_raw_prices(project_root: str | Path | None = None) -> list[dict[str, object]]:
    root = Path(project_root).resolve() if project_root is not None else Path(__file__).resolve().parent
    raw_dir = root / "data" / "raw" / "prices"
    results: list[dict[str, object]] = []
    if not raw_dir.exists():
        return results

    for file_path in sorted(raw_dir.glob("*.parquet")):
        frame = load_market_data(file_path)
        validation = validate_market_data(frame, symbol=file_path.stem)
        results.append({"symbol": file_path.stem, "file": str(file_path), "validation": validation})
    return results


def main() -> int:
    """Command-line entry point for the data pipeline."""
    parser = argparse.ArgumentParser(description="SET50 historical data pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    data_parser = subparsers.add_parser("data", help="Data pipeline commands")
    data_subparsers = data_parser.add_subparsers(dest="data_command", required=True)

    download_parser = data_subparsers.add_parser("download", help="Download historical SET50 OHLCV data")
    download_parser.add_argument("--start", required=True, dest="start_date")
    download_parser.add_argument("--end", required=True, dest="end_date")
    download_parser.add_argument("--force", action="store_true")

    validate_parser = data_subparsers.add_parser("validate", help="Validate all raw price files")

    args = parser.parse_args()

    if args.command == "data" and args.data_command == "download":
        report = download_set50_data(args.start_date, args.end_date, force=args.force)
        print(f"Requested symbols: {len(report['requested_symbols'])}")
        print(f"Downloaded: {report['successful_symbols']}")
        print(f"Failed: {report['failed_symbols']}")
        return 0

    if args.command == "data" and args.data_command == "validate":
        results = _validate_raw_prices()
        for result in results:
            payload = result["validation"]
            print(f"{result['symbol']}: valid={payload['is_valid']} issues={payload['issues']}")
        return 0

    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())