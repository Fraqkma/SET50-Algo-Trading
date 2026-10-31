# Phase 5 Collector Readiness

Oct 30's collector completed 21 rotations and persisted 5,314 1m rows and 9,689 BBO events before it failed after three local health subprocess timeouts at 60 seconds. Collection subprocesses exited 0; the evidence supports a slow health scan as the observed cause, not a stuck collector. Default timeout is now 180 seconds (bounded 90–300), with failure propagation preserved.

Oct 29 remains `PARTIAL_COLLECTION`. The Task Scheduler task was directly rechecked as enabled/Ready with Password logon and `interactive_only=false`, but actual unattended execution remains `UNATTENDED_CONFIGURED_NOT_RUNTIME_VALIDATED`. Nov 2 is `NOV2_NOT_YET_OBSERVABLE`. Read-only check after 09:45 Bangkok: `'.\.venv\Scripts\python.exe scripts\check_settrade_collector_readonly.py --target-date 2026-11-02'`. See [diagnostics](../reports/phase5_collector_diagnostics.json).
