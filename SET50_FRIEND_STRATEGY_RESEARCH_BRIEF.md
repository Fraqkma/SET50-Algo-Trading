# SET50 Strategy Research Lab — Friend Assignment & Hypothesis Backlog

**Version:** 2026-10-31  
**Language:** Thai brief with English technical terminology  
**Use:** ส่งให้เพื่อนทำงาน Strategy Research แบบอิสระ ขณะที่ทีมหลักทำ Core Engineering, Data, Collector, TradeSim และ Competition Cockpit

> **เป้าหมาย:** ค้นหา *hypotheses* ที่มีเหตุผลและหลักฐานว่าคาดหวังผลตอบแทนสุทธิเป็นบวกใน SET50 โดยไม่แอบใช้ข้อมูลอนาคตหรือทำให้ Backtest สวยผิดจริง **รายการนี้เป็นสมมติฐานให้ทดลอง ไม่ใช่สัญญาณที่ยืนยันแล้ว**

## 1. Context ที่ทุกคนต้องเข้าใจตรงกัน

- แข่ง KGI SET50 **16 ธ.ค. 2026 – 15 ม.ค. 2027**, ปฏิทินปัจจุบัน **21 trading sessions**; starting portfolio **10,000,000 THB**.
- รางวัลหลัก **Best Alpha** และรอง **Best Risk Control**. 6–7% ตลอดการแข่งขันเป็น *aspirational only* ไม่ใช่ target สำหรับจูนพารามิเตอร์.
- Common Criteria ที่ผู้จัดระบุ: Portfolio MDD **< 1.5 × Benchmark MDD**, อย่างน้อย **5 completed FIFO round-trips**, average EOD exposure **≥50%**, expected payoff **>0**. Best Alpha ยังมีเงื่อนไขผลตอบแทนและ excess return ไม่ติดลบ.
- กฎ TradeSim 0.2.7: IOC, one-tick adverse fill-price mechanics, limited by relevant tick volume, valid tick-size ladder (เปลี่ยน 16 พ.ย. 2026), no auction fills. ไม่ถือว่าคำสั่งส่งแล้วจะ filled เสมอ.
- Phase 5: **NO_SIGNAL_PASSED_PROMOTION_GATE**, no approved independent OOS, current fully approved PIT event universe **18 names**; 42 additional identities `NEEDS_REVIEW`. Never expand symbol/date coverage without dated, auditable PIT evidence. INTUCH excluded by existing gate. Official TradeSim series and Settrade production series are **not interchangeable**.
- Official tick history locally is short (13 October 2026 sessions plus separate September practice ticks); raw historical BBO is unavailable via current Settrade API. Intraday ideas are mainly feasibility/prospective pilots until data warrants otherwise.
- Previous failed/insufficient baselines include Trend20, Breakout20, RelativeStrength, MeanRev5, S3-A/B/C/D. Research the actual definitions before duplicating them. Re-running the same variants with new labels is not independent confirmation.
- Budget for buying data = **0 THB**. No new paid subscriptions. No real brokerage orders.

## 2. Data feasibility labels

- **D** = Can start on existing, approved, PIT-valid daily stock OHLCV *if the specific fields and coverage are confirmed*; research-only daily approximate fills.
- **I** = Also requires aligned, source-audited historical SET50 Price Index daily closes; do not merge inconsistent price feeds silently.
- **T** = Requires actual official tick / intraday observations; current dates limited. Mechanical/research diagnostic only, not independent OOS proof.
- **E** = Requires reliable, freely available, *point-in-time* dated sector/fundamental/corporate event/flow data; otherwise BLOCKED.
- **B** = Requires historical bid/offer order-book data; **currently BLOCKED** for historical alpha claims. Prospective-only if legally available from future collector.

**Research status labels:** `BACKLOG`, `PRE_REGISTERED`, `DATA_BLOCKED`, `EXPLORATORY_ONLY`, `REJECTED`, `PROMOTION_ELIGIBLE` (last one requires independent new evidence). Always record prior inspected data.

## 3. First wave — choose a small, diversified set (suggested 8)

เลือกกระจายคนละ market mechanism ไม่ใช่ 8 ค่า period ของ RSI เดียวกัน:

