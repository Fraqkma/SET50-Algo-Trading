import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.competition.tradesim_bridge.core import (
    BridgeError, OfficialRepo, compare_results, discover_official_repo,
    list_dates, normalize_result,
)
from src.competition.tradesim_bridge import core


def test_official_repo_discovery_uses_local_runtime_only(monkeypatch):
    monkeypatch.delenv('KGI_OFFICIAL_REPO', raising=False)
    from src.competition.tradesim_bridge import core
    monkeypatch.setattr(core, 'LOCAL_ENV_FILE', Path('missing-local-config.env'))
    assert discover_official_repo() == core.LOCAL_RUNTIME.resolve()


def test_wrong_repo_type_rejected(tmp_path):
    with pytest.raises(BridgeError, match='OFFICIAL_REPO_INVALID'):
        discover_official_repo(tmp_path)


def test_date_inventory_uses_csv_timestamps_and_symbols(tmp_path):
    folder=tmp_path/'marketInfo'/'ticks'; folder.mkdir(parents=True)
    (folder/'misleading.csv').write_text('TradeDateTime,ShareCode,LastPrice\n2026-09-10 10:00:00,ABC,1\n2026-09-10 10:01:00,XYZ,2\n',encoding='utf-8')
    rows=list_dates(tmp_path)
    assert rows[0]['dates']==['2026-09-10']
    assert rows[0]['symbols']==['ABC','XYZ']


def test_normalizer_preserves_unknown_fields_as_null(tmp_path):
    repo=OfficialRepo(tmp_path,tmp_path/'python.exe','3.13.1','abc',True)
    normalized=normalize_result({'start_cash':10,'daily':[{'Cash Balance':9,'Net Asset Value':11,'Portfolio Total Return':10,'Benchmark Return':3}],'transactions':[]},'r1','S',['2026-01-01'],'hash',tmp_path,tmp_path,repo,1.2,tmp_path)
    assert normalized['excess_return']==7
    assert normalized['commission'] is None
    assert normalized['final_portfolio_value']==11
    assert normalized['metadata']['official_git']['status']=='NOT_A_GIT_ROOT'


def test_missing_benchmark_does_not_fabricate_excess(tmp_path):
    repo=OfficialRepo(tmp_path,tmp_path/'python.exe','3.13.1','abc',False)
    value=normalize_result({'daily':[{'Portfolio Total Return':2}]},'r1','S',[],'hash',tmp_path,tmp_path,repo,0,tmp_path)
    assert value['benchmark_return'] is None
    assert value['excess_return'] is None


def test_normalizer_uses_fee_constants_from_official_source(tmp_path):
    root=tmp_path/'official'; (root/'tradeSim').mkdir(parents=True)
    (root/'tradeSim'/'CommissionService.py').write_text(
        'class commissionService:\n    comm = 0.00157\n    vat = 0.07\n', encoding='utf-8')
    repo=OfficialRepo(root,Path('python.exe'),'3.13.0','unknown',False,'0.2.5')
    result=normalize_result({'transactions':[
        {'Side':'Buy','Price':10,'Volume':100},
        {'Side':'Sell','Price':11,'Volume':100}], 'daily':[]},
        'r1','S',[],'strategy-hash',tmp_path,root,repo,1.0,tmp_path)
    notional=2100
    assert result['commission']==pytest.approx(notional*0.00157)
    assert result['vat']==pytest.approx(notional*0.00157*0.07)
    assert result['total_fees']==pytest.approx(notional*0.00157*1.07)


