"""Windows-safe, market-data-only daily Settrade pilot orchestrator."""

from __future__ import annotations

import argparse
import json
import logging
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.settrade import SettradeClient, SettradeConfig  # noqa: E402
from src.data.settrade.automation import (  # noqa: E402
    AlreadyRunningError,
    SingleInstanceLock,
    atomic_json_write,
    classify_market_window,
    request_stop,
    stop_requested,
    THAILAND,
)
from src.data.settrade.disk import check_disk  # noqa: E402

LOCK_PATH = ROOT / ".settrade-runtime" / "daily.lock"
STOP_PATH = ROOT / ".settrade-runtime" / "daily.stop"
LOG_DIR = ROOT / "logs" / "settrade"
SUMMARY_DIR = ROOT / "reports" / "runtime"
LOGGER = logging.getLogger("settrade_daily")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="run one bounded collection cycle")
    parser.add_argument("--dry-run", action="store_true", help="perform lifecycle checks without API collection")
    parser.add_argument("--max-cycles", type=int, default=0, help="test limit; zero means until session close")
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--request-stop", action="store_true", help="request another runner to stop gracefully")
    parser.add_argument("--now", help="test-only ISO timestamp; never used by Task Scheduler")
    parser.add_argument("--market-status", help="test-only API market status override")
    return parser


def _now(value: str | None) -> datetime:
    if value:
        parsed = datetime.fromisoformat(value)
        return parsed.replace(tzinfo=parsed.tzinfo or THAILAND)
    return datetime.now(timezone.utc)


def _configure_logging(now: datetime) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    filename = LOG_DIR / f"daily-{now.astimezone(THAILAND):%Y-%m-%d}.log"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", handlers=[logging.FileHandler(filename, encoding="utf-8"), logging.StreamHandler(sys.stdout)])


def _readiness() -> dict[str, Any]:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_settrade_collection_readiness.py")], cwd=ROOT, capture_output=True, text=True, timeout=180)
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError:
        result = {"status": "NOT_READY", "reasons": ["readiness output was not valid JSON"]}
    result["returncode"] = completed.returncode
    return result


def _market_status() -> str | None:
    config = SettradeConfig.from_env(ROOT / ".env")
    client = SettradeClient(config, market_rps=3)
    client.authenticate()
    payload = client.quote("PTT")
    return str(payload.get("marketStatus") or payload.get("market_status") or "") or None


def _collector_cycle(rotation_generation: int = 0) -> tuple[bool, dict[str, Any]]:
    command = [sys.executable, str(ROOT / "scripts" / "run_settrade_collector.py"), "--universe", "current_set50", "--mode", "combined", "--once", "--rotation-generation", str(rotation_generation)]
    process = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        output, error_output = process.communicate(timeout=900)
    except subprocess.TimeoutExpired:
        LOGGER.error("collector cycle exceeded timeout; requesting graceful interruption")
        process.send_signal(signal.SIGINT)
        try:
            output, error_output = process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            LOGGER.error("collector did not stop after graceful interruption; terminating process")
            process.terminate()
            output, error_output = process.communicate(timeout=30)
        return False, {"status": "FAILURE", "error": "collector timeout", "output": output[-1000:]}
    if error_output:
        LOGGER.info("collector diagnostics=%s", error_output[-1000:].replace("\n", " "))
    LOGGER.info("collector cycle exit=%s", process.returncode)
    try:
        result = json.loads(output)
        if not isinstance(result, dict):
            raise ValueError("collector JSON result must be an object")
    except (json.JSONDecodeError, TypeError, ValueError):
        result = {"status": "FAILURE", "error": "collector output was not valid JSON"}
    return process.returncode == 0 and result.get("status", "SUCCESS") != "FAILURE", result


def _health() -> dict[str, Any]:
    completed = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_settrade_collector_health.py")], cwd=ROOT, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"status": "FAILED", "error": "health output was not valid JSON"}


def _sleep(seconds: int, stop_path: Path = STOP_PATH) -> bool:
    for _ in range(max(0, seconds)):
        if stop_requested(stop_path, __import__("os").getpid()):
            return True
        time.sleep(1)
    return False


