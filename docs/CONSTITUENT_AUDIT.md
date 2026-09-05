# SET50 Constituent Data Audit

## Audit Scope

เอกสารนี้เป็น final data audit ก่อนสร้าง historical constituent CSV

ขอบเขต:

- ตรวจสอบ 6 SET50 Snapshot ที่มีใน Official SET archive
- คำนวณ Added และ Removed เฉพาะ consecutive periods ที่กำหนด
- ตรวจสอบ Symbol Mapping ของ `TRUEE`, `SAWAD`, `BANPUU` และ `MRDIYT`
- ตรวจสอบว่า symbols มาจาก PDF โดยตรงหรือมาจากแหล่งอื่น

ยังไม่ทำสิ่งต่อไปนี้:

- ไม่สร้าง final CSV
- ไม่ดาวน์โหลด Yahoo Finance
- ไม่รัน Backtest
- ไม่แทนที่ disputed symbol โดยอัตโนมัติ

---

## Snapshot Audit

| Period | Effective Date | Source URL | Symbols | Unique | Duplicate | Missing Symbols | Status |
|---|---|---|---:|---:|---|---|---|
| 2023 H1 | 2023-01-01 | https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE |
| 2023 H2 | 2023-07-01 | https://media.set.or.th/set/Documents/2023/Jun/SET50-SET100_H2_2023.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE |
| 2024 H1 | 2024-01-02 | https://media.set.or.th/set/Documents/2023/Dec/SET50_100_H1_2024.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE |
| 2024 H2 | 2024-07-01 | https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE |
| 2025 H1 | 2025-01-01 | https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE |
| 2025 H2 | 2025-07-01 | https://media.set.or.th/set/Documents/2025/Jun/SET50_100_H2_2025.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE |
| 2026 H1 | 2026-01-01 | https://media.set.or.th/set/Documents/2025/Dec/SET50_100_H1_2026.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE |
| 2026 H2 | 2026-07-01 | https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf | 50 | 50 | None | None from rows 1-50 | COMPLETE WITH SYMBOL ISSUE |

### Snapshot Audit Method

- ตรวจเลขลำดับใน SET50 section ของแต่ละ PDF
- ตรวจ `Symbol` ทุกแถวโดยตรงจาก PDF text layer ด้วย `pypdf`
- ตรวจจำนวน symbols ด้วย set comparison
- ไม่รวม Reserve list, SET100 list หรือ `Inclusion` / `Exclusion` text เป็น SET50 snapshot
- Expected result คือ 50 symbols, 50 unique symbols และ 0 duplicates

ผลการตรวจ:

- ทั้ง 6 Snapshot มี 50 symbols
- ทั้ง 6 Snapshot มี 50 unique symbols
- ไม่พบ duplicate symbol ใน SET50 rows 1-50
- 2023 H2 PDF ระบุ `For calculating the index during Jul 1 - Dec 31, 2023`
- 2024 H1 PDF ระบุ `For calculating the index during January 2 - June 30, 2024`
- 2026 H2 มี `MRDIYT` เป็น row 29 และถือว่าเป็น symbol จริงใน full Snapshot
- `TRUEE` และ `BANPUU` ไม่อยู่ใน SET50 rows 1-50 ของ Snapshot ที่ตรวจสอบ แต่ปรากฏใน change-related text จึงไม่ถูกเพิ่มเข้า Snapshot โดยอัตโนมัติ

### Newly Closed Gaps: Exact SET50 Rows 1-50

#### 2023 H2

Source URL: https://media.set.or.th/set/Documents/2023/Jun/SET50-SET100_H2_2023.pdf

Effective Date: 2023-07-01

SET50 rows 1-50 จาก PDF โดยตรง:

`ADVANC, AOT, AWC, BANPU, BBL, BDMS, BEM, BGRIM, BH, BTS, CBG, CENTEL, COM7, CPALL, CPF, CPN, CRC, DELTA, EA, EGCO, GLOBAL, GPSC, GULF, HMPRO, INTUCH, IVL, KBANK, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SAWAD, SCB, SCC, SCGP, TIDLOR, TISCO, TLI, TOP, TRUE, TTB, TU, WHA`

Audit result: 50 symbols, 50 unique symbols, 0 duplicates, complete rows 1-50.

PDF change fields:

- Inclusion: `TLI, WHA`
- Exclusion: `JMT, JMART`

#### 2024 H1

Source URL: https://media.set.or.th/set/Documents/2023/Dec/SET50_100_H1_2024.pdf

Effective Date: 2024-01-02

