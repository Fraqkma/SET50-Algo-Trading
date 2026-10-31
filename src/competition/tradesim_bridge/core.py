from __future__ import annotations
import ast, csv, hashlib, json, os, re, shutil, subprocess, sys, time, uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .runtime import archive_path, inspect_archive, runtime_root

LOCAL_ENV_FILE = Path(__file__).resolve().parents[3] / '.env'
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
LOCAL_RUNTIME = runtime_root(REPOSITORY_ROOT)

class BridgeError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(f"{code}: {message}")

@dataclass(frozen=True)
class OfficialRepo:
    root: Path
    python: Path
    python_version: str
    commit: str
    dirty: bool
    tradesim_version: str | None = None

def discover_official_repo(value: str | Path | None = None) -> Path:
    root = Path(value).expanduser().resolve() if value else LOCAL_RUNTIME.resolve()
    allowed = {LOCAL_RUNTIME.resolve(), (REPOSITORY_ROOT / 'tools' / 'kgi_tradesim').resolve(),
               (REPOSITORY_ROOT / 'tools' / 'kgi_tradesim' / '0.2.5').resolve(),
               (REPOSITORY_ROOT / 'tools' / 'kgi_tradesim' / '0.2.6').resolve(),
               (REPOSITORY_ROOT / 'tools' / 'kgi_tradesim' / '0.2.7').resolve()}
    if root not in allowed:
        raise BridgeError("OFFICIAL_REPO_INVALID", "This bridge only uses local, versioned TradeSim extractions.")
    if not root.is_dir() or not (root/'tradeSim/TradeSim.py').is_file() or not (root/'TradingSimulation.ipynb').is_file():
        raise BridgeError("OFFICIAL_REPO_INVALID", f"{root} does not contain TradeSim and TradingSimulation.ipynb.")
    return root

def _git(root: Path, *args: str) -> str:
    p = subprocess.run(['git', '-c', f'safe.directory={root}', *args], cwd=root, capture_output=True, text=True, timeout=15)
    return p.stdout.strip() if p.returncode == 0 else 'unknown'

def _git_metadata(root: Path) -> dict[str, Any]:
    """Report a commit only when the supplied directory is itself a Git root."""
    top = _git(root, 'rev-parse', '--show-toplevel')
    if top == 'unknown' or Path(top).resolve() != root.resolve():
        return {'commit': None, 'dirty': None, 'status': 'NOT_A_GIT_ROOT'}
    return {'commit': _git(root, 'rev-parse', 'HEAD'),
            'dirty': bool(_git(root, 'status', '--porcelain')), 'status': 'AVAILABLE'}

def inspect_official(root: Path, research_root: Path | None = None,
                     version_override: str | None = None) -> OfficialRepo:
    repo = research_root.resolve() if research_root else (root.parents[2] if root.name in {'0.2.5', '0.2.6', '0.2.7'} else root.parents[1])
    py = repo/'.venv-kgi313/Scripts/python.exe'
    if not py.is_file(): raise BridgeError('OFFICIAL_VENV_MISSING', f'Expected official interpreter at {py}.')
    p = subprocess.run([str(py), '-c', "import sys,tradeSim; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"], cwd=root, capture_output=True, text=True, timeout=20)
    if p.returncode: raise BridgeError('TRADESIM_IMPORT_FAILED', p.stderr.strip())
    version = p.stdout.strip().splitlines()[-1]
    if version != '3.13.0': raise BridgeError('OFFICIAL_PYTHON_WRONG_VERSION', f'Expected exactly Python 3.13.0, found {version}.')
    package_version = version_override or (root.name if root.name in {'0.2.5', '0.2.6', '0.2.7'} else '0.2.5')
    git_info = _git_metadata(root)
    return OfficialRepo(root, py, version, git_info['commit'] or 'NOT_A_GIT_ROOT',
                        bool(git_info['dirty']), package_version)

