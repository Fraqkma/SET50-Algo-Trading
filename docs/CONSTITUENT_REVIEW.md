# Historical SET50 Rebalancing Research

## เป้าหมาย

เรากำลังสร้าง Historical SET50 Universe เพื่อใช้ในการ Research และ Backtest

เป้าหมายของงานนี้คือ:

- ค้นหาการเปลี่ยนแปลงรายชื่อหุ้น SET50 จากแหล่งทางการของ SET
- ตรวจสอบ announcement date และ effective date อย่างชัดเจน
- แยกข้อมูลที่ยืนยันได้จากข้อมูลที่ยังไม่สามารถยืนยัน
- ป้องกัน survivorship bias และ no lookahead bias
- ไม่สร้าง final CSV จนกว่าจะมีหลักฐานที่น่าเชื่อถือเพียงพอ

> ข้อสังเกต: เราไม่ได้สร้าง final CSV, ไม่โหลด Yahoo Finance, และไม่เริ่ม Backtest ในขั้นตอนนี้

---

## Research Period

ช่วงที่ตรวจสอบคือ 2016-2026 โดยเน้นปีที่มีความเป็นไปได้ทาง official evidence:

- 2016-2022: ยังไม่พบ official SET rebalancing announcement ที่สามารถยืนยันได้จากการค้นหาในช่วงนี้
- 2023: พบ official constituent list PDF สำหรับช่วง Jan 1 - Jun 30, 2023
- 2024: พบ official SET News announcement สำหรับ semi-annual review และ official index constituent archive
- 2025-2026: พบ official constituent archive page และ PDF archive แต่ยังไม่มีเอกสาร rebalancing announcement ที่ชัดเจนในผลการค้นหา

---

## Archive Finding

หน้า Official SET archive ไม่ได้มีแค่ current snapshot เท่านั้น แต่มี period-specific PDF สำหรับ SET50 / SET100 ด้วย

จากการเปิด PDF ที่ดาวน์โหลดได้ พบว่า:

- แต่ละ PDF มี SET50 section แยกจาก SET100 section
- SET50 section มีรายการหุ้นครบ 50 symbols พร้อมลำดับ, symbol, company name และ sector
- PDF ระบุช่วงเวลาที่ใช้คำนวณ index เช่น `January 1 - June 30, 2025`
- PDF ระบุวันที่ update หรือวันที่ publish
- หลาย PDF มี `Inclusion` และ `Exclusion` ซึ่งเป็นหลักฐาน Added / Removed โดยตรง
- การใช้ archive ต่อเนื่องกันทำให้คำนวณ Added และ Removed ด้วย set difference ได้

ดังนั้น archive นี้สามารถใช้ reconstruct historical membership ได้ในระดับ period snapshot สำหรับช่วงที่มี PDF ครบและตรวจสอบได้

ข้อจำกัดคือ archive page แสดงปีจำนวนมาก แต่ไม่ใช่ทุก period ที่ถูกดึงมาและตรวจสอบได้ในงานนี้ และบาง period อาจมี revised document หรือ interim update

---

## Available Period Snapshots

รายการด้านล่างเป็น period ที่เปิด PDF และตรวจสอบ SET50 symbol list ได้จริงในงานวิจัยนี้

### 2023 H1

- Period: 2023-01-01 ถึง 2023-06-30
- Effective date: 2023-01-01 ตามช่วงที่ PDF ระบุ
- Published / update: 2023-04-07
- Source URL: https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf
- Complete list: YES, มี 50 symbols
- ใช้ reconstruct membership: YES สำหรับ snapshot นี้

SET50 symbols:

`ADVANC, AOT, AWC, BANPU, BBL, BDMS, BEM, BGRIM, BH, BTS, CBG, CENTEL, COM7, CPALL, CPF, CPN, CRC, DELTA, EA, EGCO, GLOBAL, GPSC, GULF, HMPRO, INTUCH, IVL, JMART, JMT, KBANK, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SAWAD, SCB, SCC, SCGP, TIDLOR, TISCO, TOP, TRUE, TTB, TU`

Explicit change fields in the PDF:

- Inclusion: `SAWAD, TRUE`
- Exclusion: `DTAC, TRUEE`

หมายเหตุ: inclusion / exclusion ใน PDF นี้เป็นข้อมูล change ที่ source ระบุโดยตรง แต่ต้องตรวจสอบ symbol mapping ของ `TRUEE` เพิ่มเติม เพราะชื่อ symbol นี้อาจเกี่ยวข้องกับ historical naming หรือข้อมูลเดิมของบริษัท

### 2024 H2

- Period: 2024-07-01 ถึง 2024-12-31
- Effective date: 2024-07-01
- Published / update: 2024-06-17
- Source URL: https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf
- Complete list: YES, มี 50 symbols
- ใช้ reconstruct membership: YES สำหรับ snapshot นี้

SET50 symbols:

`ADVANC, AOT, AWC, BBL, BCP, BDMS, BEM, BGRIM, BH, BJC, BTS, CBG, CENTEL, CPALL, CPF, CPN, CRC, DELTA, EA, EGCO, GLOBAL, GPSC, GULF, HMPRO, INTUCH, ITC, IVL, KBANK, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SCB, SCC, SCGP, TIDLOR, TISCO, TLI, TOP, TRUE, TTB, TU, WHA`

Explicit change fields in the PDF:

- Inclusion: `BCP, BJC, ITC, TIDLOR`
- Exclusion: `BANPU, COM7, KCE, SAWAD`

### 2025 H1

- Period: 2025-01-01 ถึง 2025-06-30
- Effective date: 2025-01-01
- Published / update: 2024-12-18
- Source URL: https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf
- Complete list: YES, มี 50 symbols
- ใช้ reconstruct membership: YES สำหรับ snapshot นี้

SET50 symbols:

`ADVANC, AOT, AWC, BANPU, BBL, BDMS, BEM, BGRIM, BH, BJC, BTS, CBG, CCET, COM7, CPALL, CPF, CPN, CRC, DELTA, EGCO, GLOBAL, GPSC, GULF, HMPRO, INTUCH, ITC, IVL, KBANK, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SAWAD, SCB, SCC, SCGP, TISCO, TLI, TOP, TRUE, TTB, TU, WHA`

Explicit change fields in the PDF:

- Inclusion: `BANPU, CCET, COM7, SAWAD`
- Exclusion: `BCP, CENTEL, EA, TIDLOR`

### 2025 H2

- Period: 2025-07-01 ถึง 2025-12-31
- Effective date: 2025-07-01
- Published / update: 2025-06-16
- Source URL: https://media.set.or.th/set/Documents/2025/Jun/SET50_100_H2_2025.pdf
- Complete list: YES, มี 50 symbols
- ใช้ reconstruct membership: YES สำหรับ snapshot นี้

SET50 symbols:

`ADVANC, AOT, AWC, BANPU, BBL, BCP, BDMS, BEM, BH, BJC, BTS, CBG, CCET, COM7, CPALL, CPF, CPN, CRC, DELTA, EGCO, GPSC, GULF, HMPRO, IVL, KBANK, KKP, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SCB, SCC, SCGP, TCAP, TIDLOR, TISCO, TLI, TOP, TRUE, TTB, TU, VGI, WHA`

Explicit change fields in the PDF:

- Inclusion: `BCP, KKP, TCAP, TIDLOR`
- Exclusion: `BGRIM, GLOBAL, ITC, SAWAD`

### 2026 H1

- Period: 2026-01-01 ถึง 2026-06-30
- Effective date: 2026-01-01
- Published / update: 2025-12-15
- Source URL: https://media.set.or.th/set/Documents/2025/Dec/SET50_100_H1_2026.pdf
- Complete list: YES, มี 50 symbols
- ใช้ reconstruct membership: YES สำหรับ snapshot นี้

SET50 symbols:

`ADVANC, AOT, AWC, BANPU, BBL, BCP, BDMS, BEM, BH, BJC, BTS, CBG, CCET, CENTEL, COM7, CPALL, CPF, CPN, CRC, DELTA, EGCO, GPSC, GULF, HMPRO, IVL, KBANK, KKP, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SCB, SCC, SCGP, TCAP, TIDLOR, TISCO, TLI, TOP, TRUE, TTB, TU, WHA`