SET50 rows 1-50 จาก PDF โดยตรง:

`ADVANC, AOT, AWC, BANPU, BBL, BDMS, BEM, BGRIM, BH, BTS, CBG, CENTEL, COM7, CPALL, CPF, CPN, CRC, DELTA, EA, EGCO, GLOBAL, GPSC, GULF, HMPRO, INTUCH, IVL, KBANK, KCE, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SAWAD, SCB, SCC, SCGP, TISCO, TLI, TOP, TRUE, TTB, TU, WHA`

Audit result: 50 symbols, 50 unique symbols, 0 duplicates, complete rows 1-50.

PDF change-related sections include a Reserve List and `Inclusion` / `Exclusion` labels. The full SET50 rows above are the authoritative Snapshot for this audit; no symbol was modified or inferred.

---

## Consecutive Period Comparison

คำนวณเฉพาะคู่ที่เป็น consecutive periods ตาม requirement:

```text
Added = Current Snapshot - Previous Snapshot
Removed = Previous Snapshot - Current Snapshot
```

| Previous | Current | Added | Removed | Status |
|---|---|---|---|---|
| 2023 H1 | 2023 H2 | TLI, WHA | JMART, JMT | VALID_CONSECUTIVE |
| 2023 H2 | 2024 H1 | KCE | TIDLOR | VALID_CONSECUTIVE |
| 2024 H1 | 2024 H2 | BCP, BJC, ITC, TIDLOR | BANPU, COM7, KCE, SAWAD | VALID_CONSECUTIVE |
| 2025 H1 | 2025 H2 | BCP, KKP, TCAP, TIDLOR, VGI | BGRIM, GLOBAL, ITC, SAWAD | VALID_CONSECUTIVE |
| 2025 H2 | 2026 H1 | CENTEL | BCP, VGI | VALID_CONSECUTIVE |
| 2026 H1 | 2026 H2 | MRDIYT, TFG, THAI | CENTEL | VALID_CONSECUTIVE_WITH_MAPPING_REVIEW |

### Non-consecutive Comparison

| Previous | Current | Result | Status |
|---|---|---|---|
| 2023 H1 | 2024 H2 | BCP, BJC, ITC, TLI / BANPU, COM7, EA, KCE, SAWAD | NON_CONSECUTIVE / GAP | ห้ามใช้เป็น normal rebalance |

ไม่คำนวณ Added / Removed แบบปกติจาก `2023 H1 -> 2024 H2` เพราะไม่มี:

- 2023 H2
- 2024 H1

Set difference ระหว่างสอง period นี้บอกได้เพียงว่า snapshots ต่างกัน แต่ไม่สามารถระบุได้ว่าการเปลี่ยนแปลงเกิดขึ้นใน period ใด

---

## Historical Gaps

ช่วงที่ขาดและยังไม่ควรสร้าง membership interval ต่อเนื่อง:

- ทุก period ก่อน 2023 H1 ที่ยังไม่ได้เปิดและตรวจสอบ PDF ใน audit นี้

ผลกระทบ:

- ไม่สามารถคำนวณ Added / Removed ของช่วงที่มี gap เป็น normal rebalancing ได้
- ไม่สามารถสมมติว่าสมาชิกจาก 2023 H1 ยังคงอยู่ก่อน 2023 H1 หรือข้าม period ที่ยังไม่มีหลักฐาน
- ต้องค้นหาและตรวจสอบ PDF ของช่วงที่หายก่อนสร้าง complete historical CSV

---

## Symbol Mapping Audit

| Original Symbol | Company | Correct Symbol | Yahoo Symbol | Evidence | Status |
|---|---|---|---|---|---|
| TRUEE | TRUE CORPORATION PUBLIC COMPANY LIMITED | TRUEE เป็น temporary/revised symbol ของ TRUE ใน official SET notice; ไม่แทนเป็น TRUE ใน CSV โดยอัตโนมัติ | UNRESOLVED | Official SET notice: https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2023015414&symbol=TRUEE | RESOLVED_AS_TEMPORARY_SYMBOL |
| SAWAD | SRISAWAD CORPORATION PUBLIC COMPANY LIMITED | SAWAD | SAWAD.BK เป็น candidate ที่มี secondary market reference แต่ยังไม่ได้ทดสอบกับ Yahoo Finance | SET PDF row: https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf; Reuters reference: https://www.reuters.com/markets/companies/SAWAD.BK/ | SET_SYMBOL_CONFIRMED; YAHOO_UNVERIFIED |
| BANPUU | BANPU PUBLIC COMPANY LIMITED | BANPUU เป็น temporary/revised symbol ที่ SET ระบุว่าเปลี่ยนจาก BANPU ในช่วง amalgamation; ห้ามแทนเป็น BANPU โดยอัตโนมัติ | UNRESOLVED | Official SET notice: https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105409300&symbol=BPP | TEMPORARY_SYMBOL_CONFIRMED; YAHOO_UNVERIFIED |
| MRDIYT | MR. D.I.Y. HOLDING (THAILAND) PUBLIC COMPANY LIMITED | MRDIYT | UNRESOLVED | Official SET quote result: https://www.set.or.th/en/market/product/stock/quote/mrdiyt/; issuer announcement: https://investor.mrdiy.co.th/en/updates/ir-press-release/148/mrdiyt-makes-market-debut-on-set-as-thailands-largest-ipo-in-2025 | SET_SYMBOL_CONFIRMED; YAHOO_UNVERIFIED |