1. **RS-02 — Residual Strength vs Market** (D+I): after subtracting beta/market exposure, does idiosyncratic strength persist?
2. **RS-05 — Leadership Persistence by Dispersion** (D+I): is ranking persistence conditional on cross-sectional dispersion?
3. **TR-03 — Trend Pullback Recovery** (D): in established trends, do modest pullbacks resume faster than unfiltered dips?
4. **MR-03 — Market-Conditioned Oversold Bounce** (D+I): does the same short-term selloff behave differently during stable vs distressed index regimes?
5. **GP-02 — Gap With Prior-Day Liquidity** (D): can the sign of an overnight gap plus *prior* liquidity help separate continuation/reversal?
6. **VL-03 — Volume Shock × Return Sign** (D): does unusual prior-day turnover have information conditional on price direction?
7. **RG-02 — Volatility-Adjusted Rotation** (D+I): conditional long-only allocation among approved PIT names, with realistic turnover.
8. **EX-02 — IOC Sizing vs Tick Volume** (T): determine what order sizes plausibly survive volume constraints without claiming statistical alpha.

**STOP RULE:** อย่ารันทั้ง backlog เพื่อหา parameter ที่ให้กำไรสูงสุด. ให้ register hypothesis, controls, entry clock, horizons, fees, failure criteria **ก่อนเปิดผลตอบแทนอนาคต**. หากเป็นข้อมูลที่เคยเห็นแล้ว ให้บอกว่าเป็น exploratory ไม่ใช่ OOS.

## 4. Hypothesis backlog — 58 research ideas

> ระดับความสำคัญ: **P1** เริ่มตรวจสอบได้และมีคำถามเชิงเศรษฐศาสตร์ชัด; **P2** สำรวจรองเมื่อทรัพยากรถึง; **P3** ต้องการข้อมูลเพิ่มหรือเป็น engineering/diagnostic. ชื่อไม่ใช่คำรับรองว่ามี edge.

### A. Relative Strength / Cross-Sectional Leadership

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| RS-01 | P2 · D | **Simple 5/10/20-day cross-sectional relative strength** เทียบหุ้นที่แรงสุดกับ random/equal-weight basket | **Replication baseline** (prior RelativeStrength failed); use fixed comparator and report net costs |
| RS-02 | P1 · D+I | **Residual strength** หักผลตอบแทนดัชนีหรือ beta โดยใช้ข้อมูลถึง t เท่านั้น | Predict forward return after beta adjustment, not just positive market exposure |
| RS-03 | P2 · D | **Acceleration vs level** หุ้นที่แรงขึ้นต่อเนื่อง เทียบหุ้นที่แรงอยู่แล้ว | Is change in rank more informative than rank alone? |
| RS-04 | P2 · D | **Rank stability** หุ้นที่ติด top quantile ติดต่อกันหลายวัน | Test turnover benefit and avoid overlapping pseudo-independent events |
| RS-05 | P1 · D+I | **Leadership under high/low dispersion** เลือกหุ้นเด่นเมื่อทั้งตลาดกระจายแรง/อ่อน | Does effect survive matched dispersion/regime controls? |
| RS-06 | P2 · D+I | **Market-down relative winners** หุ้นตกน้อยกว่า index ในวันตลาดแย่ | Do defensive relative winners recover or merely have lower beta? |
| RS-07 | P3 · E | **Sector leadership rotation** หุ้นเด่นใน sector ที่เพิ่งนำตลาด | Needs point-in-time sector map; sector labels from today's list alone may leak |

### B. Trend / Breakout / Volatility Structure

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| TR-01 | P2 · D | **Multi-scale trend agreement** 5/20-day slope agree vs conflict | Predefine only a few regimes; avoid dozens of moving-average grids |
| TR-02 | P2 · D | **Breakout retention** close holds above *previously known* rolling high | Prior Breakout20 lost; test new mechanism explicitly and benchmark costs |
| TR-03 | P1 · D | **Pullback within uptrend** ย่อระยะสั้นในหุ้นขาขึ้น | Matched comparison to dip buys without established trend; 1–10-day curve |
| TR-04 | P2 · D | **Trend exhaustion** price stretch from rolling median vs subsequent reversal | Compare trend continuation and reversal; predeclare direction |
| TR-05 | P2 · D | **Range contraction followed by expansion** volatility squeezed vs subsequent movement | Audit overlap with S3-A and any existing volatility hypothesis before running |
| TR-06 | P2 · D | **Breakout false-start** failed breakout measured only *after observable failure* | No hindsight “failure” selection; entry after the failure is known |
| TR-07 | P2 · D | **Trend quality / efficiency ratio** smooth directed movement vs noisy movement | Differentiate from simple momentum with matched return magnitude |

