# command.md

## SET50 Research Repo — Quick Commands

> Example research repo path:
>
> `D:\GitHub\SET50-Algo-Trading`

### Go to the research repo

```cmd
cd /d D:\GitHub\SET50-Algo-Trading
```

### Activate the research virtual environment

CMD:

```cmd
.venv\Scripts\activate
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Deactivate:

```cmd
deactivate
```

## Streamlit Web UI

Run the research website:

```cmd
.\.venv\Scripts\python.exe -m streamlit run ui\app.py
```

If the virtual environment is already activated:

```cmd
python -m streamlit run ui\app.py
```

Default URL:

```text
http://localhost:8501
```

Stop the web server with `Ctrl+C`.

## Settrade Collector

Start the normal daily collector:

```cmd
.\scripts\start_settrade_daily.bat
```

Stop the collector:

```cmd
.\scripts\stop_settrade_daily.bat
```

Check collector health:

```cmd
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
```

Run collector directly for debugging:

```cmd
.\.venv\Scripts\python.exe scripts\run_settrade_collector.py --universe current_set50 --mode combined
```

## Collector Logs

Follow today's collector log in PowerShell:

```powershell
Get-Content .\logs\settrade\daily-$(Get-Date -Format yyyy-MM-dd).log -Wait
```

Stop with `Ctrl+C`.

## Windows Task Scheduler

Check scheduled collector task:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\check_settrade_task.ps1
```

Install / reinstall the scheduled task:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\install_settrade_task.ps1
```

If the uninstall script exists:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\uninstall_settrade_task.ps1
```

Known task name:

```text
SET50 Settrade Daily Collector
```

## Tests / Git Validation

Run all tests:

```cmd
.\.venv\Scripts\python.exe -m pytest
```

Short output:

```cmd
.\.venv\Scripts\python.exe -m pytest -q
```

Check whitespace/errors:

```cmd
git diff --check
```

Check repository status:

```cmd
git status
```

Check current branch:

```cmd
git branch --show-current
```

Check repo root:

```cmd
git rev-parse --show-toplevel
```

## Python / Environment Checks

Check Python version:

```cmd
.\.venv\Scripts\python.exe --version
```

Check which Python is being used:

```cmd
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
```

Show installed Settrade package:

```cmd
.\.venv\Scripts\python.exe -m pip show settrade-v2
```

## Codex

Open Codex inside the research repo:

```cmd
cd /d D:\GitHub\SET50-Algo-Trading
codex
```

Open Codex from the parent GitHub folder when a task intentionally needs both repos:

```cmd
cd /d D:\GitHub
codex
```

## Switching Between the Two Repositories

Intended workflow:

- `SET50-Algo-Trading` = research
- KGI official repo = TradeSim / final submission

Do not share `.venv` between them.

Research repo:

```cmd
deactivate
cd /d D:\GitHub\SET50-Algo-Trading
.venv\Scripts\activate
```

Official KGI repo:

```cmd
deactivate
cd /d D:\GitHub\<KGI-OFFICIAL-REPO>
.venv\Scripts\activate
```

## Official KGI TradeSim Repo

Run these from the official competition repo only.

Check Python version:

```cmd
.venv\Scripts\python.exe --version
```

Expected:

```text
Python 3.13.x
```

Activate official environment:

```cmd
.venv\Scripts\activate
```

If recreating the official `.venv`:

```cmd
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

Launch Jupyter if installed by the official requirements:

```cmd
python -m jupyter notebook
```

Then open:

```text
TradingSimulation.ipynb
```

## After Moving the GitHub Folder

Example new location:

```text
D:\GitHub
```

Go to research repo:

```cmd
cd /d D:\GitHub\SET50-Algo-Trading
```

Then verify:

```cmd
git status
```

```cmd
.\.venv\Scripts\python.exe --version
```

Reinstall/check the collector task:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\install_settrade_task.ps1
```

Check collector health:

```cmd
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
```

Run Streamlit:

```cmd
.\.venv\Scripts\python.exe -m streamlit run ui\app.py
```

## Most-Used Commands

Research website:

```cmd
.\.venv\Scripts\python.exe -m streamlit run ui\app.py
```

Start collector:

```cmd
.\scripts\start_settrade_daily.bat
```

Collector health:

```cmd
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
```

Stop collector:

```cmd
.\scripts\stop_settrade_daily.bat
```

Direct collector debug:

```cmd
.\.venv\Scripts\python.exe scripts\run_settrade_collector.py --universe current_set50 --mode combined
```

Git status:

```cmd
git status
```

Run tests:

```cmd
.\.venv\Scripts\python.exe -m pytest -q
```

## Safety Notes

- Run collector commands only from the research repo.
- Run TradeSim/submission work only from the official KGI repo.
- Do not use one repo's `.venv` inside the other repo.
- Do not commit `.env` or credentials.
- If the repo is moved to a new disk, reinstall/check the Windows scheduled collector task.

Normal usage
.\.venv\Scripts\python.exe scripts\check_settrade_production_readiness.py
.\.venv\Scripts\python.exe scripts\probe_settrade_production.py
.\scripts\start_settrade_daily.bat

For future package refreshes, use:
.\.venv\Scripts\python.exe scripts\ingest_official_daily_ticks.py
.\.venv\Scripts\python.exe scripts\compare_official_tradesim_sources.py
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --list-official-data