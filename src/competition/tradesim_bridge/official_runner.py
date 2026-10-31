"""Thin official-process runner. Runs only inside the official Python environment."""
import argparse, importlib.util, json, os, sys
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--official-root',required=True); ap.add_argument('--run-id',required=True)
    ap.add_argument('--strategy',required=True); ap.add_argument('--dates',nargs='+',required=True)
    ap.add_argument('--version', default='0.2.6')
    ap.add_argument('--output-dir',required=True); a=ap.parse_args()
    root=Path(a.official_root).resolve(); out=Path(a.output_dir).resolve(); sys.path.insert(0,str(root))
    from tradeSim import TradeSim, StrategyHandler
    observer = None
    if a.version == '0.2.7':
        from tradeSim import Order, CommissionService
        from observation import OrderObserver
        observer = OrderObserver(Order.order, CommissionService.commissionService)
    strategy_path=Path(a.strategy).resolve(); spec=importlib.util.spec_from_file_location(strategy_path.stem,strategy_path)
    if spec is None or spec.loader is None: raise RuntimeError(f"Cannot load candidate strategy: {strategy_path}")
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    cls=getattr(module,strategy_path.stem,None)
    if cls is None: raise AttributeError(f"Strategy class must be named {strategy_path.stem}")
    all_daily=[]; all_tx=[]; all_orders=[]; start_cash=10_000_000.0
    for day in a.dates:
        path=root/'marketInfo'/'ticks'/f'{day}.csv'
        df=pd.read_csv(path); df['TradeDateTime']=pd.to_datetime(df['TradeDateTime'])
        actual=sorted({x.date().isoformat() for x in df['TradeDateTime'].dropna()})
        if actual != [day]: raise ValueError(f"Requested date {day}, but {path.name} contains {actual}")
        ticks={s:g.to_dict('records') for s,g in df.groupby('ShareCode')}
        sim=TradeSim.tradeSim(a.run_id,current_date=df['TradeDateTime'].dt.date.iloc[0])
        if observer is not None:
            observer.attach(sim.execution)
        runner=sim.get_strategy_runner(); handlers={s:StrategyHandler.StrategyHandler(cls,runner,strategy_path.parent) for s in ticks}
        for i in range(max(map(len,ticks.values()))):
            for symbol,rows in ticks.items():
                if i>=len(rows): continue
                row=rows[i]; handlers[symbol].process_row(row)
                if not sim.isOrderbooksEmpty(): sim.isMatch(row)
                sim.update_market_prices({row['ShareCode']:row['LastPrice']})
        # TradeSim creates a fresh in-memory order book for each day. Capture
        # the residual before explicitly clearing it so the bridge can report
        # EOD cancellation without carrying orders into the next session.
        for order in ([] if observer is not None else list(sim.execution.Orders_Book)):
            requested = int(order.get_volume())
            remaining = int(order.get_remaining_volume())
            filled = requested - remaining
            all_orders.append({
                'order_id': order.get_order_number(), 'symbol': order.get_symbol(),
                'side': order.get_side(), 'order_type': order.get_order_type(),
                'requested_quantity': requested, 'filled_quantity': filled,
                'remaining_quantity': remaining,
                'status': 'PARTIALLY_FILLED_EOD_CANCELED' if filled else 'EOD_CANCELED',
                'placed_timestamp': order.get_formatted_placed_timestamp(),
                'day': day,
            })
        sim.cancel_all_orders()
        sim.flushTransactionLog(); sim.flushErrorLogger(); sim.create_transaction_summarize(a.run_id)
        snapshots=sim.portfolio.daily_snapshots; begin=snapshots[0]['date'] if snapshots else str(df['TradeDateTime'].dt.date.iloc[0])
        sim.save_summary_csv(df['TradeDateTime'].dt.date.iloc[0],university_start_date=begin); sim.save_portfolio()
        info=runner.get_portfolio_info(); info['Date']=day; all_daily.append(info)
    folder=root/'result'/a.run_id
    summary=pd.read_csv(folder/f'{a.run_id}_portfolio_summary.csv')
    transactions_path=folder/f'{a.run_id}_transaction_log.csv'
    transactions=pd.read_csv(transactions_path).to_dict('records') if transactions_path.exists() else []
    portfolio=json.loads((folder/f'{a.run_id}_portfolio.json').read_text(encoding='utf-8'))
    error_file=folder/f'{a.run_id}_error_log.txt'
    errors=[line.strip() for line in error_file.read_text(encoding='utf-8',errors='replace').splitlines() if '[ERROR]' in line] if error_file.exists() else []
    raw={'start_cash':start_cash,'daily':summary.tail(len(a.dates)).to_dict('records'),
         'transactions':transactions,'orders':observer.snapshot() if observer else all_orders,
         'rejected_orders':observer.rejections if observer else [],
         'positions':portfolio.get('stocksList',portfolio.get('positions')),
         'round_trips':portfolio.get('round_trips',[]),'daily_snapshots':portfolio.get('daily_snapshots',[]),
         'portfolio_state':portfolio,'errors':errors,'warnings':[]}
    (out/'official_result.json').write_text(json.dumps(raw,indent=2,default=str),encoding='utf-8')
    print(json.dumps({'days':len(a.dates),'fills':len(transactions),'run_id':a.run_id}))

if __name__=='__main__': main()