def list_dates(root: Path) -> list[dict[str, Any]]:
    folder=root/'marketInfo/ticks'
    if not folder.is_dir(): raise BridgeError('TICK_DATA_MISSING',str(folder))
    out=[]
    for path in sorted(folder.glob('*.csv')):
        try:
            with path.open(encoding='utf-8-sig',newline='') as f:
                reader=csv.DictReader(f); fields=reader.fieldnames or []
                if not {'TradeDateTime','ShareCode'} <= set(fields): continue
                from datetime import datetime
                count=0; first_stamp=None; last_stamp=None; dates=set(); symbols=set()
                for row in reader:
                    count+=1
                    try:
                        stamp=datetime.fromisoformat(row['TradeDateTime'].replace('Z','+00:00'))
                        first_stamp=stamp if first_stamp is None or stamp<first_stamp else first_stamp
                        last_stamp=stamp if last_stamp is None or stamp>last_stamp else last_stamp
                        dates.add(stamp.date().isoformat())
                    except (KeyError,ValueError,TypeError): pass
                    if row.get('ShareCode','').strip(): symbols.add(row['ShareCode'].strip())
            if not count or first_stamp is None: continue
            out.append({'file':path.name,'dates':sorted(dates),'first_timestamp':first_stamp.isoformat(),'last_timestamp':last_stamp.isoformat(),'rows':count,'symbols':sorted(symbols)})
        except (OSError,csv.Error,ValueError): continue
    return out

def _git_state(root: Path): return {'commit':_git(root,'rev-parse','HEAD'),'dirty':bool(_git(root,'status','--porcelain'))}
def _hash(path: Path): return hashlib.sha256(path.read_bytes()).hexdigest()

def _official_fee_rates(root: Path) -> tuple[float, float] | None:
    """Read literal commission/VAT constants from the vendored simulator source."""
    source = root / 'tradeSim' / 'CommissionService.py'
    try:
        tree = ast.parse(source.read_text(encoding='utf-8'))
    except (OSError, SyntaxError, UnicodeError):
        return None
    values: dict[str, float] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef) or node.name != 'commissionService':
            continue
        for statement in node.body:
            if isinstance(statement, ast.Assign) and len(statement.targets) == 1 and isinstance(statement.targets[0], ast.Name):
                name = statement.targets[0].id
                if name in {'comm', 'vat'}:
                    try:
                        values[name] = float(ast.literal_eval(statement.value))
                    except (ValueError, TypeError):
                        pass
    if {'comm', 'vat'} <= values.keys():
        return values['comm'], values['vat']
    return None