### Symbol Mapping Findings

#### TRUEE

- Official SET search result ระบุ `Securities symbol - old: TRUE`
- Official SET search result ระบุ `Securities symbol - new: TRUEE`
- Company คือ TRUE Corporation Public Company Limited
- จึงไม่ใช่ OCR แบบสรุปได้ทันที
- เป็น temporary/revised ticker ในช่วงเวลาที่ SET ประกาศ
- ต้องรักษา symbol ตามวันที่ใน source หากสร้าง historical security master
- ไม่ควรแทนเป็น `TRUE` จนกว่าจะกำหนด policy สำหรับ ticker change

#### SAWAD

- เป็น symbol ที่ปรากฏใน SET50 full Snapshot ปี 2023
- PDF ระบุ company เป็น Srisawad Corporation Public Company Limited
- Official SET search result มีหน้า quote และ company profile ของ `SAWAD`
- เป็น valid SET ticker จากหลักฐานที่พบ
- ไม่พบหลักฐานว่า `SAWAD` เป็น ticker change หรือ OCR issue
- `SAWAD.BK` เป็น Yahoo Ticker candidate แต่ยังไม่ถูกตรวจสอบโดยการดาวน์โหลด Yahoo Finance

#### BANPUU

- ปรากฏใน change-related section ของ 2026 H2 PDF
- ไม่ปรากฏใน SET50 rows 1-50 ของ 2026 H2 Snapshot
- Official SET notice ระบุว่า ticker ของ BANPU จะเปลี่ยนเป็น BANPUU ตามข่าววันที่ 13 July 2026
- จึงเป็น temporary/revised symbol ที่มีหลักฐาน ไม่ใช่การเดา `BANPUU -> BANPU`
- ต้องเก็บ event และ effective date ของ ticker change แยกจาก index membership change
- Yahoo Ticker ยังไม่ยืนยัน

#### MRDIYT

- ปรากฏจริงใน SET50 rows 1-50 ของ 2026 H2 PDF
- PDF ระบุ company เป็น MR. D.I.Y. Holding (Thailand) Public Company Limited
- Official SET search result มี quote page ของ `MRDIYT`
- Issuer announcement ระบุว่าเริ่มซื้อขายบน SET ภายใต้ symbol `MRDIYT` วันที่ 5 November 2025
- เป็น valid SET ticker และไม่ใช่ OCR issue จากหลักฐานที่พบ
- Yahoo Ticker ยังไม่ยืนยัน จึงไม่ใส่ `.BK` โดยอัตโนมัติ

---

## Source Extraction Audit

| Period | Exact PDF URL | Extraction Source | OCR Used? | Suspicious Fields |
|---|---|---|---|---|
| 2023 H1 | https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf | PDF text layer via `pypdf` | No | `TRUEE` appears in Exclusion; source may represent temporary symbol change |
| 2023 H2 | https://media.set.or.th/set/Documents/2023/Jun/SET50-SET100_H2_2023.pdf | PDF text layer via `pypdf` | No | No issue in SET50 rows 1-50; change fields are explicit |
| 2024 H1 | https://media.set.or.th/set/Documents/2023/Dec/SET50_100_H1_2024.pdf | PDF text layer via `pypdf` | No | No issue in SET50 rows 1-50; Reserve List is separate |
| 2024 H2 | https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf | PDF text layer via `pypdf` | No | No issue in SET50 rows 1-50 |
| 2025 H1 | https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf | PDF text layer via `pypdf` | No | No issue in SET50 rows 1-50 |
| 2025 H2 | https://media.set.or.th/set/Documents/2025/Jun/SET50_100_H2_2025.pdf | PDF text layer via `pypdf` | No | No issue in SET50 rows 1-50 |
| 2026 H1 | https://media.set.or.th/set/Documents/2025/Dec/SET50_100_H1_2026.pdf | PDF text layer via `pypdf` | No | `SAWAD` appears in an Inclusion-related section but not in SET50 rows 1-50 |
| 2026 H2 | https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf | PDF text layer via `pypdf` | No | `BANPUU` appears in change-related text; `MRDIYT` is a valid row 29 symbol |

