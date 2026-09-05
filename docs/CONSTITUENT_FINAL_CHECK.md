# SET50 Constituent Final Check

## ขอบเขต

ตรวจสอบ Historical SET50 Universe จาก Official SET constituent PDFs ในช่วง:

`2023 H1` ถึง `2026 H2`

ตรวจสอบเฉพาะ:

- จำนวน symbols ต่อ period
- duplicate symbols
- period overlap และ gap
- Effective Date
- Revised PDF
- Symbol Mapping issue
- การใช้ consecutive Snapshot
- ความเสี่ยง Survivorship Bias

ยังไม่สร้าง final CSV, ไม่ดาวน์โหลด Yahoo Finance และไม่ทำ Backtest

## Summary

ผลการตรวจสอบเชิงโครงสร้าง:

- มี 8 periods ต่อเนื่องในช่วงที่ตรวจสอบ
- ทุก period มี 50 symbols
- ทุก period มี 50 unique symbols
- ไม่พบ duplicate ใน SET50 rows 1-50
- ไม่พบ period overlap
- ไม่พบ membership gap ระหว่าง period ที่ตรวจสอบ
- 2024 H1 เริ่มวันที่ 2024-01-02 ตาม Official SET PDF เนื่องจากเป็นวันเริ่ม period ที่ source ระบุ
- Revised 2026 H2 PDF ไม่เปลี่ยนรายชื่อ SET50 rows 1-50 เมื่อเทียบกับ original PDF
- ยังมี Symbol Mapping และ company-name issue ที่ต้องกำหนด policy ก่อนสร้าง final CSV

## Period Summary

| Period | Effective From | Effective To | Symbol Count | Duplicate | Revision | Symbol Issue | Status |
|---|---|---|---:|---|---|---|---|
| 2023 H1 | 2023-01-01 | 2023-06-30 | 50 | None | `_revise` file; full list verified | TRUEE อยู่ใน change-related text แต่ไม่อยู่ใน full rows | NEEDS_REVIEW |
| 2023 H2 | 2023-07-01 | 2023-12-31 | 50 | None | No revision marker | None in full rows | READY |
| 2024 H1 | 2024-01-02 | 2024-06-30 | 50 | None | No revision marker | TIDLOR company name continuity requires metadata policy | NEEDS_REVIEW |
| 2024 H2 | 2024-07-01 | 2024-12-31 | 50 | None | No revision marker | None in full rows | READY |
| 2025 H1 | 2025-01-01 | 2025-06-30 | 50 | None | No revision marker | None in full rows | READY |
| 2025 H2 | 2025-07-01 | 2025-12-31 | 50 | None | No revision marker | None in full rows | READY |
| 2026 H1 | 2026-01-01 | 2026-06-30 | 50 | None | No revision marker | None in full rows | READY |
| 2026 H2 | 2026-07-01 | 2026-12-31 | 50 | None | Revised source selected; full list unchanged | BANPUU change-related text, MRDIYT appears as new full symbol | NEEDS_REVIEW |

Source URLs are recorded in [docs/SYMBOL_AUDIT.md](SYMBOL_AUDIT.md) and the raw archive README.

## 1. Symbol Count and Duplicate Check

ตรวจสอบ SET50 rows 1-50 จาก PDF โดยตรง:

| Check | Result |
|---|---|
| Expected symbols per period | 50 |
| Periods checked | 8 |
| Periods with 50 symbols | 8/8 |
| Periods with 50 unique symbols | 8/8 |
| Duplicate symbols | 0 |
| Missing numbered rows | 0 |

สรุป: Snapshot ทุก period มีรูปแบบครบถ้วนในระดับจำนวนและความ unique ของ symbol

## 2. Period Overlap Check

ช่วงเวลาใน Official SET PDFs:

- 2023-01-01 ถึง 2023-06-30
- 2023-07-01 ถึง 2023-12-31
- 2024-01-02 ถึง 2024-06-30
- 2024-07-01 ถึง 2024-12-31
- 2025-01-01 ถึง 2025-06-30
- 2025-07-01 ถึง 2025-12-31
- 2026-01-01 ถึง 2026-06-30
- 2026-07-01 ถึง 2026-12-31

ผลตรวจ:

- ไม่พบช่วงที่ overlap กัน
- period หนึ่งสิ้นสุดก่อน period ถัดไปเริ่ม
- ไม่มีช่วงที่ขาดในมุมมองของ SET review periods

## 3. Gap Check

### Membership period gap