def normalize_result(raw: dict[str,Any], runid: str, name: str, dates: list[str], strategy_hash: str, research_root: Path, root: Path, official: OfficialRepo, duration: float, out: Path, run_metadata: dict[str, Any] | None = None) -> dict[str,Any]:
    from src.competition.period import boundary_fill_status, competition_scope

    period_scope = competition_scope(dates)
    boundary_status = None
    daily=raw.get('daily',[]); last=daily[-1] if daily else {}
    pr=last.get('Portfolio Total Return'); bm=last.get('Benchmark Return')
    errors=raw.get('errors',[])
    excess=last.get('Excess Return')
    if excess is None and isinstance(pr,(int,float)) and isinstance(bm,(int,float)):
        excess=pr-bm
    tx=raw.get('transactions',[])
    raw_orders = raw.get('orders', [])
    fills_by_order: dict[str, list[dict[str, Any]]] = {}
    normalized_fills = []
    for index, fill in enumerate(tx):
        order_id = str(fill.get('Order Number') or fill.get('order_id') or f'fill-{index + 1}')
        fills_by_order.setdefault(order_id, []).append(fill)
        normalized_fills.append({**fill, 'order_id': order_id,
            'fill_id': f'{order_id}:{index + 1}',
            'filled_quantity': fill.get('Volume'), 'fill_price': fill.get('Price'),
            'fill_timestamp': fill.get('Timestamp'), 'raw_fill': fill,
            'simulator_version': official.tradesim_version,
            'reference_latest_price': fill.get('Market Price')})
    pending_by_id = {str(item.get('order_id') or item.get('Order Number')): item for item in raw_orders}
    order_ids = list(dict.fromkeys([*fills_by_order, *pending_by_id]))
    orders = []
    for order_id in order_ids:
        fills = fills_by_order.get(order_id, [])
        pending = pending_by_id.get(order_id, {})
        filled_quantity = sum(int(float(item.get('Volume', 0) or 0)) for item in fills)
        remaining = pending.get('remaining_quantity')
        requested = pending.get('requested_quantity')
        if requested is None and remaining is not None:
            requested = filled_quantity + int(remaining)
        if requested is None and fills and official.tradesim_version != '0.2.7':
            requested = filled_quantity
        status = pending.get('status') or ('FILLED' if fills else 'UNKNOWN')
        orders.append({**pending, 'order_id': order_id,
            'requested_quantity': requested, 'filled_quantity': filled_quantity,
            'matched_quantity': filled_quantity, 'simulator_version': official.tradesim_version,
            'remaining_quantity': 0 if 'CANCELED' in str(status) else (remaining if remaining is not None else (0 if fills else None)),
            'unfilled_quantity': int(remaining) if remaining is not None else 0,
            'canceled_quantity': int(remaining) if 'CANCELED' in str(status) and remaining is not None else 0,
            'status': status,
            'fill_timestamps': [item.get('Timestamp') for item in fills],
            'fill_prices': [item.get('Price') for item in fills],
            'fills': [item for item in normalized_fills if item['order_id'] == order_id]})
    partial_fill_count = sum(1 for item in orders if len(item['fills']) > 1
                             or str(item.get('status', '')).startswith('PARTIALLY_FILLED'))
    slippage_cost = 0.0
    for fill in tx:
        if official.tradesim_version == '0.2.7' or str(fill.get('Type', '')).lower() == 'market':
            try:
                direction = 1 if str(fill.get('Side', '')).lower() == 'buy' else -1
                slippage_cost += direction * (float(fill['Price']) - float(fill['Market Price'])) * int(float(fill['Volume']))
            except (KeyError, TypeError, ValueError):
                slippage_cost = None
                break
    commission=vat=0.0
    fee_rates = _official_fee_rates(root)
    if fee_rates is None:
        commission=vat=None
        commission_rate=vat_rate=None
    else:
        commission_rate, vat_rate = fee_rates
    for fill in tx:
        try:
            if commission_rate is None or vat_rate is None:
                break
            value=float(fill.get('Price'))*int(float(fill.get('Volume')))
            fee=value*commission_rate
            commission+=fee; vat+=fee*vat_rate
        except (TypeError, ValueError):
            commission=vat=None; break
    fifo_roundtrips=[]; fifo_count=None; fifo_metrics=None
    try:
        if commission_rate is not None and vat_rate is not None:
            from src.competition.metrics import fifo_metrics_from_fills
            ledger,fifo_metrics=fifo_metrics_from_fills(tx,commission_rate,vat_rate)
            fifo_roundtrips=[{'symbol':lot.symbol,'lot_id':lot.lot_id,'quantity':lot.initial_quantity,
                'matched_sell_quantity':lot.matched_sell_quantity,'net_pnl':lot.net_pnl,
                'completed':lot.completed,'open_timestamp':lot.open_timestamp,
                'closing_events':lot.closing_events} for lot in ledger.lots]
            fifo_count=fifo_metrics['round_trips']
    except (KeyError, TypeError, ValueError):
        fifo_count=None
    warnings=list(raw.get('warnings',[]))
    simulator_roundtrips=last.get('Total Round-Trip')
    if fifo_count is not None and simulator_roundtrips is not None and fifo_count != simulator_roundtrips:
        warnings.append(f'FIFO fill reconstruction ({fifo_count}) differs from TradeSim summary ({simulator_roundtrips}).')
    simulator_win_rate=last.get('Win Rate')
    simulator_expected_payoff=last.get('Expected Payoff')
    if fifo_metrics is not None and simulator_win_rate is not None and fifo_metrics.get('win_rate') is not None:
        if round(fifo_metrics['win_rate'], 1) != round(float(simulator_win_rate), 1):
            warnings.append('FIFO fill reconstruction Win Rate differs from TradeSim summary.')
    if fifo_metrics is not None and simulator_expected_payoff is not None and fifo_metrics.get('expected_payoff') is not None:
        if round(fifo_metrics['expected_payoff'], 2) != round(float(simulator_expected_payoff), 2):
            warnings.append('FIFO fill reconstruction Expected Payoff differs from TradeSim summary.')
    roundtrip_count = fifo_count if fifo_count is not None else simulator_roundtrips
    win_rate = fifo_metrics.get('win_rate') if fifo_metrics is not None else simulator_win_rate
    expected_payoff = fifo_metrics.get('expected_payoff') if fifo_metrics is not None else simulator_expected_payoff
    boundary_status = boundary_fill_status(tx)
    # Calendar coverage alone does not prove an official competition score:
    # the current runner resets TradeSim's portfolio on every date. Require
    # explicit evidence that a caller used a continuous portfolio engine.
    portfolio_continuity_validated = bool((run_metadata or {}).get('continuous_portfolio_validated'))
    competition_metrics_authorized = (
        period_scope['metrics_authorized']
        and boundary_status['status'] != 'UNKNOWN'
        and portfolio_continuity_validated
    )
    qualification={key:{'status':'UNKNOWN','value':None,'threshold':threshold} for key,threshold in {
        'drawdown_vs_benchmark':'< 1.5 × benchmark max DD','minimum_roundtrips':'>= 5',
        'average_exposure':'>= 0.50','expected_payoff':'> 0'}.items()}
    try:
        from src.competition.metrics import award_readiness, qualification_report
        scoring_metrics = {
            'portfolio_max_drawdown': last.get('Portfolio Maximum Drawdown (%)'),
            'benchmark_max_drawdown': last.get('Benchmark Maximum Drawdown'),
            'round_trips': roundtrip_count,
            'average_portfolio_exposure': last.get('Average Portfolio Exposure'),
            'expected_payoff': expected_payoff,
        } if competition_metrics_authorized else {
            'portfolio_max_drawdown': None, 'benchmark_max_drawdown': None,
            'round_trips': None, 'average_portfolio_exposure': None, 'expected_payoff': None,
        }
        qualification=qualification_report(scoring_metrics, 'CANONICAL_COMPETITION_WINDOW')
        awards=award_readiness({
            'portfolio_total_return': pr if competition_metrics_authorized else None,
            'excess_return': excess if competition_metrics_authorized else None,
            'calmar_ratio': last.get('Calmar Ratio') if competition_metrics_authorized else None,
            'portfolio_max_drawdown': last.get('Portfolio Maximum Drawdown (%)') if competition_metrics_authorized else None,
            'round_trips': roundtrip_count if competition_metrics_authorized else None,
            'win_rate': win_rate if competition_metrics_authorized else None,
        })
    except (TypeError,ValueError):
        awards=None
    return {'schema_version':6,'engine':f'OFFICIAL_TRADESIM_{official.tradesim_version.replace(".","_")}' if official.tradesim_version else 'OFFICIAL_TRADESIM_UNKNOWN','run_id':runid,'status':'completed_with_errors' if errors else 'success','strategy':name,'strategy_version':None,'strategy_sha256':strategy_hash,'dates':dates,
        'trading_dates':dates,'tradesim_version':official.tradesim_version,
        'competition_period': {'scope': period_scope, 'round_trip_boundary': boundary_status,
                              'continuous_portfolio_validated': portfolio_continuity_validated,
                              'scoring_metrics_authorized': competition_metrics_authorized,
                              'scoring_blocker': None if portfolio_continuity_validated else 'TRADE_SIM_RUNNER_RESETS_PORTFOLIO_PER_DATE'},
        'python_version':official.python_version,
        'tradesim_archive_sha256':((run_metadata or {}).get('tradesim_archive') or {}).get('sha256'),
        'runtime_seconds':duration,
        'starting_nav':raw.get('start_cash'),'ending_nav':last.get('Net Asset Value'),
        'portfolio_total_return':pr if competition_metrics_authorized else None,
        'benchmark_return':bm if competition_metrics_authorized else None,
        'excess_return':excess if competition_metrics_authorized else None,
        'portfolio_max_drawdown':last.get('Portfolio Maximum Drawdown (%)') if competition_metrics_authorized else None,
        'benchmark_max_drawdown':last.get('Benchmark Maximum Drawdown') if competition_metrics_authorized else None,
        'calmar_ratio':last.get('Calmar Ratio') if competition_metrics_authorized else None,
        'round_trips':roundtrip_count if competition_metrics_authorized else None,
        'simulator_metrics': {'portfolio_total_return': pr, 'benchmark_return': bm, 'excess_return': excess,
            'portfolio_max_drawdown': last.get('Portfolio Maximum Drawdown (%)'),
            'benchmark_max_drawdown': last.get('Benchmark Maximum Drawdown'), 'calmar_ratio': last.get('Calmar Ratio'),
            'round_trips': roundtrip_count, 'average_portfolio_exposure': last.get('Average Portfolio Exposure'),
            'win_rate': win_rate, 'expected_payoff': expected_payoff},
        'simulator_round_trips':simulator_roundtrips,
        'average_portfolio_exposure':last.get('Average Portfolio Exposure') if competition_metrics_authorized else None,
        'win_rate':win_rate if competition_metrics_authorized else None,
        'simulator_win_rate':simulator_win_rate,'expected_payoff':expected_payoff if competition_metrics_authorized else None,
        'simulator_expected_payoff':simulator_expected_payoff,
        'qualification':qualification,'award_readiness':awards,
        'start_cash':raw.get('start_cash'),'end_cash':last.get('Cash Balance'),'final_portfolio_value':last.get('Net Asset Value'),
        'gross_return':None,'net_return':pr if competition_metrics_authorized else None,
        'order_count':len(orders),
        'fill_count':len(tx),'fifo_roundtrip_count':fifo_count,'fifo_roundtrips':fifo_roundtrips,
        'non_fill_count':sum(item['filled_quantity'] == 0 for item in orders) if official.tradesim_version == '0.2.7' else None,
        'rejected_order_count':len(raw.get('rejected_orders', [])) if official.tradesim_version == '0.2.7' else None,'buy_value':None,'sell_value':None,
        'partial_fill_count':partial_fill_count,
        'commission':commission,'vat':vat,'total_fees':commission+vat if commission is not None else None,'slippage_cost':slippage_cost,
        'orders':orders,'fills':normalized_fills,'non_fills':raw.get('non_fills'),'rejected_orders':raw.get('rejected_orders'),'pending_orders':[item for item in orders if item.get('status') == 'PENDING_EOD_CANCELED'],'canceled_orders':[item for item in orders if 'CANCELED' in str(item.get('status'))],'ending_positions':raw.get('positions'),
        'errors':errors,'warnings':warnings,'daily':daily,'raw':{'official_result':str(out/'official_result.json')},
        'metadata':{'research_git':_git_state(research_root),'official_git':_git_metadata(root),
        'python_version':official.python_version,'tradesim_version':official.tradesim_version,
        'duration_seconds':duration,'raw_artifacts':str(out/'raw_official'),
        'raw_result':str(out/'official_result.json'),'stdout':str(out/'stdout.log'),
        'stderr':str(out/'stderr.log'),'official_root':str(root),
        'strategy_artifact':str(out/f'{name}.py'),**(run_metadata or {})}}