### C. Conditional Mean Reversion / Dislocation

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| MR-01 | P2 · D | **Short-horizon reversal after 1-day shock** | Replication control for failed MeanRev5; do not promote on seen data |
| MR-02 | P2 · D | **Two-step selloff vs one-day crash** same cumulative loss, different path | Is recovery dependent on shock structure, after controlling volatility? |
| MR-03 | P1 · D+I | **Index-regime-conditioned reversal** same oversold stock, market calm vs stress | Test interaction term against matched unconditional MeanRev5 |
| MR-04 | P2 · D | **Idiosyncratic oversold vs market-driven drop** | Requires credible market adjustment, distinct from simply low-beta selection |
| MR-05 | P2 · D | **Close-near-low capitulation vs ordinary decline** | Next-session entry only; candle close location known at day end |
| MR-06 | P2 · D | **Volume-confirmed exhaustion after downside shock** | One *predeclared* volume filter, not retrofitted to best winners |
| MR-07 | P3 · D | **Relative pair dislocation** two approved stocks that historically co-move | Shorting/neutral-leg assumption may be unavailable; long-only version only if justified |

### D. Overnight Gap / Daily Price-Action Anatomy

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| GP-01 | P2 · D | **Gap continuation vs fade** close(t−1) to open(t) | Replicate prior gap research first; no same-open fill after observing open without latency |
| GP-02 | P1 · D | **Gap × prior-day turnover** does preceding liquidity condition gap persistence? | Features known before/at entry only; gap sign requires observing open |
| GP-03 | P2 · D+I | **Gap aligned/opposed to previous index move** | No leakage of same-day index close; align lagged index data |
| GP-04 | P2 · D | **Large-range close-location** near-high close vs near-low close | Matched control for volatility and raw daily return |
| GP-05 | P2 · D | **Inside day then breakout** range compression → subsequent move | Define breakout using only *prior* ranges; no fill assumed at known high |
| GP-06 | P2 · D | **Long-wick rejection** wick-to-body ratio → next-session reversal | Daily bar cannot establish intraday order of touch points |

### E. Volume / Turnover / Liquidity

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| VL-01 | P2 · D | **Relative volume (RVOL) anomaly** today vs trailing known average | Compare against raw return matched controls; earlier S3-D may overlap |
| VL-02 | P2 · D | **Quiet-volume trend** rising prices with declining turnover | Detect if trend failure risk rises; predeclare direction |
| VL-03 | P1 · D | **Volume shock × return sign** abnormal volume on up-day vs down-day | Separate directional and absolute-volume effects; cluster by day/symbol |
| VL-04 | P2 · D | **Dollar turnover participation feasibility** order sizing as share of measured liquidity | Liquidity screen, not proof of executable IOC fills |
| VL-05 | P2 · D | **Price movement per unit turnover** illiquidity / price impact proxy | May mechanically favor illiquid symbols; compare realistic tick-size stress |
| VL-06 | P3 · T | **Trade-rate bursts** ticks/min and recent trades predicting near-term movement | Limited event window; no independent OOS; account for timestamp duplicates |

### F. Regime / Risk / Portfolio Construction

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| RG-01 | P2 · D+I | **Market trend state** index risk-on/risk-off from prior closes | Market timing by itself may fail ≥50% average exposure |
| RG-02 | P1 · D+I | **Volatility-adjusted rotation** balance stock ranks with forecast vol | Evaluate net turnover, exposure, MDD, and >=5 round trips, not just Sharpe |
| RG-03 | P2 · D+I | **High-dispersion vs low-dispersion basket** performance conditional on universe dispersion | PIT composition changes must not use future membership |
| RG-04 | P2 · D | **Correlation-aware basket** stock selection with correlation penalty | 18-name universe creates estimation error; covariance shrinkage only if preregistered |
| RG-05 | P2 · D | **Risk budget / inverse-vol weights** equal-weight vs inverse-vol, same signals | Construction-only benchmark, not independent alpha signal |
| RG-06 | P2 · D+I | **Defensive cash-floor vs qualification exposure** optimize rule robustness near ≥50% | Need actual EOD NAV/fills; daily feasibility alone not qualification proof |
| RG-07 | P2 · D | **Holding horizon distribution / competing risk** H=1/2/3/5/7/10/15 | Reuse Phase 4 report as baseline; don't select ex-post best exit |

