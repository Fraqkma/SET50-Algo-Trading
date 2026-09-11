# Strategy Research Record: Design A with a Limited Design C Component

เอกสารนี้บันทึก research direction ที่กำลังเสนอ ยังไม่ใช่ผล Backtest และไม่ใช่การอนุมัติ strategy สุดท้าย

## Current implementation

ข้อมูล production research ต้องมาจาก `load_approved_market_data()` และผ่าน `MarketDataEligibilityGate` ทุกวันที่นำมาใช้ วิธีนี้รักษา historical SET50 membership, approved date ranges, known gaps และ identity policies โดยไม่แก้ raw data

`build_features()` สร้าง feature แบบ deterministic จากข้อมูลถึงวัน `t` เท่านั้น ส่วน `BaselineStrategy` เป็น Design A: ตัดสินแต่ละ symbol จากประวัติของตัวเอง

เพิ่ม `rank_time_series_candidates()` เป็นส่วน Design C ขนาดเล็กเท่านั้น ฟังก์ชันนี้:

1. ตรวจ eligibility ของ `(symbol, date)` ผ่าน gate
2. ใช้ time-series baseline filter (`momentum_20 > 0` และ `close > sma_20`)
3. จัดอันดับผู้ที่ผ่าน filter ด้วย `momentum_20` จากมากไปน้อย
4. ใช้ symbol เป็น deterministic tie-breaker และคืน top `N`

ฟังก์ชันนี้ไม่จัดการ cash, position, order, rebalance หรือ Backtest execution

## Feature evaluation ก่อนการใช้งาน

| Feature | ความหมายแบบง่าย | ทำไมอาจช่วย | Assumption | Failure mode / bias | ข้อเสนอ |
|---|---|---|---|---|---|
| `daily_return` | การเปลี่ยนแปลงราคาจากวันก่อน | เป็น building block ของ momentum และ volatility | ราคาปิดรายวันสะท้อนข้อมูลที่ใช้ได้ | corporate action หรือ OHLC anomaly อาจทำให้ return ผิดรูป | **รวม** เป็น diagnostic และ input |
| `momentum_20` | ราคาวันนี้เทียบกับ 20 observations ก่อนหน้า | บอกแรงส่งของราคาตัวเดียวและใช้ relative ranking ได้ | แนวโน้มระยะสั้นมี persistence | reversal, gap และ sample สั้นทำให้สัญญาณหลอก | **รวม** เป็น Design A filter และ Design C ranking factor |
| `sma_20` | ค่าเฉลี่ยราคาย้อนหลัง 20 วัน | ลด noise และระบุว่าราคาอยู่เหนือ trend ระยะสั้นหรือไม่ | ราคาที่อยู่เหนือค่าเฉลี่ยสะท้อน trend ที่แข็งแรง | lag ทำให้เข้า/ออกช้า และ sideway ทำให้สัญญาณสลับ | **รวม** เป็น baseline filter |
| `sma_50` / `trend_20_50` | เปรียบเทียบ trend สั้นกับยาว | อาจเป็น context ของ trend/regime โดยไม่ใช้ market-regime model | trend สองช่วงช่วยแยก noise ได้ | warm-up ยาว ลดจำนวน observations และอาจ overfit หากใช้ threshold เพิ่ม | **คำนวณไว้**; ยังไม่เพิ่มเป็น mandatory signal จนกว่าจะอนุมัติ |
| `volatility_20` | ความผันผวนย้อนหลังของ daily return | ช่วยระบุความเสี่ยงและใช้เป็น risk control ภายหลัง | volatility ในอดีตเป็น proxy ของความเสี่ยงใกล้ ๆ นี้ | volatility clustering และ extreme value อาจไม่คงอยู่ | **คำนวณไว้**; ใช้รายงาน/risk control ไม่ใช่ ranking ตอนนี้ |
| `volume_sma_20` / `volume_ratio_20` | volume ปัจจุบันเทียบกับค่าเฉลี่ยของตัวเอง | ช่วยตรวจ liquidity และ confirmation | volume สูงสัมพันธ์กับความสามารถในการซื้อขาย | volume ไม่เท่ากับ liquidity จริง และอาจได้รับผลจาก event | **คำนวณไว้**; ยังไม่ใช้เป็น signal |