def prepare_official_data_runtime(base_runtime: Path, research_root: Path, destination: Path,
                                  dates: list[str]) -> dict[str, Any]:
    """Create a per-run TradeSim copy populated only with explicit official data."""
    from src.competition.official_data import DEFAULT_ROOT, TRADESIM_OFFICIAL_TICKS

    official_ticks = DEFAULT_ROOT / "ticks" / "ticks"
    official_history = DEFAULT_ROOT / "history"
    missing = [day for day in dates if not (official_ticks / f"{day}.csv").is_file()]
    if missing:
        raise BridgeError("OFFICIAL_TICK_DATE_NOT_AVAILABLE", ", ".join(missing))
    if not official_history.is_dir():
        raise BridgeError("OFFICIAL_HISTORY_NOT_AVAILABLE", str(official_history))

    def ignore_runtime_items(directory: str, names: list[str]) -> set[str]:
        current = Path(directory)
        ignored = {name for name in names if name == "result"}
        if current.name == "marketInfo":
            ignored.update(name for name in names if name in {"ticks", "daily_history", "intraday_history", "benchmark", "symbolSET50"})
        return ignored

    if destination.exists():
        raise BridgeError("OFFICIAL_RUNTIME_COPY_EXISTS", str(destination))
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(base_runtime, destination, ignore=ignore_runtime_items)
    market_info = destination / "marketInfo"
    (market_info / "ticks").mkdir(parents=True, exist_ok=True)
    for day in dates:
        shutil.copy2(official_ticks / f"{day}.csv", market_info / "ticks" / f"{day}.csv")
    for name in ("daily_history", "intraday_history", "benchmark", "symbolSET50"):
        source = official_history / name
        if source.is_dir():
            shutil.copytree(source, market_info / name, dirs_exist_ok=True)
    package_manifest = research_root / "reports" / "tradesim_official_daily_ticks_package.json"
    outer_hash = nested_hash = None
    if package_manifest.is_file():
        try:
            manifest = json.loads(package_manifest.read_text(encoding="utf-8"))
            outer_hash = manifest.get("archive_identity", {}).get("outer_sha256")
            nested = manifest.get("archive_identity", {}).get("nested_archives", {})
            nested_hash = nested.get("tradeSim_ticks.zip", {}).get("sha256")
        except (OSError, json.JSONDecodeError):
            pass
    return {"data_source": TRADESIM_OFFICIAL_TICKS, "history_source": "TRADESIM_OFFICIAL_HISTORY",
            "outer_archive_sha256": outer_hash, "tick_archive_sha256": nested_hash,
            "official_ticks_path": str(official_ticks), "official_history_path": str(official_history),
            "runtime_copy": str(destination), "selected_dates": dates}