### G. Calendar / Corporate Events (mostly conditional)

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| EV-01 | P2 · D | **Weekday return pattern** effect on short-term continuation | Many date/holiday clusters; low effective sample size |
| EV-02 | P2 · D | **Month-turn positioning** last/first trading days of month | Must compare to date-matched placebo; very few independent months |
| EV-03 | P3 · E | **Earnings announcement drift** price response after timestamped public disclosure | Requires actual public release timestamps / surprise known then; blocked without them |
| EV-04 | P3 · E | **Ex-dividend / corporate-action event** adjusted-price / entitlement timing | Require true announcement/action-date PIT data; do not mistake price adjustment for signal |
| EV-05 | P3 · E | **Index membership change event** announcement versus effective date | Must use historically announced membership, proper eligibility & corporate changes |
| EV-06 | P3 · E | **Free official investor-flow events** institutional/foreign net flow vs next-session | Need reliable issuer/market timestamps; avoid backdated and aggregate leakage |

### H. Intraday Tick / Order Book (explicitly limited)

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| TK-01 | P3 · T | **Morning vs afternoon return continuation** within a trading day | Align actual session breaks, exclude auctions, use entry after observation |
| TK-02 | P3 · T | **Short-horizon trade-rate and price impulse** | 13 Oct sessions alone = diagnostics, not strong alpha evidence |
| TK-03 | P3 · T | **Tick volatility burst and snap-back** | Event-time market microstructure, timestamp duplicates not blindly dropped |
| TK-04 | P3 · T | **Round-number / valid tick ladder response** | Respect exchange tick-size change on Nov 16 and official fill rules |
| TK-05 | P3 · B | **Top-of-book imbalance predictability** | BLOCKED for historical claims; prospective collection only |
| TK-06 | P3 · B | **Spread/depth regime filter** | BLOCKED for historical claims; no synthetic order books |
| TK-07 | P3 · T | **First liquid trade after opening auction** | Do not assume auction prints are executable if TradeSim excludes auctions |

### I. Execution / Qualification Feasibility (not alpha claims)

| ID | Priority / Data | Experiment / สิ่งที่ลอง | Key test / failure condition |
|---|---|---|---|
| EX-01 | P2 · T | **Order time grid** after signal becomes observable | Compare accepted/IOC-cancelled/fill quantities, not just slippage |
| EX-02 | P1 · T | **Order sizing vs tick volume** possible filled proportions for different participation caps | Tests actual official 0.2.7 constraint; don't generalize 13 days to competition |
| EX-03 | P2 · T | **Limit price distance / tick ladder validity** one, two or more valid ticks | Fill price not guessed from OHLC; obey actual simulator rules |
| EX-04 | P2 · D+T | **Turnover break-even edge** required per trade before fee + one/two-tick stress | Economics / necessary hurdle, not a fill forecast |
| EX-05 | P2 · D+T | **Competition 21-day roundtrip/exposure feasibility** under H=1–15 | Stress incomplete fills, exits, end boundary, ≥5 FIFO roundtrips, ≥50% exposure |

**Total: 7 + 7 + 7 + 6 + 6 + 7 + 6 + 7 + 5 = 58 hypotheses/engineering investigations.**

## 5. How to run a scientifically useful experiment

### Before testing — one-page preregistration per independent hypothesis

1. `hypothesis_id`, purpose, economic mechanism, intended *direction* (long-only if no short permission).
2. Data source, version/hash, timestamp range, PIT universe and every exclusion reason.
3. Information clock: precise time features become observable.
4. Entry/exit rule, maximum holding horizon, cash/exposure, symbol/position limit.
5. Baseline/negative control: market-only, matched return-volatility-volume controls, randomized basket, and prior failed baseline as relevant.
6. One primary endpoint; optional secondary H curve (1/2/3/5/7/10/15). Do not select best H post hoc and call it OOS.
7. Cost scenario(s): configured fees+VAT, one adverse tick per side, further stressed two ticks and higher fees; for daily OHLCV mark **execution approximation only**.
8. Planned effect size, minimum events and *effective* independent date/symbol clusters; CI by dependence-aware bootstrap, not naive event count.
9. Fixed splits; existing Phase 3/4/5 inspected period is *research seen*, not untouched holdout. Use genuinely subsequent, time-stamped samples for prospective confirmation.
10. Multiplicity: account for all tested hypotheses/horizons/screen variants (Holm/FDR + registry); store every failed test.
11. Predefined rejection reasons and a `DATA_BLOCKED` status if no valid observations.
12. Git/code revision, seed, reproducible command and complete output locations.