Explicit change fields in the PDF:

- Inclusion: `CENTEL, SAWAD`
- Exclusion: `BCP, VGI`

ข้อสังเกต: เมื่อคำนวณจาก full snapshots, `SAWAD` ไม่ได้อยู่ใน 2026 H1 list แม้ข้อความ change field ที่ extract ได้แสดง `SAWAD` ในบริบทของ inclusion/exclusion ของเอกสาร จึงต้องตรวจสอบหน้า PDF ต้นฉบับและ layout เพิ่มเติมก่อนใช้ change field นี้เป็นหลักฐานเด็ดขาด

### 2026 H2

- Period: 2026-07-01 ถึง 2026-12-31
- Effective date: 2026-07-01
- Published / update: 2026-08-03
- Source URL: https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf
- Complete list: YES, มี 50 symbols
- ใช้ reconstruct membership: YES สำหรับ snapshot นี้

SET50 symbols:

`ADVANC, AOT, AWC, BANPU, BBL, BCP, BDMS, BEM, BH, BJC, CCET, COM7, CPALL, CPF, CPN, CRC, DELTA, EGCO, GPSC, GULF, HMPRO, IVL, KBANK, KKP, KTB, KTC, LH, MINT, MRDIYT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SCB, SCC, SCGP, TCAP, TFG, THAI, TIDLOR, TISCO, TLI, TOP, TRUE, TTB, TU, WHA`

Explicit change fields in the PDF:

- Inclusion: `BANPU`
- Exclusion: `BANPUU`

ข้อสังเกต: `BANPUU` ต้องถูกตรวจสอบเป็น Symbol Issue เพราะ full snapshot เปลี่ยนจาก 2026 H1 ไป 2026 H2 ในหลาย symbols และชื่อ `BANPUU` อาจเป็น reserve-list หรือ typo/layout extraction ไม่ใช่ removal จาก SET50 โดยตรง

---

## Can Added / Removed Be Calculated?

ได้ สำหรับ period ที่มี full snapshot สองช่วงติดกันและใช้ symbol mapping เดียวกัน:

```text
Added = CurrentPeriodSymbols - PreviousPeriodSymbols
Removed = PreviousPeriodSymbols - CurrentPeriodSymbols
```

ตัวอย่างที่คำนวณได้จาก snapshots ที่ตรวจสอบแล้ว:

| Transition | Added จาก set difference | Removed จาก set difference | ใช้ได้หรือไม่ |
|---|---|---|---|
| 2024 H2 เทียบกับ 2023 H1 | BCP, BJC, ITC, TLI | BANPU, COM7, EA, KCE, SAWAD | PARTIAL: มีช่วง 2023 H2 และ 2024 H1 ที่ยังไม่ได้ตรวจสอบ จึงไม่ควรถือว่าเป็น direct consecutive review |
| 2025 H1 เทียบกับ 2024 H2 | BANPU, CCET, COM7, SAWAD | BCP, CENTEL, EA, ITC, TIDLOR | YES, direct adjacent snapshots |
| 2025 H2 เทียบกับ 2025 H1 | BCP, KKP, TCAP, TIDLOR, VGI | BGRIM, GLOBAL, ITC, SAWAD, TLI | YES, direct adjacent snapshots |
| 2026 H1 เทียบกับ 2025 H2 | CENTEL | VGI | YES จาก full snapshot; explicit change field ยังต้องตรวจสอบ |
| 2026 H2 เทียบกับ 2026 H1 | MRDIYT, TFG, THAI | CENTEL | PARTIAL: full snapshot ใช้ได้ แต่ revised PDF มี change field ที่ต้องตรวจสอบ |

หลักการสำคัญ:

- Full snapshot ทำให้คำนวณ Added / Removed ได้ แม้ source จะไม่มี change field
- ต้องใช้ period ที่ติดกันจริง ไม่ข้าม period ที่ยังไม่มี PDF
- ต้อง normalize symbol และจัดการ ticker change ก่อน set comparison
- revised PDF ต้องถือเป็น version ใหม่ และต้องตรวจสอบว่าแทนที่ PDF เดิมหรือไม่
- ผลจาก set difference ยังต้องถูก cross-check กับ official announcement เมื่อมี

