# Backtest Report กูเขียนเองแต่ AI เรียบเรียงย้ำๆๆ

## Backtest คืออะไร?

Backtest คือการทดสอบ Strategy ในข้อมูลประวัติศาสตร์ย้อนหลัง เพื่อดูว่า Strategy นี้จะทำงานได้ดีแค่ไหนถ้าเราใช้ข้อมูลเก่าและกฎเดียวกับการแข่งขัน

ในบริบทของโปรเจกต์นี้ Backtest ช่วยให้เราเห็นว่า:

- Strategy ควรซื้อหรือขายอะไร
- Portfolio ควรถือกี่หุ้นและมากน้อยแค่ไหน
- Fees, Commission, VAT, Slippage มีผลต่อผลลัพธ์อย่างไร
- ความเสี่ยงจะมีระดับเท่าไร
- Strategy มีปัญหาเรื่อง Lookahead Bias หรือ Data Leakage หรือไม่

---

## Architecture

Pipeline ของ Backtest ควรเป็นลำดับดังนี้:

Data
→ Features
→ Signals
→ Portfolio
→ Risk
→ Execution Simulation
→ Transaction Costs
→ Equity

แต่ละขั้นตอนมีความหมายดังนี้:

- Data: ข้อมูลที่ใช้สำหรับ Backtest
- Features: Feature ที่สร้างจากข้อมูล
- Signals: สัญญาณ Buy / Sell / Hold
- Portfolio: การจัดสรรเงินและการถือหุ้น
- Risk: การจำกัดความเสี่ยง เช่น Position Limit, Exposure Limit, Drawdown
- Execution Simulation: จำลองการซื้อขายตามกฎของ competition
- Transaction Costs: Commission, VAT, Slippage
- Equity: มูลค่าของพอร์ตการลงทุนในแต่ละจุดเวลา

---

## Portfolio Accounting

Portfolio Accounting ควรมีการบันทึกหลักดังนี้:

- Cash
- Holdings
- Market Value
- Realized P&L
- Unrealized P&L
- Fees
- Equity

สิ่งเหล่านี้สำคัญ เพราะต้องสามารถตอบคำถามได้ว่า:

- เรามีเงินสดเท่าไร
- เราถือหุ้นอะไรบ้าง
- มูลค่าหุ้นเท่าไร
- กำไรที่ขายไปแล้วเท่าไร
- กำไรที่ยังไม่ขายเท่าไร
- ค่าธรรมเนียมรวมเท่าไร
- มูลค่ารวมของพอร์ตคือเท่าไร

---

## Transaction Costs

ตาม AGENTS.md ของโปรเจกต์ ความคิดเรื่อง Transaction Costs คือ:

- Commission = 0.157% ของมูลค่า Order
- VAT = 7% ของ Commission
- Slippage = 1 Tick Size

ค่านี้มีผลต่อทั้ง Buy และ Sell จริง ดังนั้น Backtest ต้องคำนวณค่าใช้จ่ายจริง และแยก Commission กับ VAT ให้เห็นชัด เพื่ออธิบายได้ว่า Net P&L ถูกลดจากอะไร

สิ่งสำคัญคือ:

- ไม่สามารถซ่อนค่า Fees หรือคิดซ้ำได้
- ไม่ควรใช้ Fixed Percentage แบบสุ่มแทน Slippage
- ต้องคำนึงถึงทั้ง Price, Quantity, และ Order Type

---

## Performance Metrics

Metric ที่ระบบควรรองรับมีดังนี้:

- Return
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Win Rate
- Profit Factor
- Turnover
- Number of Trades
- Fees
- Net P&L

แต่ในปัจจุบันยังไม่มีผล Backtest จริงที่สามารถรายงานได้

---

## Validation

Validation เป็นส่วนสำคัญเพื่อให้ Strategy ไม่เป็นแค่การ fit กับข้อมูลแบบเกินจริง

ประเภทที่ควรมีคือ:

- Train/Test Split
- Out-of-Sample
- Walk-forward Validation

ทำไมต้องมี Validation:

เพราะ Strategy ที่ดูดีในข้อมูลที่เคยเห็นอาจทำงานแย่ในข้อมูลที่ยังไม่เคยเห็น โดยเฉพาะกับข้อมูลเวลา Series ที่มีความสัมพันธ์กันสูง

---

## Bias Control

ทีมต้องระวัง Bias ต่อไปนี้:

- Lookahead Bias: ใช้ข้อมูลที่ไม่ควรรู้ตอนตัดสินใจ
- Survivorship Bias: ใช้ universe ที่ผิดเพราะเลือกหุ้นที่ยังอยู่ใน SET50 ทุกช่วงเวลา
- Data Leakage: ใช้ข้อมูลจากอนาคตในกระบวนการสร้าง Feature หรือ Train Model
- Overfitting: ปรับ Strategy ให้พอดีกับ historical dataset มากเกินไป

การควบคุม Bias เป็นเรื่องสำคัญมาก เพราะ Backtest ที่ดูดีแต่มี Bias จะทำให้สรุปผิดได้ง่าย

---

## Backtest Limitations

Backtest ในปัจจุบันยังไม่ทำงานในระดับ full strategy เพราะ:

- Historical SET50 universe ยังต้องมี data จริงเพิ่มเติม
- Strategy ยังไม่ได้เริ่มทดสอบ
- Data source ยังเป็น research version
- ผลลัพธ์ทางการเงินยังไม่มีข้อมูลจริง

ดังนั้นผลลัพธ์วันนี้ยังไม่สามารถใช้ประกอบการตัดสินใจทางการเงินได้

---

## Current Status

Backtest framework เป็นส่วนที่อยู่ในแผนงานต่อไป และยังไม่ได้เริ่มทำการทดลองจริงในระดับ Strategy

เรายังคงอยู่ในช่วงการสร้าง foundation ของ Data Pipeline ก่อนที่จะเริ่ม Backtest อย่างมีคุณภาพ