ไม่พบ membership gap ระหว่าง period ที่ตรวจสอบ เพราะช่วงต่าง ๆ ต่อกันตาม SET semi-annual review:

- 2023 H1 ต่อด้วย 2023 H2
- 2023 H2 ต่อด้วย 2024 H1
- 2024 H1 ต่อด้วย 2024 H2
- 2024 H2 ต่อด้วย 2025 H1
- 2025 H1 ต่อด้วย 2025 H2
- 2025 H2 ต่อด้วย 2026 H1
- 2026 H1 ต่อด้วย 2026 H2

### Calendar-date note

2023 H2 สิ้นสุดวันที่ 2023-12-31 และ 2024 H1 เริ่มวันที่ 2024-01-02 จึงมีวันที่ 2024-01-01 อยู่ระหว่างสองค่าถ้าใช้ calendar arithmetic แบบตรง ๆ

PDF ของ SET ระบุ 2024 H1 ว่าใช้คำนวณตั้งแต่ `January 2 - June 30, 2024` ดังนั้นวันที่ 2024-01-01 ควรบันทึกเป็น non-trading/calendar boundary ไม่ควรเติม membership เอง

สถานะของ gap นี้: `NEEDS_REVIEW` สำหรับ data model แต่ไม่ถือเป็น missing SET review period

## 4. Effective Date Check

Effective dates ถูกอ่านจาก period text ใน Official SET PDFs:

- 2023 H1: 2023-01-01 ถึง 2023-06-30
- 2023 H2: 2023-07-01 ถึง 2023-12-31
- 2024 H1: 2024-01-02 ถึง 2024-06-30
- 2024 H2: 2024-07-01 ถึง 2024-12-31
- 2025 H1: 2025-01-01 ถึง 2025-06-30
- 2025 H2: 2025-07-01 ถึง 2025-12-31
- 2026 H1: 2026-01-01 ถึง 2026-06-30
- 2026 H2: 2026-07-01 ถึง 2026-12-31

ผลตรวจ:

- Effective From และ Effective To สอดคล้องกับ period ที่ระบุใน PDF
- ไม่พบวันที่ขัดกันระหว่าง filename, period label และ Snapshot audit
- 2024-01-01 ต้องเก็บเป็น calendar boundary ไม่ใช่เติมวัน membership ที่ไม่มีใน source

## 5. Revised PDF Check

ตรวจสอบ 2026 H2 original และ revised Official SET PDFs:

- Original: https://media.set.or.th/set/Documents/2026/Jun/SET50-SET100-H2-2026.pdf
- Revised: https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf

ผลเปรียบเทียบ:

- Original มี 50 symbols และ 50 unique symbols
- Revised มี 50 symbols และ 50 unique symbols
- Added ระหว่าง original และ revised: ไม่มี
- Removed ระหว่าง original และ revised: ไม่มี
- รายชื่อ SET50 rows 1-50 เหมือนกัน
- Revised เปลี่ยน Update date จาก June 17, 2026 เป็น August 3, 2026
- Reserve List และ change-related sections เปลี่ยน

Decision:

- ใช้ revised PDF เป็น source หลักของ 2026 H2 เพราะ archive ระบุว่าเป็น update ระหว่าง periodic review
- revised PDF ไม่มีผลต่อ full SET50 membership list
- original URL ต้องเก็บเป็น audit trail
- revision provenance ยังต้องเก็บใน metadata

## 6. Symbol Mapping Issue Check

| Symbol / Issue | ผลตรวจ | ผลต่อ Historical Universe | Status |
|---|---|---|---|
| TRUEE | Official SET symbol change ที่ปรากฏใน change-related text; ไม่อยู่ใน full SET50 rows | ไม่เพิ่ม `TRUEE` เข้า full Snapshot และยังไม่ map เป็น `TRUE` อัตโนมัติ | NEEDS_REVIEW |
| SAWAD | เป็น valid SET symbol ใน full Snapshot บาง period และหายไปในบาง period | ถือเป็น membership change ตาม Snapshot; ไม่สรุปเป็น ticker change | READY |
| BANPUU | Temporary Corporate Action symbol ใน change-related text; full Snapshot ใช้ `BANPU` | ไม่เพิ่ม `BANPUU` เข้า full Snapshot และไม่แทน `BANPU` อัตโนมัติ | NEEDS_REVIEW |
| MRDIYT | Valid SET symbol ใน 2026 H2 rows 1-50 | เก็บ `MRDIYT` ตาม PDF เดิม | READY |
| TIDLOR | Symbol เดิมแต่ company name เปลี่ยนในบาง PDF | ต้องเก็บ company name แบบ period-specific | NEEDS_REVIEW |
| Yahoo Ticker | ยังไม่ได้ตรวจสอบตาม scope | ไม่ใช้ในการตัดสิน SET membership | UNVERIFIED |

