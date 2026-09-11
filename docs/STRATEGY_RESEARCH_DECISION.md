# Strategy Research Decision Point

เอกสารนี้เป็นจุดหยุดเพื่อขอความเห็นจาก human researcher ก่อนเริ่มพัฒนา strategy เพิ่มเติม เป้าหมายคืออธิบายทางเลือกให้เข้าใจง่าย ไม่ใช่การเลือก strategy สุดท้ายหรือรายงานผล Backtest

## สถานะปัจจุบันของ repository

ส่วนที่มีอยู่แล้ว:

- `src/data/eligibility.py` มี `MarketDataEligibilityGate` เป็น policy boundary สำหรับ SET50 membership, approved date range, Yahoo audit, acquisition/validation status, known gaps และ continuity rules
- `src/data/research.py` มี `load_approved_market_data()` ซึ่งคืนเฉพาะวันที่ผ่าน eligibility gate จาก approved manifest
- `src/data/features.py` มี feature แบบ causal ได้แก่ `daily_return`, `momentum_20`, `sma_20`, `sma_50`, `trend_20_50`, `volatility_20`, `volume_sma_20` และ `volume_ratio_20`
- `src/strategies/baseline.py` มี `BaselineStrategy` แบบ long-only ซึ่งสร้าง `BUY`, `HOLD` และ `EXIT` จาก momentum กับ moving average
- feature และ baseline ยังไม่ถูก Backtest และยังไม่มีการ optimize parameter หรือทำ OOS testing
- raw market data ต้องคง immutable และ downstream research ต้องใช้ approved research path เท่านั้น

ดังนั้น baseline ปัจจุบันเป็น time-series strategy ระดับ symbol เดียว ยังไม่ได้เปรียบเทียบหุ้นหลายตัวด้วย cross-sectional ranking

## 1. Time-series strategy คืออะไร

Time-series strategy ถามว่า “หุ้นตัวนี้มีสัญญาณของตัวเองหรือไม่” โดยดูประวัติของหุ้นตัวเดียว เช่น ราคาปัจจุบันสูงกว่า moving average หรือผลตอบแทนย้อนหลังเป็นบวก

ตัวอย่างกฎใน repository ปัจจุบัน:

- `BUY` เมื่อ `momentum_20 > 0` และ `Close > sma_20`
- `EXIT` เมื่อ feature พร้อมใช้แต่เงื่อนไขดังกล่าวไม่ครบ

จุดสำคัญคือแต่ละหุ้นถูกตัดสินแยกกัน หุ้นสองตัวอาจให้ `BUY` พร้อมกัน หรือไม่มีตัวใดให้ `BUY` ก็ได้

ข้อดี:

- อธิบายง่ายและตรวจสอบได้
- ไม่จำเป็นต้องพึ่งพาการกระจายค่าระหว่างหุ้นในแต่ละวัน
- เหมาะสำหรับ baseline และช่วยตรวจ feature timing/no-lookahead

ข้อเสีย:

- ในตลาดขาขึ้นอาจมี `BUY` หลายตัวจนต้องมีวิธีเลือกและจัดสรรเงินเพิ่ม
- ในตลาดอ่อนแออาจไม่มีสัญญาณ ทั้งที่บางหุ้นยังแข็งแกร่งเมื่อเทียบกับหุ้นอื่น
- threshold ของแต่ละ feature อาจไม่เหมาะกับหุ้นทุกตัว

## 2. Cross-sectional strategy คืออะไร

Cross-sectional strategy ถามว่า “ในวันเดียวกัน หุ้นตัวไหนแข็งแกร่งกว่าตัวอื่น” โดยคำนวณ feature ของหุ้นที่ eligible ในวันเดียวกัน แล้วจัดอันดับ เช่น เลือกหุ้นที่มี `momentum_20` สูงสุด 5 ตัว

ตัวอย่างลำดับ:

1. สร้าง candidate universe จาก historical SET50 membership และ eligibility gate ณ วันนั้น
2. คำนวณ feature ของทุก candidate ที่มีข้อมูลพร้อม
3. จัดอันดับด้วย momentum หรือ score
4. เลือก top `N` หรือ percentile ที่กำหนดไว้ล่วงหน้า

ข้อดี:

- เปรียบเทียบ relative strength ได้โดยตรง
- ช่วยควบคุมจำนวนหุ้นและทำให้ stock selection ชัดเจน
- ไม่ต้องตั้ง threshold เดียวที่ต้องใช้ได้กับหุ้นทุกตัว

ข้อเสีย:

- อันดับอาจเปลี่ยนบ่อย ทำให้ turnover และค่าธรรมเนียมสูง
- ต้องระวังว่า universe ของวันนั้นใช้ historical membership จริง ไม่ใช่รายชื่อ SET50 ปัจจุบัน
- หากข้อมูลของบางหุ้นขาดหาย การจัดอันดับอาจมี selection bias
- คะแนนที่ดูดีใน sample เล็กอาจเป็นเพียง noise

## 3. Hybrid Time-series + Cross-sectional strategy

Hybrid ใช้สองขั้นตอนที่มีหน้าที่ต่างกัน:

- Time-series เป็น **filter**: หุ้นต้องมีสัญญาณที่ดีของตัวเองก่อน เช่น trend เป็นบวก
- Cross-sectional เป็น **ranking/selection**: จากหุ้นที่ผ่าน filter แล้ว เลือกตัวที่แข็งแกร่งที่สุดเมื่อเทียบกับ eligible peers

ตัวอย่างลำดับการทำงานในวัน `t`:

```text
Historical SET50 membership ณ t
        ↓
Eligibility gate และ approved date range
        ↓
Time-series filters (trend/momentum/quality)
        ↓
Cross-sectional ranking ของหุ้นที่ผ่าน filter
        ↓
เลือกจำนวนหุ้นตามกฎที่ human อนุมัติ
        ↓
สร้าง signal ณ t และ execute ได้เร็วที่สุดในวันถัดไป
```

แนวทางนี้ไม่ได้เปลี่ยน INTUCH/GULF, BANPU หรือ TIDLOR policy และไม่ทำให้ข้อมูลที่ไม่ผ่าน gate กลับมา eligible

## 4. Feature families จาก daily data ปัจจุบัน

### Momentum

วัดว่าราคาปัจจุบันเปลี่ยนแปลงจากอดีตอย่างไร เช่น `daily_return` และ `momentum_20`

- เหมาะเป็น ranking factor เพื่อหา relative strength
- เหมาะเป็น time-series filter เมื่อกำหนดว่า momentum ต้องเป็นบวก
- อาจใช้เป็น risk context ได้ แต่ไม่ใช่ risk control โดยตรง

### Trend

วัดทิศทางและโครงสร้างของราคา เช่น `sma_20`, `sma_50` และ `trend_20_50`

- เหมาะเป็น filter ว่าราคาต้องอยู่เหนือ moving average
- ใช้เป็น ranking factor ได้ เช่นจัดอันดับค่า `trend_20_50`
- ใช้ลดความเสี่ยงเชิง regime ได้ เช่นไม่เปิด position เมื่อ trend ติดลบ

### Volatility / risk

`volatility_20` วัดความผันผวนย้อนหลังของ daily return

- ใช้เป็น risk control เช่นตัดหุ้นที่ volatility สูงเกินเพดาน
- ใช้ปรับขนาด position ใน Backtest ภายหลังได้
- ใช้เป็น ranking factor ได้ แต่ต้องตัดสินใจก่อนว่าจะชอบ volatility ต่ำหรือสูง

### Volume / liquidity

`volume_sma_20` และ `volume_ratio_20` ใช้เปรียบเทียบ volume ปัจจุบันกับค่าเฉลี่ยของตัวเอง