def test_normalizer_keeps_multiple_fills_and_eod_canceled_residual(tmp_path):
    root=tmp_path/'official'; (root/'tradeSim').mkdir(parents=True)
    (root/'tradeSim'/'CommissionService.py').write_text(
        'class commissionService:\n    comm = 0.00157\n    vat = 0.07\n', encoding='utf-8')
    repo=OfficialRepo(root,Path('python.exe'),'3.13.0','unknown',False,'0.2.6')
    raw={'transactions':[
        {'Order Number':'o1','Side':'Buy','Symbol':'AOT','Volume':100,'Price':10,'Timestamp':'t1'},
        {'Order Number':'o1','Side':'Buy','Symbol':'AOT','Volume':200,'Price':10,'Timestamp':'t2'}],
        'orders':[{'order_id':'o1','requested_quantity':500,'filled_quantity':300,
                   'remaining_quantity':200,'status':'PARTIALLY_FILLED_EOD_CANCELED'}],
        'daily':[]}
    result=normalize_result(raw,'r1','S',[],'hash',tmp_path,root,repo,1.0,tmp_path)
    assert result['schema_version']==4
    assert result['fill_count']==2
    assert result['partial_fill_count']==1
    assert result['orders'][0]['requested_quantity']==500
    assert result['orders'][0]['filled_quantity']==300
    assert result['orders'][0]['canceled_quantity']==200
    assert result['orders'][0]['remaining_quantity']==0
    assert result['canceled_orders'][0]['status']=='PARTIALLY_FILLED_EOD_CANCELED'
    assert [fill['fill_timestamp'] for fill in result['fills']]==['t1','t2']


def test_normalized_qualification_prefers_fifo_rebuilt_completed_lots(tmp_path):
    root=tmp_path/'official'; (root/'tradeSim').mkdir(parents=True)
    (root/'tradeSim'/'CommissionService.py').write_text(
        'class commissionService:\n    comm = 0.00157\n    vat = 0.07\n', encoding='utf-8')
    repo=OfficialRepo(root,Path('python.exe'),'3.13.0','unknown',False,'0.2.5')
    raw={
        'start_cash':1_000_000,
        'daily':[{'Portfolio Total Return':1,'Benchmark Return':0,
                  'Portfolio Maximum Drawdown (%)':0,'Benchmark Maximum Drawdown':1,
                  'Total Round-Trip':99,'Average Portfolio Exposure':0.6,
                  'Win Rate':0,'Expected Payoff':-1}],
        'transactions':[
            {'Order Number':'buy-1','Side':'Buy','Symbol':'AOT','Volume':100,'Price':10,'Timestamp':'d1'},
            {'Order Number':'sell-1','Side':'Sell','Symbol':'AOT','Volume':100,'Price':11,'Timestamp':'d2'}],
    }
    result=normalize_result(raw,'r1','S',[],'strategy-hash',tmp_path,root,repo,1.0,tmp_path)
    assert result['round_trips']==1
    assert result['simulator_round_trips']==99
    assert result['win_rate']==100
    assert result['expected_payoff']>0
    assert result['qualification']['minimum_roundtrips']['status']=='FAIL'
    assert result['qualification']['expected_payoff']['status']=='PASS'
    assert any('differs from TradeSim' in warning for warning in result['warnings'])


def test_simulator_errors_are_not_reported_as_clean_success(tmp_path):
    repo=OfficialRepo(tmp_path,tmp_path/'python.exe','3.13.1','abc',False)
    value=normalize_result({'daily':[],'errors':['rejected order']},'r1','S',[],'hash',tmp_path,tmp_path,repo,0,tmp_path)
    assert value['status']=='completed_with_errors'


def test_comparison_keeps_engine_values_separate():
    row=compare_results({'ending_equity':10,'return':.1,'cost':2},{'dates':['2026-01-01'],'final_portfolio_value':12,'net_return':.2})
    assert row['research_ending_equity']==10
    assert row['official_ending_equity']==12
    assert row['official_cost'] is None
    assert row['dimensions']['return']['status']=='DIVERGENCE'
    assert row['dimensions']['signals']['status']=='UNKNOWN'
    assert row['cause_attribution'].startswith('UNKNOWN')
from types import SimpleNamespace

def test_missing_official_interpreter(tmp_path):
    root=tmp_path/'tools'/'kgi_tradesim'; root.mkdir(parents=True)
    (tmp_path/'.venv-kgi313'/'Scripts').mkdir(parents=True)
    with pytest.raises(BridgeError, match='OFFICIAL_VENV_MISSING'):
        core.inspect_official(root)


def test_wrong_official_python_version(tmp_path, monkeypatch):
    root=tmp_path/'tools'/'kgi_tradesim'; root.mkdir(parents=True)
    (tmp_path/'.venv-kgi313'/'Scripts').mkdir(parents=True)
    (tmp_path/'.venv-kgi313'/'Scripts'/'python.exe').touch()
    monkeypatch.setattr(core.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='3.13.16\n',stderr=''))
    with pytest.raises(BridgeError,match='OFFICIAL_PYTHON_WRONG_VERSION'):
        core.inspect_official(root)


