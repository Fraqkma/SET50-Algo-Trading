from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from src.competition.tradesim_bridge.core import BridgeError, compare_results, discover_official_repo, inspect_official, list_dates, run
from src.competition.official_data import list_history_dates, list_tick_dates
from src.competition.tradesim_bridge.runtime import (inspect_archive, inventory_ticks,
    notebook_flow, discover_python3130, runtime_diagnostic, RuntimeErrorDetail)


def _run_summary(result):
    """Keep CLI output bounded; complete normalized data stays in run artifacts."""
    metadata = result.get("metadata", {})
    return {"run_id": result.get("run_id"), "status": result.get("status"),
            "strategy": result.get("strategy"), "tradesim_version": result.get("tradesim_version"),
            "python_version": result.get("python_version"), "data_source": metadata.get("data_source", "UNKNOWN"),
            "dates": result.get("dates"), "orders": result.get("order_count"),
            "fills": result.get("fill_count"), "ending_nav": result.get("ending_nav"),
            "error_count": len(result.get("errors", [])), "error_examples": result.get("errors", [])[:3],
            "run_directory": str(Path(metadata.get("raw_result", "")).parent) if metadata.get("raw_result") else None,
            "warning": "Run output is simulator evidence only; it is not a competition performance claim."}

def main():
    p=argparse.ArgumentParser(description='Invoke the official KGI TradeSim in its own Python environment.')
    p.add_argument('--official-repo', help='Compatibility alias; only tools/kgi_tradesim is accepted.')
    p.add_argument('--check',action='store_true'); p.add_argument('--list-dates',action='store_true', help='List the selected source dates (practice by default).')
    p.add_argument('--list-official-data',action='store_true',help='Show cached official archive identity and coverage manifests.')
    p.add_argument('--list-tick-dates',action='store_true',help='List official Daily_Ticks archive dates.')
    p.add_argument('--list-history-dates',nargs='?',const='1D',metavar='TIMEFRAME',help='List official history dates (1D, 1m, 3m, 5m, 10m, 15m, 30m, 60m, 120m, 240m).')
    p.add_argument('--data-source',choices=('practice','official'),default='practice',help='Select bundled practice data or official Daily_Ticks data explicitly; there is no fallback.')
    p.add_argument('--archive-info',action='store_true'); p.add_argument('--notebook-flow',action='store_true')
    p.add_argument('--check-python3130',action='store_true')
    p.add_argument('--date',action='append',dest='dates'); p.add_argument('--all-days',action='store_true')
    p.add_argument('--strategy',type=Path); p.add_argument('--timeout',type=int,default=600)
    p.add_argument('--compare',nargs=2,metavar=('RESEARCH_JSON','OFFICIAL_JSON'))
    a=p.parse_args()
    try:
        if a.archive_info:
            print(json.dumps(inspect_archive(), indent=2)); return 0
        if a.notebook_flow:
            print(json.dumps(notebook_flow(), indent=2)); return 0
        if a.check_python3130:
            try:
                print(str(discover_python3130()))
                return 0
            except RuntimeErrorDetail as e:
                print(str(e), file=sys.stderr); return 2
        if a.compare:
            research=json.loads(Path(a.compare[0]).read_text(encoding='utf-8'))
            official=json.loads(Path(a.compare[1]).read_text(encoding='utf-8'))
            print(json.dumps(compare_results(research,official),indent=2,default=str)); return 0
        if a.check:
            report=runtime_diagnostic(ROOT)
            print(json.dumps(report, indent=2))
            return 0 if report['status'] in {'READY', 'READY_WITH_WARNINGS'} else 2
        repo=discover_official_repo(a.official_repo)
        if a.list_official_data:
            report_path=ROOT/'reports'/'tradesim_official_daily_ticks_package.json'
            if not report_path.is_file():
                print(json.dumps({'status':'OFFICIAL_DATA_NOT_INGESTED','manifest':str(report_path)})); return 2
            manifest=json.loads(report_path.read_text(encoding='utf-8'))
            history_dates=manifest.get('official_history',{}).get('dates',[])
            tick_dates=manifest.get('official_ticks',{}).get('dates',[])
            print(json.dumps({'source':manifest.get('source'),'archive_identity':manifest.get('archive_identity'),
                'history':{'file_count':manifest.get('official_history',{}).get('file_count'),
                           'total_rows':manifest.get('official_history',{}).get('total_rows'),
                           'date_count':len(history_dates),'first_date':history_dates[0] if history_dates else None,
                           'latest_date':history_dates[-1] if history_dates else None,
                           'symbols':manifest.get('official_history',{}).get('symbols')},
                'ticks':{'file_count':manifest.get('official_ticks',{}).get('file_count'),
                         'total_rows':manifest.get('official_ticks',{}).get('total_rows'),
                         'dates':tick_dates,'symbols':manifest.get('official_ticks',{}).get('symbols')},
                'standalone_daily_ticks':{'file_count':manifest.get('standalone_daily_ticks',{}).get('file_count'),
                                          'dates':manifest.get('standalone_daily_ticks',{}).get('dates')},
                'comparison_report':'reports/tradesim_vs_settrade_data_comparison.json'},indent=2)); return 0
        if a.list_tick_dates:
            print(json.dumps({'source':'TRADESIM_OFFICIAL_TICKS','dates':list_tick_dates()},indent=2)); return 0
        if a.list_history_dates is not None:
            timeframe=a.list_history_dates
            print(json.dumps({'source':'TRADESIM_OFFICIAL_HISTORY','timeframe':timeframe,
                              'dates':list_history_dates(timeframe=timeframe)},indent=2)); return 0
        if a.list_dates:
            if a.data_source == 'official':
                print(json.dumps({'source':'TRADESIM_OFFICIAL_TICKS','dates':list_tick_dates()},indent=2)); return 0
            print(json.dumps(inventory_ticks(),indent=2)); return 0
        if a.data_source == 'official':
            inventory=[{'dates':[day]} for day in list_tick_dates()]
        else:
            inventory=list_dates(repo)
        dates=[d for row in inventory for d in row['dates']] if a.all_days else (a.dates or [])
        if not dates: p.error('specify --date YYYY-MM-DD, --all-days, --check, or --list-dates')
        result=run(repo,ROOT,dates,a.strategy,a.timeout,a.data_source); print(json.dumps(_run_summary(result),indent=2,default=str)); return 0 if result['status']=='success' else 3
    except (BridgeError, RuntimeErrorDetail) as e:
        print(str(e),file=sys.stderr); return 2
if __name__=='__main__': raise SystemExit(main())