def run(root: Path, research_root: Path, dates: list[str], strategy: Path|None=None,
        timeout: int=600, data_source: str="practice") -> dict[str,Any]:
    if timeout <= 0:
        raise BridgeError('INVALID_TIMEOUT', 'timeout must be a positive number of seconds.')
    if data_source not in {"practice", "official"}:
        raise BridgeError("DATA_SOURCE_INVALID", "Choose exactly 'practice' or 'official'.")
    base_official = inspect_official(root)
    official=base_official
    official_data_metadata: dict[str, Any] = {"data_source": "TRADESIM_" + (base_official.tradesim_version or "UNKNOWN").replace(".", "_") + "_PRACTICE"}
    if data_source == "official":
        if base_official.tradesim_version not in {"0.2.6", "0.2.7"}:
            raise BridgeError("OFFICIAL_DATA_REQUIRES_TRADESIM_026", "Official Daily_Ticks data is wired to the 0.2.6 runtime only.")
        from src.competition.official_data import list_tick_dates
        available = set(list_tick_dates())
        missing = [day for day in dates if day not in available]
        if missing:
            raise BridgeError("OFFICIAL_TICK_DATE_NOT_AVAILABLE", ", ".join(missing))
        runid = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
        out = research_root/'artifacts/official_tradesim_runs'/runid
        out.mkdir(parents=True,exist_ok=False)
        official_data_metadata = prepare_official_data_runtime(root, research_root, out/'runtime', dates)
        root = out/'runtime'
        official = inspect_official(root, research_root=research_root, version_override=base_official.tradesim_version)
    else:
        available={d for x in list_dates(root) for d in x['dates']}
    missing=[d for d in dates if d not in available]
    if missing: raise BridgeError('TICK_DATE_NOT_AVAILABLE',', '.join(missing))
    if strategy is None:
        name='BridgeSmokeStrategy'
        example = root/'strategy'/'Example_strategy.py'
        source=example.read_text(encoding='utf-8')
        name='Example_strategy'
        shash=hashlib.sha256(source.encode()).hexdigest()
    else:
        strategy=strategy.expanduser().resolve()
        if not strategy.is_file() or strategy.suffix.lower()!='.py': raise BridgeError('STRATEGY_ADAPTER_FAILED',str(strategy))
        name=strategy.stem
        if not re.fullmatch(r'[A-Za-z_]\w*',name): raise BridgeError('STRATEGY_ADAPTER_FAILED','Strategy filename must be a Python identifier.')
        source=strategy.read_text(encoding='utf-8'); shash=_hash(strategy)
    if data_source != "official":
        runid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]
        out=research_root/'artifacts/official_tradesim_runs'/runid; out.mkdir(parents=True,exist_ok=False)
    strategy_file=out/f'{name}.py'; strategy_file.write_text(source,encoding='utf-8')
    official_result=root/'result'/runid
    if official_result.exists():
        raise BridgeError('RUN_ID_COLLISION', f'Official temporary result path already exists: {official_result}')
    runner=Path(__file__).with_name('official_runner.py')
    cmd=[str(official.python),str(runner),'--official-root',str(root),'--run-id',runid,'--strategy',str(strategy_file),'--dates',*dates,'--output-dir',str(out),'--version',str(official.tradesim_version)]
    archive_info = None
    try:
        archive_info = inspect_archive(archive_path(research_root, base_official.tradesim_version))
    except (OSError, RuntimeError):
        pass
    tick_data = []
    for day in dates:
        path = root / 'marketInfo' / 'ticks' / f'{day}.csv'
        tick_data.append({'date': day, 'path': str(path),
                          'size_bytes': path.stat().st_size if path.is_file() else None,
                          'sha256': _hash(path) if path.is_file() else None})
    source_digest = hashlib.sha256()
    source_files = sorted((root / 'tradeSim').rglob('*.py')) if (root / 'tradeSim').is_dir() else []
    for source_path in source_files:
        source_digest.update(source_path.relative_to(root).as_posix().encode('utf-8'))
        source_digest.update(source_path.read_bytes())
    run_metadata = {
        'run_started_at_utc': datetime.now(timezone.utc).isoformat(),
        'tradesim_archive': archive_info,
        'tradesim_source_tree_sha256': source_digest.hexdigest() if source_files else None,
        'tick_data': tick_data,
        'simulation_dates': dates,
        'research_git': _git_state(research_root),
        'strategy_sha256': shash,
        **official_data_metadata,
    }
    (out/'run_metadata.json').write_text(json.dumps(run_metadata,indent=2,default=str),encoding='utf-8')
    start=time.monotonic()
    try:
        secret_markers=('SECRET','TOKEN','PASSWORD','API_KEY','APP_ID','SETTRADE','CREDENTIAL')
        child_env={k:v for k,v in os.environ.items() if 'PYTHONPATH' != k.upper() and not any(x in k.upper() for x in secret_markers)}
        p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=timeout,env=child_env)
        duration=time.monotonic()-start
        (out/'stdout.log').write_text(p.stdout,encoding='utf-8',errors='replace'); (out/'stderr.log').write_text(p.stderr,encoding='utf-8',errors='replace')
        rawfile=out/'official_result.json'
        if p.returncode: raise BridgeError('TRADESIM_RUN_FAILED',f'exit={p.returncode}; see {out}/stderr.log')
        if not rawfile.is_file(): raise BridgeError('RESULT_PARSE_FAILED',str(rawfile))
        raw=json.loads(rawfile.read_text(encoding='utf-8'))
        normalized=normalize_result(raw,runid,name,dates,shash,research_root,root,official,duration,out,run_metadata)
        (out/'normalized_result.json').write_text(json.dumps(normalized,indent=2,default=str),encoding='utf-8')
        return normalized
    except subprocess.TimeoutExpired as e:
        (out/'stdout.log').write_text(str(e.stdout or ''),encoding='utf-8'); (out/'stderr.log').write_text(str(e.stderr or ''),encoding='utf-8')
        raise BridgeError('TRADESIM_RUN_TIMEOUT',f'Timed out after {timeout}s; logs in {out}') from e
    finally:
        if official_result.exists():
            shutil.copytree(official_result,out/'raw_official',dirs_exist_ok=True)
            shutil.rmtree(official_result)