## 7. Consecutive Snapshot Check

Consecutive Snapshot สามารถใช้สร้าง Historical SET50 Universe ได้ในช่วงที่มี full Snapshot:

```text
Universe(period) = SET50 rows 1-50 ของ Official SET PDF
Added = Current Snapshot - Previous Snapshot
Removed = Previous Snapshot - Current Snapshot
```

คู่ที่ตรวจสอบได้:

- 2023 H1 -> 2023 H2
- 2023 H2 -> 2024 H1
- 2024 H1 -> 2024 H2
- 2024 H2 -> 2025 H1
- 2025 H1 -> 2025 H2
- 2025 H2 -> 2026 H1
- 2026 H1 -> 2026 H2

ผลตรวจ:

- ใช้ set difference ได้ เพราะแต่ละ Snapshot มี 50 unique symbols
- ต้องไม่เอา `Inclusion` / `Exclusion` text มาปนกับ full Snapshot
- ต้องเก็บ source period และ revision status ต่อ row
- ต้องใช้ Effective Date จาก PDF ไม่ใช่ announcement date

สถานะ: `READY` สำหรับการสร้าง universe จาก Snapshot ในช่วงนี้ แต่ยังไม่ใช่การอนุมัติ final CSV

## 8. Survivorship Bias Check

ความเสี่ยงลดลงอย่างมากเมื่อใช้ period-specific SET50 Snapshot แทน current SET50 list เพราะ universe เปลี่ยนตามเวลา

สิ่งที่ทำถูกต้อง:

- ใช้ historical constituents ตามแต่ละ period
- ไม่ใช้ current SET50 list ย้อนกลับไปแทนอดีต
- ไม่เติม symbol ที่ไม่อยู่ใน full Snapshot
- ไม่ map symbol ที่ยังไม่มีหลักฐาน
- แยก change-related symbol ออกจาก membership rows

ข้อจำกัดที่ยังเหลือ:

- Coverage เริ่มที่ 2023 H1 ไม่ใช่ตั้งแต่ 2016
- ช่วงก่อน 2023 H1 ยังไม่สามารถใช้ Historical SET50 Universe นี้ได้
- Ticker identity และ company-name continuity ยังต้องเก็บเป็น metadata
- ถ้าใช้ price data โดยไม่จัดการ Corporate Action อาจเกิด lookahead หรือ symbol continuity issue

สถานะ: `NEEDS_REVIEW`

## 9. Final Recommendation

ข้อมูลพร้อมในระดับ Snapshot Audit สำหรับช่วง 2023 H1 ถึง 2026 H2 แต่ยังไม่พร้อมสร้าง final historical constituent CSV

เหตุผล:

1. `TRUEE` และ `BANPUU` ยังต้องกำหนด policy ว่าจะเก็บเป็น event-time symbol แยกจาก canonical company identity อย่างไร
2. `TIDLOR` ต้องเก็บ company name แบบ period-specific
3. 2026 H2 ต้องเก็บ original/revised provenance แม้รายชื่อ SET50 ไม่เปลี่ยน
4. Calendar boundary วันที่ 2024-01-01 ต้องกำหนดวิธีเก็บใน data model
5. Coverage ก่อน 2023 H1 ยังไม่มี จึงห้ามอ้างว่า dataset ครบ 2016-2026
6. Yahoo Ticker ยังเป็น UNVERIFIED และอยู่นอก scope งานนี้

## Decision

**NOT_READY**

สรุปคำตอบ: Historical SET50 Universe ตั้งแต่ 2023 H1 ถึง 2026 H2 ผ่าน Snapshot count, duplicate, overlap และ membership continuity checks แล้ว แต่ยังไม่ผ่าน Symbol Mapping policy, revision provenance metadata และ calendar-boundary policy จึงยังไม่พร้อมสำหรับการสร้าง historical constituent CSV

## ข้อจำกัดของงานนี้

- ไม่สร้าง CSV
- ไม่ดาวน์โหลด Yahoo Finance
- ไม่ทำ Backtest
- ไม่ทำ Strategy
- ไม่แก้ PDF หรือ raw data
