# SET50 Constituent Data Policy

## ขอบเขต

Policy นี้ใช้สำหรับสร้าง Historical SET50 Universe จาก Official SET PDFs ในช่วง 2023 H1 ถึง 2026 H2

Policy นี้ไม่ทำสิ่งต่อไปนี้:

- ไม่ดาวน์โหลด Yahoo Finance
- ไม่ map Yahoo Ticker
- ไม่ทำ Backtest
- ไม่สร้าง Strategy
- ไม่แก้ symbol ใน Official SET PDF โดยไม่มี source รองรับ

## 1. TRUEE และ BANPUU

### Event-time symbol

`TRUEE` และ `BANPUU` จะถูกเก็บเป็น `event-time symbol` แยกจาก `canonical symbol`

กฎ:

- ถ้า symbol ปรากฏใน change-related text หรือ Corporate Action record ให้เก็บ symbol เดิมตาม source
- ไม่เพิ่ม `TRUEE` หรือ `BANPUU` เข้า full SET50 Snapshot ถ้าไม่อยู่ใน SET50 rows 1-50
- ไม่ทำ `TRUEE -> TRUE` หรือ `BANPUU -> BANPU` ใน constituent CSV โดยอัตโนมัติ
- `canonical_symbol` จะเป็นค่าว่างจนกว่าจะมี policy และหลักฐานที่อนุมัติการรวม identity
- เก็บ `event_time_symbol`, `canonical_symbol`, `mapping_status` และ `mapping_source` แยกกันเมื่อมี event record

ผลต่อ CSV:

- CSV ของ full SET50 membership จะใช้เฉพาะ symbol ที่อยู่ใน SET50 rows 1-50
- `TRUEE` และ `BANPUU` จะไม่ถูกเพิ่มเป็นสมาชิกจากข้อความ Inclusion/Exclusion เพียงอย่างเดียว

## 2. TIDLOR

เก็บ symbol เดิมคือ `TIDLOR` ตลอดทุก period ที่ PDF ระบุ symbol นี้

กฎ:

- ห้ามเปลี่ยน symbol ตาม company name
- เก็บ `company_name` ตามชื่อที่ปรากฏใน PDF ของแต่ละ period
- ชื่อบริษัทที่เปลี่ยน เช่น Ngern Tid Lor และ TIDLOR Holdings ถือเป็น period-specific metadata
- การเปลี่ยน company name ไม่ถือเป็น ticker change โดยอัตโนมัติ

## 3. 2026 H2 Revised PDF

ใช้ revised PDF เป็น `primary source`:

- Revised: https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf
- Original provenance: https://media.set.or.th/set/Documents/2026/Jun/SET50-SET100-H2-2026.pdf

กฎ:

- ใช้รายชื่อ SET50 rows 1-50 จาก revised PDF
- เก็บ `revision_status=REVISED_PRIMARY`
- เก็บ original URL ใน `provenance_source_url`
- ผล audit พบว่า original และ revised มี SET50 rows เหมือนกัน 50 symbols
- ความแตกต่างของ Reserve List และ change-related sections ไม่เปลี่ยน full SET50 membership

## 4. 2024-01-01 Calendar Boundary

วันที่ 2024-01-01 ถือเป็น `non-trading calendar boundary`

กฎ:

- ไม่เติม membership ในวันที่ 2024-01-01
- ใช้ Effective Date ตาม Official SET PDF คือ 2024-01-02
- ไม่เลื่อน Effective Date เอง
- CSV จะบันทึก period ตาม source และไม่สร้างแถวพิเศษสำหรับวันที่ 2024-01-01

## 5. Yahoo Ticker

ขั้นนี้ไม่ทำ Yahoo Ticker mapping

กฎ:

- constituent CSV ใช้ SET symbol จาก Official SET PDF
- ไม่เติม `.BK` หรือ mapping อื่น
- Yahoo Ticker audit เป็นงานแยกภายหลัง
- ราคาหุ้นและ identity mapping ต้องผ่าน price-source audit ก่อนใช้ร่วมกับ universe

## 6. CSV Schema Policy

Historical constituent CSV ให้เก็บอย่างน้อย:

- `period`
- `effective_from`
- `effective_to`
- `symbol`
- `company_name`
- `source_url`
- `provenance_source_url`
- `revision_status`
- `mapping_status`

กฎการสร้าง row:

- หนึ่ง row ต่อ symbol ต่อ Official SET period
- อ่าน symbol จาก SET50 rows 1-50 เท่านั้น
- ไม่รวม Reserve List
- ไม่รวม SET100
- ไม่รวม symbols ที่ปรากฏเฉพาะ change-related text
- ไม่ deduplicate ข้าม period เพราะการปรากฏในแต่ละ period เป็นข้อมูล historical membership

## 7. Readiness Decision

Policy นี้เพียงพอสำหรับสร้าง `data/processed/constituents/historical_set50.csv` ในขอบเขต 2023 H1 ถึง 2026 H2 เพราะ:

- ทุก period มี full SET50 Snapshot ครบ 50 symbols
- ไม่มี duplicate ใน Snapshot
- ไม่มี membership gap ระหว่าง SET review periods
- disputed symbols ไม่อยู่ใน full rows หรือมีการเก็บตาม source โดยไม่เดา mapping
- TIDLOR รองรับ company_name แบบ period-specific
- 2026 H2 มี revised primary source และ original provenance
- 2024-01-01 ไม่ถูกเติม membership
- Yahoo Ticker ไม่จำเป็นสำหรับ constituent universe CSV

สถานะ: `READY_FOR_CONSTITUENT_CSV`

ข้อจำกัด:

- CSV นี้ครอบคลุมตั้งแต่ 2023 H1 ไม่ใช่ตั้งแต่ 2016
- CSV นี้ยังไม่ใช่ price-ready dataset
- ต้องทำ Yahoo Ticker และ Corporate Action audit แยกก่อนเชื่อมกับราคา
