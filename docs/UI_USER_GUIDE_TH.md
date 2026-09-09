# คู่มือทดสอบ UI แบบ Manual สำหรับ SET50 Research Desk

เอกสารนี้ใช้สำหรับตรวจสอบ Streamlit UI ใน repository ปัจจุบันแบบ manual โดย UI เป็นแบบ read-only: อ่านข้อมูลจาก CSV/JSON และ raw OHLCV เท่านั้น และไม่แก้ไข เติม หรือซ่อมข้อมูลต้นฉบับ

คำสั่งและ technical terms เช่น `Streamlit`, `OHLCV`, `CSV`, `manifest` และ `eligibility gate` คงไว้เป็น English เพื่อให้ตรงกับ repository

## 1. การเริ่ม Streamlit app

เปิด PowerShell ที่ repository root:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run ui/app.py
```

จากนั้นเปิด URL:

```text
http://localhost:8501
```

`8501` คือ default Streamlit port หาก port นี้ถูกใช้งานอยู่ ให้รัน:

```powershell
python -m streamlit run ui/app.py --server.port 8502
```

แล้วเปิด `http://localhost:8502`

หากไม่ต้องการ activate environment สามารถใช้ `\.venv\Scripts\python.exe -m streamlit run ui/app.py` ได้โดยตรง

## 2. แหล่งข้อมูลที่ UI อ่าน

UI ควรอ่านข้อมูลจากแหล่งต่อไปนี้โดยไม่เขียนทับ:

- `data/processed/constituents/historical_set50.csv` — historical SET50 membership
- `reports/yahoo_ticker_audit.csv` — Yahoo ticker mapping/audit
- `reports/market_data_acquisition.csv` — acquisition status
- `reports/data_acquisition_metadata.json` — acquisition metadata
- `data/raw/market_data/` — raw OHLCV CSV files

สำหรับการตรวจว่า data ผ่าน research approval แล้วหรือไม่ ให้ตรวจเพิ่มจาก:

- `data/processed/approved_market_data_manifest.csv` — machine-readable approved date ranges
- `reports/research_data_readiness.csv` หรือ `.md` — decision ของทุก SET symbol
- `src/data/eligibility.py` — reusable `eligibility gate` สำหรับ downstream code

UI ปัจจุบันยังไม่มีหน้าแสดง approved manifest โดยตรง ดังนั้นผล approved/excluded ที่เป็นทางการต้องยืนยันจาก manifest และ readiness report ไม่ใช่ดูจากการมี raw file เพียงอย่างเดียว

## 3. หน้าหลักและสิ่งที่ควรเห็น

### Dashboard

ใช้ดูภาพรวมของ dataset:

- จำนวน historical SET50 periods และ symbols
- จำนวน raw series ที่ดาวน์โหลดได้
- ช่วงวันที่ที่พบใน raw data
- จำนวน missing/failed acquisition
- สรุป `Yahoo audit` status และ acquisition status
- ตำแหน่ง raw-data directory ที่ค้นพบ

ใน snapshot ปัจจุบันควรเห็นประมาณ 63 historical symbols, raw files สำหรับ symbols ส่วนใหญ่, acquisition ที่มีทั้ง `SUCCESS`, `PARTIAL`, `PARTIAL_KNOWN_GAP` และ `NO_DATA` และมี missing series ของ `INTUCH` หนึ่งรายการ การนับที่เปลี่ยนตามข้อมูลล่าสุดไม่ถือเป็นความผิดพลาด ให้ยึด reports เป็น source of truth

### Historical SET50 Universe

ใช้ตรวจ historical constituents ตาม `period`:

- เลือก `Effective period`
- ตรวจ `symbol`, `company_name`, `effective_from`, `effective_to`
- ตรวจ `Yahoo Ticker` และ mapping `Status`
- ตรวจ `source_url`/provenance เมื่อมี

ยืนยันว่า official SET symbol แยกจาก Yahoo mapping และ membership มีขอบเขตวันที่ ไม่ควรใช้รายชื่อ SET50 ปัจจุบันแทน historical universe

### Market Data Explorer

ใช้ตรวจ raw data ของ symbol รายตัว:

- เลือก symbol
- เลือก date range
- ตรวจตาราง OHLCV และกราฟ Candlestick/Volume
- ดู `Rows`, `Missing values`, `Duplicate dates` และ `OHLC warnings`
- เปิด `Data quality details` เพื่อดูรายละเอียด diagnostics

วันที่ที่แสดงคือวันที่มีอยู่จริงใน raw file เท่านั้น UI จะไม่ forward-fill, interpolate หรือ fabricate OHLCV และถ้าไม่มีไฟล์จะแสดง warning แทนการสร้างข้อมูล