### Suggested practical return conventions

- For an EOD signal at close(t), first feasible **next** entry is after the signal becomes observable (e.g., next open with explicitly acknowledged fill approximation); never buy at close(t) using close(t) to decide.
- If a signal depends on open(t) or intraday flow(t), model latency and first permissible next tick. A daily open cannot be both an observed input and guaranteed fill at the same instant.
- Corporate-action effects, holidays, missing bars, adjustments and PIT membership changes must be explicit.
- Report **gross**, **fee-only net**, **1-tick-adverse stress**, **2-tick-adverse stress**, and **not-computable** where inputs are insufficient.
- Do not infer path-dependent stop loss / take profit order from daily OHLC when both levels are touched within one bar.
- Do not mix Settrade and TradeSim values unless audited as distinct source-specific experiments.
- For signal quality: mean/median matched uplift, clustered 95% CI, multiple-test adjusted p-values, positive fraction, sample support, horizon distribution, regime breakdown, and sensitivity to 1–2 high-impact symbols/dates.
- For portfolio feasibility: net cumulative return, EOD NAV MDD, index excess return, Calmar, exposure, FIFO completed round trips, win rate, expected payoff, rejected order %, estimated commission/tick burden; **unknown** for qualification metrics that require unobserved fills.

### Correct gate

- **G0:** Data/source/PIT and time availability passed. Else `DATA_BLOCKED`.
- **G1:** Sufficient effect evidence vs matched control accounting for dependence and multiplicity. Else `REJECTED` / `INCONCLUSIVE`.
- **G2:** Effect survives conservative costs/tick sensitivity and simple counterfactual baselines. Else `NOT_EXECUTABLE`.
- **G3:** Truly untouched chronological/prospective evidence available and supportive. Else `AWAITING_OOS`.
- **G4:** Real official 0.2.7 tick-level replay, valid order fills, qualification feasibility, and human review. No autonomous final strategy choice.

A result that *fails* is a valuable deliverable, not a reason to hide it. More variants on the same seen dataset do not repair weak evidence.

## 6. Division of responsibility

**Friend — Strategy Research Lab (own folder/branch, independent workspace):**
- Select small batches of genuinely different hypotheses from this backlog, preregister, code, run, preserve results and failure reasons.
- Reproduce precisely one existing baseline to prove compatibility before any new screening.
- Deliver reproducible, source-aware signal results and evidence files; never mutate core datasets, collector, competition metrics, or official simulator code.
- Use read-only **approved** research data snapshots and immutable source manifest; request missing data by schema rather than sourcing questionable substitutes.

**You + Codex — Core / Data / Execution:**
- PIT/data identity audits, collector, holidays, corporate actions, scoring, TradeSim 0.2.7, fill mechanics, official allowed universe, Cockpit and integration.
- Review friend contributions through diff/report; independently reproduce before promotion.
- Own final strategy selection decision.

**Integration rule:** A friend's apparently profitable equity curve is **not automatically eligible**. Keep friend outputs in `research_external/<researcher>/<hypothesis_id>/` or separate repo and ingest via read-only review; maintain provenance. Do not touch the other official competition submission repo. Do not send passwords/tokens or broker credentials. Check dataset sharing/license rules before forwarding organizer/market-data archives externally.

## 7. Deliverables per hypothesis (give this template to friend)

```text
Hypothesis ID:
Researcher:
Date preregistered:
Economic idea and expected direction:
Data source/version/hash + period + PIT membership:
Eligibility/missingness:
Exact feature timestamp and entry timing:
Baseline and matched-control design:
Fixed parameter set / horizons:
N events / N symbols / N dates / effective N:
Gross return and matched uplift:
Fee-only net:
One-tick / two-tick stress:
Clustered confidence interval / multiplicity-adjusted significance:
Overlapping events / symbol dependence:
Holding-period distribution:
Chronological OOS status:
Official simulator replay status:
Qualification feasibility (5 RT / 50% EOD exposure / MDD / payoff):
Failure reasons and caveats:
Code path, source hash, reproducible command:
Decision: REJECTED / INCONCLUSIVE / DATA_BLOCKED / AWAITING_OOS / HUMAN_REVIEW_READY
```