---

## Verified Events

| Effective Date | Announcement Date | Added | Removed | Primary Source | Status |
|---|---|---|---|---|---|
| 2023-01-01 | 2023-04-07 | SAWAD, TRUE | DTAC, TRUEE | https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf | PARTIAL |
| 2024-07-01 | 2024-06-17 | BCP, BJC, ITC, TIDLOR | BANPU, COM7, KCE, SAWAD | https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf | VERIFIED |
| 2025-01-01 | 2024-12-18 | BANPU, CCET, COM7, SAWAD | BCP, CENTEL, EA, TIDLOR | https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf | VERIFIED |
| 2025-07-01 | 2025-06-16 | BCP, KKP, TCAP, TIDLOR, VGI | BGRIM, GLOBAL, ITC, SAWAD | https://media.set.or.th/set/Documents/2025/Jun/SET50_100_H2_2025.pdf | VERIFIED |
| 2026-01-01 | 2025-12-15 | CENTEL | VGI | https://media.set.or.th/set/Documents/2025/Dec/SET50_100_H1_2026.pdf | PARTIAL |
| 2026-07-01 | 2026-08-03 | TFG, THAI | CENTEL | https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf | PARTIAL |

หมายเหตุ:

- สำหรับ period ที่มี full snapshot สองช่วงติดกัน เราคำนวณ Added / Removed จาก symbol set ได้
- `VERIFIED` หมายถึง full snapshot และ effective period ชัดเจน และ set difference ใช้ได้โดยไม่มีช่วงที่ขาดระหว่างสอง snapshot
- `PARTIAL` หมายถึงมี symbol หรือ revision issue ที่ต้องตรวจสอบกับ PDF layout ต้นฉบับเพิ่มเติม
- เราไม่เติม symbol ที่ไม่ปรากฏใน source

---

## Secondary Evidence

| Effective Date | Added | Removed | Source | Official Source Found? | Status |
|---|---|---|---|---|---|
| 2023-01-01 to 2023-06-30 | Complete official SET50 snapshot | SAWAD, TRUE / DTAC, TRUEE fields present | https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf | YES | PARTIAL |
| 2024-07-01 to 2024-12-31 | Complete official SET50 snapshot | BCP, BJC, ITC, TIDLOR / BANPU, COM7, KCE, SAWAD | https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf | YES | VERIFIED |
| 2025-01-01 to 2025-06-30 | Complete official SET50 snapshot | BANPU, CCET, COM7, SAWAD / BCP, CENTEL, EA, TIDLOR | https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf | YES | VERIFIED |
| 2025-07-01 to 2025-12-31 | Complete official SET50 snapshot | BCP, KKP, TCAP, TIDLOR, VGI / BGRIM, GLOBAL, ITC, SAWAD | https://www.set.or.th/services/download?url=https://media.set.or.th/set/Documents/2025/Jun/SET50_100_H2_2025.pdf&name=SET50_100_H2_2025 | YES | VERIFIED |
| 2026-01-01 to 2026-06-30 | Complete official SET50 snapshot | CENTEL, SAWAD / BCP, VGI fields require review | https://media.set.or.th/set/Documents/2025/Dec/SET50_100_H1_2026.pdf | YES | PARTIAL |
| 2026-07-01 to 2026-12-31 | Complete official SET50 snapshot | TFG, THAI / CENTEL by set difference | https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf | YES | PARTIAL |

หมายเหตุ:

- ตารางนี้เป็น evidence ของ constituent list archive มากกว่า event-by-event announcement
- รายการนี้มี full snapshot จึงใช้ reconstruct membership period ได้
- Added / Removed ต้องคำนวณจาก consecutive snapshots และไม่ควรข้าม period ที่ไม่มีเอกสาร

---

## Year-by-Year Coverage