def _mock_bridge_inputs(tmp_path, monkeypatch):
    root=tmp_path/'official'; root.mkdir(); research=tmp_path/'research'; research.mkdir()
    official=core.OfficialRepo(root,Path('official-python'),'3.13.0','official-commit',False)
    (root/'strategy').mkdir(parents=True)
    (root/'strategy'/'Example_strategy.py').write_text('class Example_strategy: pass',encoding='utf-8')
    monkeypatch.setattr(core,'inspect_official',lambda _:official)
    monkeypatch.setattr(core,'list_dates',lambda _:[{'dates':['2026-09-09']}])
    monkeypatch.setattr(core,'_git_state',lambda _:{'commit':'research-commit','dirty':True})
    monkeypatch.setattr(core,'_git_metadata',lambda _:{'commit':None,'dirty':None,'status':'NOT_A_GIT_ROOT'})
    monkeypatch.setattr(core.uuid,'uuid4',lambda:SimpleNamespace(hex='12345678abcd'))
    return root,research,official


def test_subprocess_uses_official_python_and_captures_logs(tmp_path,monkeypatch):
    root,research,_=_mock_bridge_inputs(tmp_path,monkeypatch)
    monkeypatch.setenv('SETTRADE_APP_SECRET','should-not-cross-process')
    monkeypatch.setenv('BRIDGE_TEST_SAFE_FLAG','kept')
    def fake_run(cmd,**kwargs):
        assert cmd[0]=='official-python'
        assert 'SETTRADE_APP_SECRET' not in kwargs['env']
        assert kwargs['env']['BRIDGE_TEST_SAFE_FLAG']=='kept'
        out=Path(cmd[cmd.index('--output-dir')+1])
        (out/'official_result.json').write_text(json.dumps({'daily':[{'Cash Balance':10,'Net Asset Value':11,'Portfolio Total Return':1,'Benchmark Return':0}],'transactions':[]}))
        return SimpleNamespace(returncode=0,stdout='out',stderr='err')
    monkeypatch.setattr(core.subprocess,'run',fake_run)
    result=core.run(root,research,['2026-09-09'])
    assert result['status']=='success'
    assert Path(result['metadata']['stdout']).read_text()=='out'
    assert Path(result['metadata']['stderr']).read_text()=='err'


def test_nonzero_official_exit_is_failure(tmp_path,monkeypatch):
    root,research,_=_mock_bridge_inputs(tmp_path,monkeypatch)
    monkeypatch.setattr(core.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=2,stdout='bad out',stderr='bad err'))
    with pytest.raises(BridgeError,match='TRADESIM_RUN_FAILED'):
        core.run(root,research,['2026-09-09'])


def test_missing_result_file_is_failure(tmp_path,monkeypatch):
    root,research,_=_mock_bridge_inputs(tmp_path,monkeypatch)
    monkeypatch.setattr(core.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='',stderr=''))
    with pytest.raises(BridgeError,match='RESULT_PARSE_FAILED'):
        core.run(root,research,['2026-09-09'])


def test_timeout_preserves_run_logs(tmp_path,monkeypatch):
    root,research,_=_mock_bridge_inputs(tmp_path,monkeypatch)
    def timeout(*a,**k): raise core.subprocess.TimeoutExpired('cmd',1,output='partial')
    monkeypatch.setattr(core.subprocess,'run',timeout)
    with pytest.raises(BridgeError,match='TRADESIM_RUN_TIMEOUT'):
        core.run(root,research,['2026-09-09'])
    assert list((research/'artifacts'/'official_tradesim_runs').glob('*/stderr.log'))


def test_unavailable_date_fails_before_launch(tmp_path,monkeypatch):
    root,research,_=_mock_bridge_inputs(tmp_path,monkeypatch)
    monkeypatch.setattr(core.subprocess,'run',lambda *a,**k:pytest.fail('subprocess should not run'))
    with pytest.raises(BridgeError,match='TICK_DATE_NOT_AVAILABLE'):
        core.run(root,research,['2026-01-01'])


def test_runner_has_no_cross_repository_import():
    runner=Path(core.__file__).with_name('official_runner.py').read_text(encoding='utf-8')
    assert 'from src.' not in runner and 'import src.' not in runner