### Data Quality

ใช้ดูตารางรวมของ:

- acquisition status
- Yahoo ticker audit
- raw-file validation diagnostics

ให้ตรวจ `PARTIAL`, `NO_DATA`, missing values, duplicate dates, invalid OHLC relationship และ calendar gaps แล้วเทียบกับ remediation/adjudication reports อย่าถือว่า `PARTIAL` คือ approved โดยอัตโนมัติ

### Research Results

ส่วนนี้เป็น placeholder ปัจจุบัน โดย Strategy Research, Backtest, Out-of-Sample, Optimization, Robustness และ Paper Trading ควรแสดง `Not implemented` การแสดงเช่นนี้เป็นพฤติกรรมที่ถูกต้องใน milestone นี้

## 4. ขั้นตอนทดสอบ Universe/constituent

1. เปิด `Historical SET50 Universe`
2. เลือก period ที่มีใน dropdown เช่น period ของปี 2023–2026
3. ตรวจว่า symbol และ effective dates ตรงกับ `historical_set50.csv`
4. เปลี่ยน period แล้วตรวจว่าสมาชิกเปลี่ยนตามช่วงเวลา ไม่ใช่คงเป็น current universe
5. ตรวจว่า `Yahoo Ticker` แสดงเป็น mapping ที่มี audit เท่านั้น ไม่เกิดการเดา ticker หรือเติม `.BK` อัตโนมัติ

หากต้องการยืนยันเชิงไฟล์ ให้เปิด CSV ด้วย read-only viewer แล้วเทียบแถวที่มี `SET Symbol`, `effective_from` และ `effective_to`

## 5. ขั้นตอนทดสอบ market data และ data-quality status

1. เปิด `Market Data Explorer` แล้วเลือก symbol ที่มี raw file เช่น `ADVANC`
2. เลือก date range ครอบคลุมข้อมูล
3. ตรวจว่า Date เรียงลำดับ, OHLCV แสดงตาม raw CSV และกราฟไม่สร้างวันที่ใหม่
4. ตรวจ metrics `Rows`, `Missing values`, `Duplicate dates` และ `OHLC warnings`
5. เปิด `Data Quality` แล้วเทียบ status ของ symbol เดิมกับ `reports/market_data_acquisition.csv`
6. สำหรับ warning ให้เปิด `reports/market_data_remediation.csv` และ `reports/ohlc_anomaly_adjudication.csv` เพื่ออ่านเหตุผล ไม่แก้ raw file

## 6. การตรวจ approved และ excluded symbols

การมี raw file หรือ `Yahoo audit = VERIFIED` เพียงอย่างเดียวไม่เพียงพอ ต้องตรวจ `approval_status` ใน `data/processed/approved_market_data_manifest.csv` และ readiness report:

- `APPROVED` — ใช้ได้เฉพาะช่วง `approved_from` ถึง `approved_to`
- `APPROVED_WITH_KNOWN_GAP` — ใช้ได้เฉพาะช่วงที่ระบุ และต้องรักษา known gap
- `NEEDS_REVIEW` — ห้าม downstream research ใช้จนกว่าจะมี approval ที่ชัดเจน
- `REJECTED` — ห้ามใช้

ตัวอย่าง snapshot ปัจจุบันมี 18 `APPROVED`, 2 `APPROVED_WITH_KNOWN_GAP`, 42 `NEEDS_REVIEW` และ 1 `REJECTED` ทั้งนี้ให้ยึดค่าจาก manifest ที่เปิดอยู่เป็นหลักหากมีการสร้าง report ใหม่

## 7. กรณีพิเศษที่ต้องตรวจ

### BANPU

- ควรมี raw file และแสดง raw OHLCV ตามที่มีจริง
- `Data Quality` ควรแสดง `PARTIAL` และ warning/gap ที่เกี่ยวข้อง
- ช่วง suspension ที่ทราบแล้วต้องคงเป็น missing/known gap ไม่ใช่ error ที่ต้องเติมราคา
- ปัจจุบันควรเป็น `NEEDS_REVIEW` และไม่อยู่ใน approved manifest

### GULF

- raw data ควรเริ่มหลัง merger ประมาณ `2025-04-03` ตามวันที่ที่มีจริง
- ห้ามทำให้ GULF ก่อน `2025-04-01` มีสิทธิ์เพียงเพราะมี historical continuity
- manifest อนุมัติ GULF เฉพาะช่วงหลัง merger ที่ระบุไว้ (ปัจจุบันประมาณ `2025-04-03` ถึง `2026-09-04`)
- UI จะไม่สร้าง pre-merger rows; ยืนยัน approval boundary จาก manifest

