# Data Exploration UI Deployment

The repository is the portable unit. Copy the project root as one directory to
the prepared machine; do not copy generated `__pycache__` directories or local
virtual environments. The UI is optional and read-only: it does not participate
in strategy, backtest, execution, or paper-trading runtime.

## Install

From the project root on the target machine:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the UI

```powershell
python -m streamlit run ui/app.py
```

The UI discovers paths from the repository. It reads the historical constituent
CSV, Yahoo ticker audit, acquisition report, metadata, and raw market-data
directories. It never fills, cleans, overwrites, or writes source data.

If the target machine is for trading only, the `ui/` directory and Streamlit
dependency may be omitted, but the data, audit, and acquisition modules remain
the authoritative project artifacts. For research review, keep the complete
repository together so provenance paths remain valid.