### Mandatory final bundle

- `README.md` — idea, how to run, limitations
- `hypothesis_spec.json` — preregistration, frozen parameters
- `data_manifest.json` — snapshot provenance and PIT choices
- `events.csv` or `.parquet` — time-stamped signal events, no future features
- `summary.json` — matched effects, uncertainty, cost scenarios, negative results
- `tests/` — timestamp/no-lookahead/source consistency, repeatability, negative controls
- `decision.md` — human-readable short verdict and follow-up

## 8. Practical first 2 research cycles

**Cycle A — setup and sanity (no alpha claim):**
1. Read previous approved signal specs, especially S3-A/B/C/D and RelativeStrength/MeanRev5.
2. Implement a read-only adapter to approved PIT snapshot; display coverage/exclusion matrix.
3. Reproduce *one* prior baseline exactly (same features, sample, matched controls, seed, cost).
4. Register **two** distinct hypotheses among RS-02, MR-03, TR-03, VL-03 and freeze primary endpoint/controls.
5. Test and publish **all results**, including rejection; do not run a parameter sweep.

**Cycle B — only if Cycle A evidence and data warrant:**
1. Register at most two further different mechanisms (e.g., GP-02 and RS-05).
2. Add clustered uncertainty, time split, cost stress, cross-symbol robustness.
3. Confirm no valid independent OOS exists today; set `AWAITING_OOS` if appropriate.
4. Share code/report with core project for independent reproduction before official replay.

**What success looks like:** A rigorous `REJECTED` with reproducible code is better than an unexplained +20% Backtest. If only old data is used, report a prioritized *prospective* validation plan rather than `confirmed edge`.

## 9. Public background literature (inspiration, not SET50 validation)

- Jegadeesh & Titman (1993), *Returns to Buying Winners and Selling Losers*, https://doi.org/10.1111/j.1540-6261.1993.tb04702.x — medium-horizon cross-sectional momentum, not proof for 1–5 day SET50.
- Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum*, https://doi.org/10.1016/j.jfineco.2011.11.003 — trend persistence in liquid futures, not transferability guarantee to Thai stocks.
- Lo & MacKinlay (1990), *When Are Contrarian Profits Due to Stock Market Overreaction?*, https://doi.org/10.1093/rfs/3.2.175 — contrarian effects and cross-stock lead/lag.
- Fink (2021), *A review of the Post-Earnings-Announcement Drift*, https://doi.org/10.1016/j.jbef.2020.100446 — earnings hypotheses require timestamped releases.
- SET trading hours, https://www.set.or.th/en/market/information/trading-procedure/trading-hours — two regular sessions; auction periods exist.
- SET opening/closing price mechanism, https://www.set.or.th/en/market/information/trading-procedure/opening-closing-price-calculation — auctions and price formation differ from continuous trades.

**Note:** Public papers are idea sources only, not evidence of SET50 alpha; all experiments require independent local verification.

---

## 10. Copy-paste assignment to researcher (short)

> ช่วยทำ SET50 Strategy Research Lab ให้แยกจาก Core งานหลักของทีม โดยอ่าน brief นี้ทั้งหมด เริ่มจาก replicate baseline เดิมให้ตรง 1 ตัวก่อน จากนั้นเลือก 2 สมมติฐาน **ต่างกลไก** ใน first wave แล้วทำ pre-registration ก่อนทดสอบ ใช้เฉพาะ approved point-in-time research data; ถ้าไม่มีข้อมูลให้ติด DATA_BLOCKED ห้ามแทนด้วยข้อมูลคนละแหล่ง ห้ามใช้ข้อมูลอนาคต ห้ามจูนเพื่อกำไร 6–7% บนข้อมูลชุดเดิม ต้องรายงาน matched controls, event counts, effective sample size, clustered CI, transaction costs, adverse-tick sensitivity, holding period distribution, OOS status และ negative results ด้วย ส่ง code + manifest + reproducible command + summary พร้อมรายการสิ่งที่ยังพิสูจน์ไม่ได้ โดยยังไม่เลือก strategy จริงและไม่แก้ core collector/official repo/ส่งคำสั่งซื้อขายจริง