### TIDLOR

- ควรเห็น raw data เริ่มประมาณ `2025-05-16`
- ช่วงก่อนหน้านั้นเป็น corporate-action/coverage gap ที่ต้องแสดง ไม่ใช่เติมราคา
- ปัจจุบันควรเป็น `APPROVED_WITH_KNOWN_GAP` เฉพาะช่วงที่ manifest ระบุ (ประมาณ `2025-05-16` ถึง `2026-09-04`)

### INTUCH

- ไม่ควรมี raw file ที่ใช้ได้; `Market Data Explorer` ควรแสดง warning ว่าไม่มี downloaded raw file
- audit/acquisition ควรแสดง `NOT_FOUND`/`NO_DATA`
- ควรเป็น `REJECTED` และไม่อยู่ใน approved manifest
- ห้าม rewrite historical INTUCH membership เป็น GULF

## 8. พฤติกรรมเมื่อข้อมูลหายหรือไม่ถูกต้อง

- ไม่มี raw file: แสดง warning และไม่สร้าง series ใหม่
- missing OHLCV: แสดงใน quality diagnostics และคง missing ไว้
- invalid OHLC relationship: แสดง `OHLC warnings`; ไม่แก้ค่าใน UI
- duplicate dates: แสดงจำนวนใน diagnostics; ไม่ deduplicate แบบเงียบ ๆ
- calendar gap: แสดงเป็น gap/known condition ตาม report; ไม่ forward-fill
- ticker mapping หาย: ไม่เดา ticker และไม่เติม `.BK`
- `PARTIAL` acquisition: ยังไม่ใช่ approval จนกว่าจะมี explicit decision ใน manifest

## 9. Checklist ทดสอบอย่างย่อ

- [ ] สร้าง/activate `.venv` และติดตั้ง `requirements.txt` สำเร็จ
- [ ] เปิด `http://localhost:8501` หรือ port ที่กำหนดเองได้
- [ ] Dashboard แสดง summary และไม่เกิด traceback
- [ ] Historical SET50 Universe เปลี่ยนตาม `Effective period`
- [ ] Yahoo mapping แยกจาก official SET symbol และไม่มี automatic guessing
- [ ] Market Data Explorer แสดง raw OHLCV, Candlestick และ quality metrics
- [ ] Data Quality แสดง acquisition/audit/validation status
- [ ] `APPROVED` และ `APPROVED_WITH_KNOWN_GAP` ถูกยืนยันจาก manifest
- [ ] `NEEDS_REVIEW` และ `REJECTED` ไม่ถูกนับเป็น research-ready
- [ ] ตรวจ BANPU, GULF, TIDLOR และ INTUCH ตามกรณีพิเศษด้านบน
- [ ] เมื่อมี missing/invalid data UI แสดง warning/diagnostic และไม่เติมข้อมูล
- [ ] Research Results ยังคงแสดง `Not implemented`

## 10. ปัญหาที่พบบ่อยและการแก้ไข

### `streamlit` ไม่ใช่ command ที่รู้จัก

ตรวจว่า activate `.venv` แล้ว หรือใช้:

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui/app.py
```

### ขาด package เช่น `pandas`, `plotly` หรือ `streamlit`

รันจาก repository root:

```powershell
python -m pip install -r requirements.txt
```

### Port 8501 ถูกใช้งาน

ใช้ port อื่น:

```powershell
python -m streamlit run ui/app.py --server.port 8502
```

แล้วเปิด `http://localhost:8502`

### Browser ไม่เปิดเอง

เปิด URL ด้วยตนเอง และตรวจ terminal ว่า Streamlit process ยังทำงานอยู่

### หน้าแสดงข้อมูลว่างหรือหาไฟล์ไม่พบ

ตรวจว่า command รันจาก repository root, โครงสร้าง `data/` และ `reports/` ยังอยู่ครบ และ metadata ชี้ไปที่ `data/raw/market_data` อย่าย้ายหรือแก้ raw files เพื่อแก้ปัญหาหน้าจอ

### มี OHLC warning หรือข้อมูลไม่ครบ

นี่อาจเป็น validation finding ที่ตั้งใจให้เห็น โดยเฉพาะ symbol ที่ `NEEDS_REVIEW` ให้ตรวจ remediation/adjudication report และคงข้อมูลเดิมไว้ ไม่เติมหรือแก้ราคา

หาก Streamlit file watcher มีปัญหา สามารถลอง:

```powershell
python -m streamlit run ui/app.py --server.fileWatcherType poll
```

เมื่อทดสอบเสร็จ ให้หยุด app ด้วย `Ctrl+C` ใน terminal