def compare_results(research:dict[str,Any], official:dict[str,Any]):
    dimensions = {
        'signals': ('signals', 'signals'),
        'orders': ('orders', 'orders'),
        'fills': ('fills', 'fills'),
        'non_fills': ('non_fills', 'non_fills'),
        'prices': ('execution_prices', 'execution_prices'),
        'fees': ('total_fees', 'total_fees'),
        'turnover': ('turnover', 'turnover'),
        'holdings': ('ending_positions', 'ending_positions'),
        'return': ('return', 'net_return'),
    }
    detail = {}
    for name, (research_key, official_key) in dimensions.items():
        left, right = research.get(research_key), official.get(official_key)
        status = ('UNKNOWN' if left is None or right is None else
                  'MATCH' if left == right else 'DIVERGENCE')
        detail[name] = {'status': status, 'research': left, 'official': right}
    return {'date':official.get('dates'),'strategy_version':official.get('strategy_sha256'),
        'research_engine':research.get('engine','RESEARCH_BACKTEST'),'official_engine':official.get('engine', 'OFFICIAL_TRADESIM_UNKNOWN'),
        'research_ending_equity':research.get('ending_equity'),'official_ending_equity':official.get('final_portfolio_value'),
        'research_return':research.get('return'),'official_return':official.get('net_return'),
        'benchmark_return':official.get('benchmark_return'),'excess_return':official.get('excess_return'),
        'research_cost':research.get('cost'),'official_cost':official.get('total_fees'),
        'research_fills':research.get('fill_count'),'official_fills':official.get('fill_count'),
        'research_turnover':research.get('turnover'),'official_turnover':official.get('turnover'),
        'research_positions':research.get('ending_positions'),'official_positions':official.get('ending_positions'),
        'dimensions':detail,
        'potential_divergence_causes':['data granularity','decision/fill timing','order validity and expiration',
            'tick-size rounding','slippage','commission/VAT','fill model','portfolio state semantics'],
        'cause_attribution':'UNKNOWN until both engines provide comparable detailed evidence',
        'comparison_note':'Differences are expected from data granularity, fill timing, order behavior, fees, slippage and portfolio state; values are kept engine-specific.'}