- ใช้เป็น filter เพื่อหลีกเลี่ยงวันที่ liquidity ต่ำ
- ใช้เป็น confirmation ของ momentum ได้
- ใช้เป็น risk/execution control ได้เมื่อมีเกณฑ์ turnover และความสามารถในการส่ง order ที่ชัดเจน

## 5. แยกหน้าที่ของ features

| หน้าที่ | ตัวอย่าง feature | คำถามที่ตอบ |
|---|---|---|
| Filter | `trend_20_50 > 0`, `momentum_20 > 0` | หุ้นมีสัญญาณที่ยอมรับได้หรือไม่ |
| Ranking factor | `momentum_20`, `trend_20_50`, หรือ score รวม | หุ้นใดแข็งแกร่งกว่า peers วันนี้ |
| Risk control | `volatility_20`, volume/liquidity และ data availability | หุ้นใดเสี่ยงหรือซื้อขายได้ยากเกินไป |

ควรแยก filter, ranking และ risk control ใน code และรายงาน เพื่อให้ทราบว่าเหตุใดหุ้นจึงถูกตัดออก ไม่ควรซ่อน risk rule ไว้ใน ranking score โดยไม่มีคำอธิบาย

## 6. Candidate research designs

ยังไม่มี design ใดได้รับการอนุมัติให้ implement

### Design A: Time-series baseline ต่อไป

- Universe: eligible historical SET50 ณ วันนั้น
- Filter: `momentum_20 > 0` และ `Close > sma_20`
- Selection: ถือทุกหุ้นที่ผ่าน filter หรือใช้จำนวนสูงสุดที่กำหนดภายหลัง
- Risk: ยังต้องออกแบบ position sizing และ volatility limit ใน Backtest
- เหมาะสำหรับ: ตรวจสอบ pipeline และสร้าง benchmark ที่เรียบง่าย

ข้อจำกัดคืออาจได้จำนวนหุ้นไม่คงที่และไม่ตอบคำถามว่า “ตัวไหนดีที่สุดเมื่อเทียบกัน”

### Design B: Pure cross-sectional momentum

- Universe: eligible historical SET50 ณ วันนั้น
- Filter ขั้นต้น: feature พร้อมใช้งานและไม่มี validation exclusion
- Ranking: จัดอันดับ `momentum_20` จากมากไปน้อย
- Selection: เลือก top `N` หรือ top percentile ตามค่าที่ human อนุมัติ
- Risk: ใช้ `volatility_20`/liquidity เป็น exclusion หรือ sizing input

ข้อจำกัดคือต้องระวังอันดับที่เปลี่ยนเร็ว, turnover และการเลือก `N` ที่อาจกลายเป็น optimization

### Design C: Hybrid trend filter + cross-sectional ranking

- Universe: eligible historical SET50 ณ วันนั้น
- Time-series filter: `Close > sma_20`, `trend_20_50 > 0` และอาจกำหนด `momentum_20 > 0`
- Ranking: จัดอันดับหุ้นที่ผ่าน filter ด้วย `momentum_20` หรือ score ที่ระบุสูตรตายตัว
- Selection: เลือก top `N` ที่ผ่าน filter
- Risk: ตัดหรือจำกัดน้ำหนักหุ้นที่ `volatility_20` สูงเกินเกณฑ์ และตรวจ volume/liquidity
- Timing: signal ที่ `t` ใช้ข้อมูลถึง `t` เท่านั้น และ order เร็วที่สุดใน trading row ถัดไป

ข้อดีคือ filter ป้องกันการเลือกหุ้นที่ trend เสีย ขณะที่ ranking ช่วยเลือกตัวที่แข็งแกร่งที่สุด ข้อเสียคือมีชั้นกฎมากขึ้นและมีโอกาส overfit หากเพิ่มเงื่อนไขหรือ weight มากเกินไป

## 7. ความเสี่ยงที่ต้องจัดการ