Archive page used to locate the hidden historical links:

https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100

ข้อสรุปของ extraction:

- SET50 symbols มาจาก PDF โดยตรง ไม่ได้มาจาก current SET page หรือ secondary list
- ไม่ได้ใช้ OCR
- `pypdf` สามารถอ่านข้อความและลำดับ 1-50 ได้
- การเรียงลำดับข้อความของ PDF ทำให้ส่วน `Reserve list`, `Inclusion` และ `Exclusion` อาจอยู่คนละตำแหน่งกับ visual layout
- ดังนั้น change-related fields ต้องตรวจสอบด้วย visual PDF review ก่อนใช้แทน full Snapshot

---

## Data Quality Issues

1. **Historical gaps**
   - ปิด gap 2023 H2 และ 2024 H1 แล้ว
   - ยังขาดทุก period ก่อน 2023 H1 ใน audit นี้

2. **Consecutive-period limitation**
   - ห้ามใช้ 2023 H1 -> 2024 H2 เป็น normal rebalance
   - ใช้ได้เฉพาะสามคู่ที่ระบุใน `Consecutive Period Comparison`

3. **Temporary ticker changes**
   - `TRUEE` เป็น symbol ที่ SET ประกาศเปลี่ยนจาก `TRUE`
   - `BANPUU` เป็น symbol ที่ SET ประกาศเปลี่ยนจาก `BANPU` ในช่วง amalgamation
   - ticker change ไม่เท่ากับ index membership change

4. **PDF text-order issue**
   - `SAWAD` และ `BANPUU` ปรากฏใน change-related text ที่ต้องแยกจาก SET50 rows
   - ไม่ควรนำทุก symbol หลัง `Inclusion` หรือ `Exclusion` ไปเพิ่มใน full Snapshot

5. **Yahoo Ticker not audited**
   - ยังไม่ได้ดาวน์โหลด Yahoo Finance ตาม requirement
   - ห้ามเดา mapping เป็น `.BK` สำหรับ disputed symbols

6. **Revision handling**
   - 2026 H2 ใช้ revised PDF
   - ต้องเก็บ original/revised version และตรวจสอบว่าฉบับใดเป็น authoritative version ก่อน final CSV

7. **Company-name continuity**
   - `TIDLOR` มี company name ต่างกันระหว่างบาง period เช่น Ngern Tid Lor และ TIDLOR Holdings
   - นี่เป็น company-name change / corporate event ที่ไม่ควรใช้เปลี่ยน symbol โดยอัตโนมัติ

8. **Archive coverage before 2023**
   - ยังไม่มีการเปิดและตรวจสอบ PDF ของทุก half-year ก่อน 2023 H1
   - จึงยังไม่ควรอ้างว่า historical coverage เริ่มครบตั้งแต่ 2016

---

## Final Recommendation

# NOT_READY_FOR_CSV

เหตุผล:

- ยังมี historical gaps ที่ทำให้ไม่สามารถสร้าง complete historical membership สำหรับช่วงที่ต้องการได้
- มี temporary/revised symbols ที่ต้องมี Symbol Mapping policy ตาม effective date
- Yahoo Ticker mappings ยังไม่ได้ตรวจสอบ และห้ามเดา
- 2026 H2 เป็น revised document ที่ต้องยืนยัน version
- `TRUEE`, `BANPUU`, `SAWAD` และ `MRDIYT` มีผลต่อการเชื่อม historical membership กับ price data

ขั้นตอนถัดไปก่อนสร้าง CSV:

1. ตรวจสอบ PDF visual layout ของทุก `Inclusion` / `Exclusion`
2. ดาวน์โหลดและตรวจสอบ periods ก่อน 2023 H1
3. สร้าง Symbol Mapping policy ที่แยก index membership ออกจาก ticker identity
4. ตรวจสอบ Yahoo Ticker mapping แยกเป็นงาน data-source audit หลังจากนี้
5. เก็บ source version, effective date และ revision status ต่อ row

> ผล audit นี้ไม่อนุญาตให้สร้าง final historical constituent CSV ในตอนนี้
