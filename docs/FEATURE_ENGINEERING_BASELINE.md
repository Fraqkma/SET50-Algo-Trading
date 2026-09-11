# Feature Engineering และ Baseline Strategy

เอกสารนี้อธิบาย foundation สำหรับ research dataset ที่ผ่าน approval แล้ว โดยยังไม่มี optimization, OOS testing, robustness testing, paper trading หรือ Backtest execution

## Data boundary

ให้โหลดข้อมูลผ่าน `src.data.research.load_approved_market_data` เท่านั้นใน production research code:

```python
from src.data.research import load_approved_market_data

prices = load_approved_market_data("BDMS", start="2024-01-01", end="2025-01-01")
```

loader ใช้ approved manifest เพื่อระบุ raw file แล้วเรียก `MarketDataEligibilityGate` กับทุกวันที่จะคืนให้ผู้เรียก จึงเคารพ historical SET50 membership, approved date range, acquisition/validation approval, INTUCH/GULF continuity, BANPU suspension และ known gaps ข้อมูลที่ไม่ผ่าน gate จะถูกตัดออก ไม่ได้เติมหรือซ่อม

raw CSV ยังคง immutable และ feature calculation ทำงานบนสำเนาใน memory เท่านั้น

## Features

`src.data.features.build_features` รับข้อมูลของ symbol เดียวที่มี date-like index และ `Close`/`Volume` แล้วคืน feature frame เดิมพร้อมคอลัมน์ต่อไปนี้:

- `daily_return`: `Close[t] / Close[t-1] - 1`
- `momentum_20`: `Close[t] / Close[t-20] - 1`
- `sma_20`: ค่าเฉลี่ย `Close` ย้อนหลัง 20 observations รวมวันที่ `t`
- `sma_50`: ค่าเฉลี่ย `Close` ย้อนหลัง 50 observations รวมวันที่ `t`
- `trend_20_50`: `sma_20 / sma_50 - 1`
- `volatility_20`: population standard deviation (`ddof=0`) ของ `daily_return` ย้อนหลัง 20 observations
- `volume_sma_20`: ค่าเฉลี่ย `Volume` ย้อนหลัง 20 observations เมื่อมี `Volume`
- `volume_ratio_20`: `Volume / volume_sma_20` เมื่อมี `Volume`

ค่าช่วง warm-up ที่ยังมี observations ไม่ครบจะเป็น `NaN` ตามธรรมชาติ ไม่ถูก forward-fill, interpolate หรือ fabricate และ missing/duplicate input จะทำให้ฟังก์ชันหยุดด้วย error แทนการซ่อนปัญหา

## Timing และการป้องกัน lookahead

ทุก rolling window ใช้ข้อมูลตั้งแต่วันแรกของ window ถึงวันที่ปัจจุบันเท่านั้น ดังนั้น feature ที่ index `t` ไม่อ่านราคา/volume หลัง `t` การเปลี่ยนแปลงราคาวันอนาคตจะไม่เปลี่ยน feature ของวันก่อนหน้า

`BaselineStrategy` สร้าง signal ที่วัน `t` จาก feature ณ วัน `t` เท่านั้น ส่วนการ execute ต้องเป็นหน้าที่ของ Backtest milestone และต้อง execute ไม่เร็วกว่าวัน trading row ถัดไป ห้ามนำ closing price ของวัน `t` ไปสมมติว่า order เกิดก่อน close ของวันเดียวกัน

## Baseline Strategy rules

`src.strategies.baseline.BaselineStrategy` เป็น long-only signal generator และไม่จัดการ cash, position หรือ order:

- `BUY` เมื่อ `momentum_20 > 0` และ `Close > sma_20`
- `EXIT` เมื่อ feature พร้อมใช้ แต่เงื่อนไข `BUY` ไม่ครบ
- `HOLD` ระหว่าง warm-up ที่ feature สำคัญยังเป็น `NaN`

กฎนี้เป็น baseline ที่อ่านง่ายและใช้ค่าคงที่ที่กำหนดไว้ล่วงหน้า ไม่ใช่ผลจาก parameter optimization ไม่มี short signal และไม่มีการอ้างอิงราคาล่วงหน้า

## ขอบเขต milestone ถัดไป

Feature/strategy foundation นี้ยังไม่ให้ผลตอบแทนหรืออ้างว่า strategy ใช้งานได้จริง ขั้นถัดไปคือสร้าง Backtest execution ที่เคารพ signal timing, historical universe, fees, tick slippage, long-only และ eligibility gate ก่อนทำ OOS หรือ optimization