### Lookahead bias

Feature ณ `t` ห้ามใช้ข้อมูลหลัง `t` และ signal จากราคาปิดของ `t` ห้ามถูก execute ก่อนเวลาที่ราคานั้นทราบจริง ต้องกำหนด signal timestamp และ execution timestamp แยกกัน

### Survivorship bias

Universe ต้องใช้ historical SET50 membership และ effective dates ของวันนั้น ไม่ใช่ใช้ constituents ปัจจุบันย้อนหลัง และต้องไม่ทำให้ GULF แทนที่ INTUCH ก่อน merger

### Overfitting

การเพิ่ม window, threshold, factor weight หรือ top `N` หลายครั้งจนผลย้อนหลังดีขึ้น คือความเสี่ยงสูง ต้องบันทึกเหตุผลล่วงหน้าและแยก research decision จากผล Backtest

### Turnover

Ranking อาจทำให้หุ้นเข้า/ออกบ่อย ต้องกำหนด rebalance frequency, holding rule และ turnover measurement ก่อนประเมินผล

### Transaction costs

Competition มี commission 0.157% และ VAT 7% ของ commission พร้อม slippage หนึ่ง tick ตาม `AGENTS.md` ต้นทุนต้องอยู่ใน Backtest execution ไม่ใช่ถูกละเลยตอนเลือก design

### Small historical sample

Approved dataset มีช่วงเวลาและจำนวน symbols ที่จำกัด รวมถึง known gaps และ `NEEDS_REVIEW` records การสรุปว่า strategy ดีจาก sample เดียวจะไม่น่าเชื่อถือ

## Recommendations (ยังไม่ใช่ final decision)

คำแนะนำเชิงกระบวนการคือเริ่ม research ด้วย Design A เป็น benchmark ที่ไม่ซับซ้อน แล้วเปรียบเทียบกับ Design C โดยกำหนดกฎ, universe, timing และต้นทุนไว้ก่อนรัน Backtest การเปรียบเทียบควรตรวจจำนวน eligible symbols, turnover และ data exclusions ควบคู่กับผลตอบแทน

นี่เป็นคำแนะนำให้จัดลำดับการวิจัย ไม่ใช่การอนุมัติ Design A หรือ C และยังไม่ควร implement จนกว่า human researcher จะเลือก design และค่าคงที่ที่จำเป็น

## Decisions requiring human approval

ก่อนเริ่ม implementation ขั้นถัดไป human researcher ต้องตัดสินใจอย่างชัดเจนว่า:

1. จะวิจัย Design A, B หรือ C เป็นลำดับแรก
2. หากเลือก cross-sectional จะใช้ ranking factor เดียวหรือ composite score ใด และสูตรคืออะไร
3. จะใช้ time-series features ใดเป็น mandatory filters
4. จะใช้ `volatility_20` และ volume/liquidity เป็น filter, ranking factor, position-sizing input หรือไม่ใช้
5. จะเลือก top `N` หรือ percentile เท่าใด และเหตุผลที่ไม่ใช่ parameter optimization คืออะไร
6. จะ rebalance บ่อยเพียงใด และมี holding/minimum-trade rule หรือไม่
7. signal ที่คำนวณจากวัน `t` จะ execute ในวันถัดไปแบบใดภายใต้ allowed order types
8. จะกำหนดวิธีจัดการหุ้นที่ eligible universe เปลี่ยน, feature warm-up ไม่ครบ หรือมี known gap อย่างไร
9. จะวัด turnover, fees, VAT, slippage และ minimum 5 unique symbols อย่างไรใน Backtest
10. จะกำหนด research period และเกณฑ์ผ่าน/ไม่ผ่านก่อนดูผล Backtestอย่างไร

จนกว่าจะมีคำตอบเหล่านี้ repository ควรคง implementation ปัจจุบันไว้และยังไม่สร้าง hybrid strategy หรือเริ่ม optimization