| Year | Events Found | Official Source | Secondary Source | Status |
|---|---:|---|---|---|
| 2016 | 0 | No clear official event found in this review | None found | NO EVIDENCE |
| 2017 | 0 | No clear official event found in this review | None found | NO EVIDENCE |
| 2018 | 0 | No clear official event found in this review | None found | NO EVIDENCE |
| 2019 | 0 | No clear official event found in this review | None found | NO EVIDENCE |
| 2020 | 0 | No clear official event found in this review | None found | NO EVIDENCE |
| 2021 | 0 | No clear official event found in this review | None found | NO EVIDENCE |
| 2022 | 0 | No clear official event found in this review | None found | NO EVIDENCE |
| 2023 | 1 complete snapshot | Official SET constituent list PDF found | None required | PARTIAL |
| 2024 | 1 complete snapshot in this review | Official SET constituent PDF and review page found | None required | VERIFIED for 2024 H2 only |
| 2025 | 2 complete snapshots | Official SET archive PDFs found | None required | VERIFIED |
| 2026 | 2 complete snapshots | Official SET archive PDFs found | None required | PARTIAL because symbol/revision issues remain |

---

## Source Links

### Official SET sources

- https://www.set.or.th/en/market/news-and-alert/newsdetails?id=85288900&symbol=SET
- https://www.set.or.th/en/market/news-and-alert/newsdetails?id=89679900&symbol=SET
- https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100
- https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf
- https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf
- https://www.set.or.th/services/download?url=https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf&name=SET50_100_H1_2025
- https://www.set.or.th/services/download?url=https://media.set.or.th/set/Documents/2025/Jun/SET50_100_H2_2025.pdf&name=SET50_100_H2_2025
- https://www.set.or.th/services/download?url=https://media.set.or.th/set/Documents/2025/Dec/SET50_100_H1_2026.pdf&name=SET50_100_H1_2026

### Supporting references reviewed

- https://www.set.or.th/en/market/index/SET50
- https://www.set.or.th/en/market/statistics/market-statistics/monthly-report/set50
- https://www.set.or.th/en/services/connectivity-and-data/data/historical

---

## Discrepancies

พบ discrepancy ระหว่าง full snapshot, explicit change fields และ PDF text extraction ในบาง period:

- 2026 H1 มี `SAWAD` ใน explicit Inclusion field แต่ไม่มี `SAWAD` ใน SET50 full snapshot
- 2026 H2 มี `BANPUU` ใน explicit Exclusion field แต่ full snapshot มี `BANPU` และไม่พบ `BANPUU` ใน SET50 list
- 2023 H1 มี `TRUEE` ใน Exclusion field แต่ต้องตรวจสอบว่าเป็น historical symbol, formatting issue หรือ symbol ที่ไม่ได้อยู่ใน SET50 snapshot เดียวกัน
- จึงต้องใช้ full SET50 table เป็นหลัก และถือ explicit change field ที่ขัดกันเป็น PARTIAL จนกว่าจะตรวจสอบ PDF layout ต้นฉบับด้วยตา

สิ่งที่สังเกตได้คือ:

- Official constituent archive page มี full list แบบ period-based
- Full snapshots ที่ติดกันทำให้คำนวณ Added / Removed ได้
- Official PDF บางฉบับมี Inclusion / Exclusion อยู่แล้ว
- Archive ที่เปิดเผยในหน้านี้ยังไม่เพียงพอที่จะยืนยันทุก period ตั้งแต่ 2016 โดยอัตโนมัติ

---

## Remaining Gaps

ช่วงที่ยังขาดหลักฐานหรือยังไม่สามารถยืนยันได้จาก official source ในงานวิจัยนี้:

- 2016-2022: ยังไม่ได้เปิดและตรวจสอบ PDF ของแต่ละ period
- 2023 H2 และ 2024 H1: ยังไม่มี snapshot ในชุดที่ตรวจสอบครั้งนี้ จึงไม่ควรเรียก 2024 H2 ว่า consecutive กับ 2023 H1
- Exact announcement-to-effective-date mapping สำหรับทุก period
- Symbol conflicts ใน 2023 และ 2026
- การยืนยันว่า revised PDF แทนที่ PDF เดิมหรือเป็น interim update
- Official historical archive ที่เปิดเผย full snapshot ครบทุก half-year ตั้งแต่ 2016

