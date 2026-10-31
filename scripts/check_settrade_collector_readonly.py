"""Read-only evidence check for the SET50 Settrade daily collector."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Asia/Bangkok")


def latest_row(path: Path, target: str, time_columns: tuple[str, ...]) -> dict:
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)), "exists": False, "latest_target_date": None, "target_rows": 0, "symbols": 0}
    dates, symbols, count = [], set(), 0
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            stamp = next((row[k] for k in time_columns if k in row and row[k]), None)
            if stamp and stamp[:10] == target:
                dates.append(stamp); count += 1
                sym = row.get("symbol") or row.get("Symbol")
                if sym: symbols.add(sym)
    return {"path": str(path.relative_to(ROOT)), "exists": True, "latest_target_date": max(dates) if dates else None, "target_rows": count, "symbols": len(symbols)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default="2026-11-02", help="Expected SET session date, YYYY-MM-DD")
    args = parser.parse_args()
    target = date.fromisoformat(args.target_date).isoformat()
    now = datetime.now(TZ)
    task_name = "SET50 Settrade Daily Collector"
    ps = f"$t=Get-ScheduledTask -TaskName '{task_name}' -ErrorAction Stop; $i=Get-ScheduledTaskInfo -TaskName '{task_name}'; [pscustomobject]@{{State=$t.State.ToString();Enabled=$t.Settings.Enabled;LastRun=$i.LastRunTime.ToString('o');NextRun=$i.NextRunTime.ToString('o');LastTaskResult=$i.LastTaskResult;Principal=$t.Principal.UserId;LogonType=$t.Principal.LogonType.ToString();InteractiveOnly=$t.Principal.LogonType.ToString() -eq 'InteractiveToken';Actions=@($t.Actions | ForEach-Object {{ [pscustomobject]@{{Execute=$_.Execute;Arguments=$_.Arguments;WorkingDirectory=$_.WorkingDirectory}} }})}} | ConvertTo-Json -Depth 5 -Compress"
    try:
        task = json.loads(subprocess.check_output(["powershell.exe", "-NoProfile", "-Command", ps], text=True, stderr=subprocess.STDOUT))
    except Exception as exc:  # access/history may be unavailable; never infer a success
        task = {"status": "UNKNOWN", "error": str(exc)}
    log = ROOT / "logs/settrade" / f"daily-{target}.log"
    log_evidence = {"path": str(log.relative_to(ROOT)), "exists": log.exists(), "started": False, "finished": False, "exit_status": None}
    if log.exists():
        content = log.read_text(encoding="utf-8", errors="replace")
        log_evidence["started"] = "daily runner started" in content or "daily runner starting" in content
        log_evidence["finished"] = "daily runner finished" in content
        if "status=FAILED" in content: log_evidence["exit_status"] = "FAILED"
        elif "status=SUCCESS" in content: log_evidence["exit_status"] = "SUCCESS"
        else: log_evidence["exit_status"] = "UNKNOWN"
    daily = latest_row(ROOT / "data/pilot/settrade/production/normalized/bars_1d/data.csv", target, ("timestamp", "datetime", "Date"))
    intraday = {tf: latest_row(ROOT / f"data/pilot/settrade/production/normalized/bars_{tf}/data.csv", target, ("timestamp", "datetime", "Date")) for tf in ("1m", "5m", "15m")}
    bbo = latest_row(ROOT / "data/pilot/settrade/production/normalized/bid_offer/data.csv", target, ("retrieved_at", "timestamp", "datetime"))
    checkpoints = {}
    for name in ("candles.json", "bid_offer.json"):
        p = ROOT / "data/pilot/settrade/production/checkpoints" / name
        try: checkpoints[name] = json.loads(p.read_text(encoding="utf-8"))
        except Exception: checkpoints[name] = {"status": "UNKNOWN", "error": "missing or unreadable"}
    lock_path = ROOT / ".settrade-runtime/daily.lock"
    lock = None
    if lock_path.exists():
        try:
            data = json.loads(lock_path.read_text(encoding="utf-8")); pid = int(data["pid"])
            proc = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True, check=False)
            lock = {"exists": True, "pid": pid, "process_listed": str(pid) in proc.stdout, "created_at": data.get("created_at")}
        except Exception as exc: lock = {"exists": True, "owner_status": "UNKNOWN", "error": str(exc)}
    else: lock = {"exists": False}
    latest_evidence = [daily, *intraday.values(), bbo]
    any_data = any(x["target_rows"] for x in latest_evidence)
    all_expected = daily["symbols"] >= 50 and all(intraday[t]["symbols"] >= 45 for t in intraday) and bbo["symbols"] >= 10
    if task.get("LastRun", "")[:10] != target and not log_evidence["started"] and not any_data: status = "NO_START"
    elif log_evidence["exit_status"] == "SUCCESS" and all_expected: status = "SUCCESS"
    elif any_data or log_evidence["started"]: status = "PARTIAL"
    else: status = "UNKNOWN"
    result = {"check_id": f"SETTRADE_COLLECTOR_READONLY_{target}", "classification": status, "checked_at_bangkok": now.isoformat(), "target_session_date": target,
        "task": task, "runner_log": log_evidence, "durable_data": {"daily": daily, "intraday": intraday, "bbo": bbo}, "checkpoints": checkpoints, "lock_process_evidence": lock,
        "next_run": task.get("NextRun"), "safety": "Read-only: queried Task Scheduler, process list, existing logs/checkpoints/CSV; no task/process/file/data mutation and no brokerage calls."}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