def run(args: argparse.Namespace) -> int:
    start = _now(args.now)
    _configure_logging(start)
    if args.request_stop:
        requested = request_stop(LOCK_PATH, STOP_PATH)
        print("STOP_REQUESTED" if requested else "NO_ACTIVE_RUNNER")
        return 0

    summary: dict[str, Any] = {
        "date": start.astimezone(THAILAND).date().isoformat(), "timezone": "Asia/Bangkok", "start_time": start.isoformat(),
        "end_time": None, "runtime_seconds": None, "market_day": False, "startup_status": "STARTING", "shutdown_status": None,
        "symbols_expected": 50, "symbols_with_1m_data": 0, "one_minute_rows_written": 0, "bbo_events_written": 0,
        "rotation_generations": 0, "api_requests": 0, "retries": 0, "reconnects": 0, "rate_limit_errors": 0,
        "validation_errors": 0, "conflicts": 0, "disk_free_start": None, "disk_free_end": None, "orders_placed": 0,
        "health_checks": 0,
        "candle_status": "NOT_RUN",
    }
    lock = SingleInstanceLock(LOCK_PATH)
    try:
        lock.acquire()
    except AlreadyRunningError:
        LOGGER.warning("ALREADY_RUNNING")
        summary["startup_status"] = "ALREADY_RUNNING"
        summary["shutdown_status"] = "NOT_STARTED"
        return 2

    stop_event = False

    def signal_stop(signum: int, _frame: Any) -> None:
        nonlocal stop_event
        stop_event = True
        LOGGER.info("graceful stop requested signal=%s", signum)

    signal.signal(signal.SIGINT, signal_stop)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, signal_stop)
    try:
        disk = check_disk(ROOT / "data" / "pilot" / "settrade")
        summary["disk_free_start"] = disk.free_bytes
        if disk.state == "CRITICAL":
            summary.update(startup_status="DISK_CRITICAL", shutdown_status="DISK_CRITICAL")
            return 1
        readiness = {"status": "READY"} if args.dry_run else _readiness()
        summary["startup_status"] = readiness.get("status", "NOT_READY")
        if readiness.get("status") != "READY":
            LOGGER.error("readiness failed reasons=%s", readiness.get("reasons", []))
            summary["shutdown_status"] = "NOT_READY"
            return 1

        status = args.market_status if args.market_status is not None else (None if args.dry_run else _market_status())
        window = classify_market_window(_now(args.now), status)
        summary["market_day"] = window.market_day
        LOGGER.info("market window state=%s reason=%s", window.state, window.reason)
        if not window.market_day or window.state == "CLOSED":
            summary["shutdown_status"] = f"MARKET_CLOSED/{window.reason}"
            return 0
        if not window.collecting and args.once:
            summary["shutdown_status"] = f"WAITING/{window.state}"
            return 0

        cycles = 0
        while not stop_event:
            if stop_requested(STOP_PATH, __import__("os").getpid()):
                LOGGER.info("graceful stop requested by stop helper")
                summary["shutdown_status"] = "STOP_REQUESTED"
                break
            # Re-evaluate against the local exchange schedule every cycle.  A
            # status fetched at startup can remain PRE_OPEN for hours in UAT.
            current = classify_market_window(_now(args.now), None)
            if current.state == "CLOSED":
                summary["shutdown_status"] = f"MARKET_CLOSED/{current.reason}"
                break
            if current.state == "MIDDAY_BREAK":
                LOGGER.info("midday break; API collection paused")
                if args.once or _sleep(60):
                    summary["shutdown_status"] = "MIDDAY_BREAK"
                    break
                continue
            attempts = 0
            while attempts < 3:
                attempts += 1
                try:
                    ok, result = (True, {"orders_placed": 0}) if args.dry_run else _collector_cycle(cycles)
                    if ok:
                        summary["rotation_generations"] += 1
                        summary["api_requests"] += 50
                        summary["one_minute_rows_written"] += int(result.get("rows_1m", 0))
                        summary["candle_status"] = str(result.get("status", "SUCCESS"))
                        if summary["candle_status"] != "SUCCESS":
                            LOGGER.warning("candle collection status=%s symbols_completed=%s no_data=%s stale=%s", summary["candle_status"], result.get("symbols", 0), result.get("no_data_symbols", []), result.get("stale_symbols", []))
                        summary["symbols_with_1m_data"] = max(summary["symbols_with_1m_data"], int(result.get("symbols", 0)))
                        bbo = result.get("realtime_rotation", result)
                        summary["bbo_events_written"] += int(bbo.get("events", 0)) if isinstance(bbo, dict) else 0
                        summary["validation_errors"] += int(result.get("validation_issues", 0))
                        summary["conflicts"] += int(result.get("conflicts", 0))
                        health = _health()
                        summary["health_checks"] += 1
                        LOGGER.info("health check completed checkpoints=%s", len(health.get("checkpoints", {})))
                        break
                    raise RuntimeError(str(result.get("error", "collector cycle failed")))
                except Exception as error:
                    LOGGER.exception("collector attempt=%s failed", attempts)
                    if attempts >= 3:
                        summary["shutdown_status"] = "FAILED"
                        return 1
                    if _sleep(30 * (2 ** (attempts - 1))):
                        summary["shutdown_status"] = "STOP_REQUESTED"
                        return 0
            cycles += 1
            if args.once or (args.max_cycles and cycles >= args.max_cycles):
                summary["shutdown_status"] = "COMPLETED_BOUNDED_RUN"
                break
            if _sleep(args.interval_seconds):
                summary["shutdown_status"] = "STOP_REQUESTED"
                break
        if stop_event and summary["shutdown_status"] is None:
            summary["shutdown_status"] = "SIGINT"
        return 0
    finally:
        disk = check_disk(ROOT / "data" / "pilot" / "settrade")
        summary["disk_free_end"] = disk.free_bytes
        end = _now(args.now).astimezone(timezone.utc)
        summary["end_time"] = end.isoformat()
        summary["runtime_seconds"] = max(0.0, (end - start.astimezone(timezone.utc)).total_seconds())
        summary["orders_placed"] = 0
        if summary["shutdown_status"] is None:
            summary["shutdown_status"] = "CLEAN_EXIT"
        atomic_json_write(SUMMARY_DIR / f"settrade_daily_{summary['date']}.json", summary)
        try:
            _health()
        except Exception:
            LOGGER.exception("final health snapshot failed")
        STOP_PATH.unlink(missing_ok=True)
        lock.release()
        LOGGER.info("daily runner finished status=%s", summary["shutdown_status"])


def main() -> int:
    try:
        return run(_parser().parse_args())
    except KeyboardInterrupt:
        return 0
    except Exception:
        LOGGER.exception("daily runner failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