---

## Unverified Information

รายการต่อไปนี้ยังถือว่า UNVERIFIED หรือ PARTIAL ตามหลักฐานที่พบ:

- exact list of removed stocks for SET50 rebalancing in 2024
- full rebalancing event log for 2016-2022
- exact annual constituent audit trail before 2023
- any claim that a stock remained in SET50 across a period without direct official evidence

---

## Symbol Issues

ปัญหาเรื่อง symbol และ company name mapping ยังต้องมีการตรวจสอบต่อก่อนสร้าง final historical dataset:

- symbol change
- company name change
- ticker mapping
- delisting
- merger
- corporate action
- temporary removal / suspension
- free-float adjusted index updates

> เราไม่สมมติว่าหุ้นที่อยู่ใน SET50 ปัจจุบันจะอยู่ใน SET50 ในอดีต และไม่ใช้ current SET50 list เป็น historical universe

---

## Coverage

### Verified แล้ว

- 2024 H2, 2025 H1 และ 2025 H2 มี full SET50 snapshot และ consecutive set-difference ที่ใช้งานได้
- ทุก PDF ที่ระบุใน `Available Period Snapshots` มี SET50 list ครบ 50 symbols
- Archive สามารถใช้ reconstruct membership ได้สำหรับ period ที่มี full snapshot

### Partial แล้ว

- 2023 H1 เพราะ explicit `TRUEE` ต้องตรวจสอบ
- 2026 H1 เพราะ explicit `SAWAD` ไม่สอดคล้องกับ full snapshot
- 2026 H2 เพราะ explicit `BANPUU` ไม่สอดคล้องกับ full snapshot และเป็น revised PDF

### ยังขาด

- full evidence for every half-year before 2023
- 2023 H2 and 2024 H1 snapshots
- symbol mapping review for conflicting explicit fields

---

## Recommended Next Step

ก่อนสร้าง CSV ต้องทำต่อไปนี้:

1. เปิดและตรวจสอบ PDF ต้นฉบับของทุก period โดยเฉพาะ 2023 H1 และ 2026 H1/H2
2. ตรวจสอบ symbol conflicts ด้วย SET factsheet และ corporate-action records
3. ค้นหาและดาวน์โหลด 2023 H2, 2024 H1 และ period ก่อน 2023 จาก archive selector
4. คำนวณ Added / Removed จาก consecutive full snapshots เท่านั้น
5. บันทึก revision และ interim update แยกจาก regular review
6. เมื่อมีข้อมูลครบแล้ว จึงค่อยสร้าง provisional CSV สำหรับ manual review

---

## สรุปเชิงตัวเลข

1. Number of VERIFIED events: 3 snapshot-derived transitions / events
2. Number of PARTIAL events: 3 snapshot periods or transitions
3. Number of SECONDARY_ONLY events: 0
4. Years with evidence: 2023, 2024, 2025, 2026
5. Years without evidence: 2016, 2017, 2018, 2019, 2020, 2021, 2022
6. Best official sources found:
   - https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100
   - https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf
   - https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf
7. Remaining gaps:
   - full half-year coverage for 2016-2022
   - 2023 H2 and 2024 H1 snapshots
   - manual resolution of conflicting symbols in 2023 and 2026

---

## ข้อสรุปสุดท้าย

ผลการวิจัยพบว่า Official SET Constituents List archive ให้ full SET50 snapshots ที่มี 50 symbols ต่อ period และระบุ effective period อย่างชัดเจนใน PDF

ดังนั้นสามารถคำนวณ Added และ Removed จาก consecutive snapshots ได้ โดยใช้ set difference และสามารถ reconstruct membership ได้สำหรับช่วงที่มี snapshot ครบ

อย่างไรก็ตาม ยังไม่ควรสร้าง final CSV เพราะยังขาดบาง period, มี revised document และมี symbol conflicts ที่ต้อง manual verify โดยเฉพาะ `TRUEE`, `SAWAD` และ `BANPUU`