ค่าช่วง warm-up เป็น `NaN` และไม่มีการ forward-fill, interpolate หรือ fabricate หาก input missing/duplicate ฟังก์ชันจะหยุดด้วย error

## Proposed feature set

ชุดเล็กที่เสนอสำหรับ research รอบแรกคือ:

- **Primary Design A:** `momentum_20` และ `sma_20` เป็น signal filter ของแต่ละ stock
- **Limited Design C:** จัดอันดับเฉพาะ stock ที่ผ่าน Design A ด้วย `momentum_20` และเลือก top `N` ที่ human กำหนด
- **Risk context only:** รายงาน `volatility_20` และ volume features โดยยังไม่ให้สองกลุ่มนี้เปลี่ยน signal
- `daily_return`, `sma_50` และ `trend_20_50` คงไว้เพื่อ diagnostics/context และการวิจัยรอบถัดไป ไม่เพิ่มเงื่อนไขหลายชั้นโดยอัตโนมัติ

เหตุผลคือการคง baseline ที่อ่านง่ายไว้เป็น reference และเพิ่ม ranking เพียงจุดเดียวเพื่อแก้ปัญหาเมื่อมีหลาย `BUY` พร้อมกัน การเพิ่ม volatility/volume เข้า score ตอนนี้จะเพิ่ม assumptions และโอกาส overfitting โดยยังไม่มี Backtest evidence

## Timing and bias controls

- ทุก feature ณ `t` ใช้ข้อมูลไม่เกิน `t`
- cross-sectional ranking อ่านเฉพาะ row ของ `as_of` และไม่อ่าน future rows
- eligibility gate ต้องผ่านก่อน symbol/date จะเข้าร่วม universe
- universe ใช้ historical SET50 effective dates ไม่ใช่ current constituents
- signal ที่ `t` ต้องถูก execute ไม่เร็วกว่า trading row ถัดไปใน Backtest
- INTUCH/GULF, BANPU และ TIDLOR policies ยังคงเป็นของ gate ไม่ถูกแก้ด้วย ranking

## Rejected or deferred directions

- **Design B / market-regime complexity:** ยังไม่ทำ เพราะอยู่นอก scope และเพิ่ม model assumptions ก่อนมี baseline evidence
- **Machine learning / advanced statistics:** ยังไม่ทำ เพื่อให้ attribution และ no-lookahead ตรวจสอบได้ง่าย
- **Composite multi-factor score:** defer เพราะต้องกำหนด weights และ validation protocol ก่อน จึงเสี่ยง parameter search
- **Volatility/volume signal filters:** defer เป็น risk/diagnostic fields ก่อน ไม่ถือว่ามีประโยชน์เพียงเพราะคำนวณได้

## Human approvals still required

ก่อน Backtest ต้องอนุมัติ:

1. ค่า `top N` และความถี่ rebalance ของ Design C หรือยืนยันให้ใช้ Design A เพียงอย่างเดียว
2. จะใช้ `trend_20_50` เป็น mandatory filter หรือเก็บเป็น diagnostics
3. จะใช้ volatility/volume เป็น risk control ใน Backtest หรือไม่ และเกณฑ์คืออะไร
4. กฎ position sizing, holding, turnover และ handling เมื่อ candidate มีน้อยกว่า `N`
5. execution timestamp/order type ภายใต้ competition constraints
6. research period, evaluation metrics และเกณฑ์หยุดก่อนทำ optimization/OOS

ขั้นถัดไปที่เหมาะสมคือสร้าง Backtest harness ที่เปรียบเทียบ Design A กับ selector Design C ภายใต้กฎเดียวกัน โดยยังไม่ optimize parameters

## Implementation decision layer

ขณะนี้มี `rebalance_dates()` สำหรับ schedule ทุก 3 observed trading rows และ `next_trading_session()` สำหรับบังคับ signal/execution boundary แล้ว ทั้งสองฟังก์ชันไม่สร้าง orders หรือทำ Backtest รายละเอียดของ Top N, fewer-than-N handling, sizing, holding rule, order/fill assumptions และ evaluation criteria อยู่ใน `docs/STRATEGY_IMPLEMENTATION_DECISIONS.md` และยังต้องได้รับ approval ก่อนสร้าง event-ordered Backtest
