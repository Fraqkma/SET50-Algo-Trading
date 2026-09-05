# SET50 Symbol Audit

## ขอบเขต

ตรวจสอบ Official SET50 constituent PDFs ที่เก็บไว้ใน:

`data/raw/constituents/set50_archive/`

Periods ที่ตรวจสอบ:

- 2023_H1
- 2023_H2
- 2024_H1
- 2024_H2
- 2025_H1
- 2025_H2
- 2026_H1
- 2026_H2

วิธีตรวจสอบ:

- อ่านเฉพาะ SET50 rows 1-50 จาก PDF
- ไม่รวม SET100, Reserve List หรือ `Inclusion` / `Exclusion` text เป็น full Snapshot
- ไม่แก้ symbol
- ไม่สร้าง final CSV
- ไม่ดาวน์โหลด Yahoo Finance
- ไม่ทำ Backtest และไม่สร้าง Strategy

## Summary

ผลการตรวจสอบ:

- ทั้ง 8 periods มี SET50 rows ครบ 50 symbols
- แต่ละ period มี 50 unique symbols และไม่พบ duplicate
- พบ 63 unique symbols ตลอดช่วง 2023_H1 ถึง 2026_H2
- `SAWAD` และ `MRDIYT` เป็น symbols ที่ปรากฏใน full SET50 Snapshot จริง
- `TRUEE` และ `BANPUU` ปรากฏใน change-related text แต่ไม่อยู่ใน SET50 rows 1-50 ของ full Snapshot
- `INDEX` ที่พบจาก PDF extraction เป็น header artifact ไม่ใช่ constituent
- การที่ symbol หายจาก period หนึ่งยังสรุปไม่ได้ว่าเป็น ticker change อาจเป็น index membership change หรือ Corporate Action

## Symbol Appearance Overview

| Group | Symbols | Result |
|---|---|---|
| Present in every period | ADVANC, AOT, AWC, BBL, BDMS, BEM, BH, CPALL, CPF, CPN, CRC, DELTA, EGCO, GPSC, GULF, HMPRO, IVL, KBANK, KTB, KTC, LH, MINT, MTC, OR, OSP, PTT, PTTEP, PTTGC, RATCH, SCB, SCC, SCGP, TISCO, TOP, TRUE, TTB | No ticker change evidence in these PDFs |
| Present in selected periods | BANPU, BCP, BGRIM, BJC, BTS, CBG, CCET, CENTEL, CHG, COM7, EA, GLOBAL, INTUCH, KKP, SAWAD, TCAP, TIDLOR, TLI, TU, VGI, WHA | Treat as membership changes unless separate Corporate Action evidence exists |
| Seen only once | JMART, JMT, KCE, MRDIYT, TFG, THAI | Requires membership/ticker context; do not normalize automatically |
| Change-related only, not full Snapshot | TRUEE, BANPUU | Keep as source symbols in audit text; do not add to full membership |

## Symbol Mapping Table

| Original Symbol | Period | Issue | Evidence | Source | Recommended mapping | Status |
|---|---|---|---|---|---|---|
| TRUEE | 2023_H1 change-related text | Official SET notice identifies old symbol `TRUE` and new symbol `TRUEE`; not a typo proven by source | Company is TRUE Corporation Public Company Limited; old/new symbol fields are explicit | https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2023015414&symbol=TRUEE | Keep `TRUEE` as event-time source symbol. Do not replace with `TRUE` automatically | VERIFIED |
| TRUEE | 2023_H1 | Not present in SET50 rows 1-50; present in Exclusion text | PDF full Snapshot contains `TRUE`, while change text contains `TRUEE` | https://www.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf | Do not add `TRUEE` to full SET50 membership | VERIFIED |
| SAWAD | 2023_H1, 2023_H2, 2024_H1, 2025_H1, 2026_H1 | Appears and disappears across periods | It is present as a full SET50 row and has official company name Srisawad Corporation Public Company Limited | https://www.set.or.th/en/market/product/stock/quote/sawad/ | Keep `SAWAD`; treat missing periods as membership changes unless another Corporate Action source proves otherwise | VERIFIED |
| BANPUU | 2026_H2 change-related text | Temporary symbol related to BANPU/BPP amalgamation; not in SET50 rows 1-50 | Official SET notice states BANPU ticker changes to BANPUU in the relevant Corporate Action context | https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105409300&symbol=BPP | Keep `BANPUU` in Corporate Action/event records only; do not replace `BANPU` in Snapshot | VERIFIED |
| BANPUU | 2026_H2 | Not present in SET50 rows 1-50; appears in Exclusion-related section | Full revised Snapshot contains `BANPU`, not `BANPUU` | https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf | Do not add `BANPUU` to SET50 membership | VERIFIED |
| MRDIYT | 2026_H2 | New symbol appears in full SET50 rows 1-50 | PDF lists MR. D.I.Y. Holding (Thailand) Public Company Limited as `MRDIYT`; issuer confirms SET listing under this symbol | https://investor.mrdiy.co.th/en/updates/ir-press-release/148/mrdiyt-makes-market-debut-on-set-as-thailands-largest-ipo-in-2025 | Keep `MRDIYT`; no normalization | VERIFIED |
| TIDLOR | 2023_H1, 2023_H2, 2024_H2, 2025_H2, 2026_H1, 2026_H2 | Company name differs between PDFs | PDF uses names such as Ngern Tid Lor and TIDLOR Holdings while symbol remains `TIDLOR` | Official PDFs in `data/raw/constituents/set50_archive/` | Keep symbol `TIDLOR`; preserve company name as period-specific metadata | NEEDS_REVIEW |
| INDEX | Raw text extraction only | Header artifact, not a ticker | It does not occur in numbered SET50 rows 1-50 | Official PDFs in `data/raw/constituents/set50_archive/` | Exclude from symbols | VERIFIED |
| Yahoo Ticker | All periods | Yahoo mapping was not audited in this task | No Yahoo Finance download was allowed | Not applicable in this audit | Do not infer a Yahoo Ticker | UNVERIFIED |

## Suspicious Symbols

ส่วนนี้อธิบาย symbols ที่ต้องแยกจาก ordinary membership change หรือมีหลักฐานเกี่ยวกับ ticker/corporate event เพิ่มเติม

## Other Symbol Review

### Stable symbols

Symbols that appear in all 8 full Snapshots do not show a ticker change in this audit. This is evidence limited to these PDFs; it does not prove that no change occurred before 2023_H1.

### Membership changes versus ticker changes

Examples such as `BGRIM`, `GLOBAL`, `INTUCH`, `EA`, `SAWAD`, `CENTEL` and `VGI` appear or disappear between SET50 periods. The PDFs support an index membership change, but appearance alone is not evidence of a ticker change.

Therefore:

- Do not normalize a symbol merely because it is absent in a later period.
- Do not infer a merger, share class change or delisting from membership changes alone.
- Keep the original SET symbol in each Snapshot.

## Revision Audit

| Period | Repository File | Official Revision Evidence | Full SET50 Difference | Selected Source | Status |
|---|---|---|---|---|---|
| 2023_H1 | `2023_H1.pdf` | Filename contains `_revise`; PDF says Published on Apr 7, 2023 | Not compared with an original file in repository | Revised archive file | VERIFIED |
| 2023_H2 | `2023_H2.pdf` | No revision marker; PDF says Published on Jun 16, 2023 | Not applicable | Official archive file | VERIFIED |
| 2024_H1 | `2024_H1.pdf` | No revision marker; PDF says Update on Dec 18, 2023 | Not applicable | Official archive file | VERIFIED |
| 2024_H2 | `2024_H2.pdf` | No revision marker; PDF says Update on Jun 17, 2024 | Not applicable | Official archive file | VERIFIED |
| 2025_H1 | `2025_H1.pdf` | No revision marker; PDF says Update on Dec 18, 2024 | Not applicable | Official archive file | VERIFIED |
| 2025_H2 | `2025_H2.pdf` | No revision marker; PDF says Update on Jun 16, 2025 | Not applicable | Official archive file | VERIFIED |
| 2026_H1 | `2026_H1.pdf` | No revision marker; PDF says Update on Dec 15, 2025 | Not applicable | Official archive file | VERIFIED |
| 2026_H2 | `2026_H2.pdf` | Archive also exposes original and `_revise` links | SET50 rows 1-50 are identical: 50 symbols, 0 set differences | Revised: https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf; Original: https://media.set.or.th/set/Documents/2026/Jun/SET50-SET100-H2-2026.pdf | NEEDS_REVIEW |

### 2026 H2 Original versus Revised

ตรวจสอบ original และ revised PDF ด้วย `pypdf` แล้ว:

- Original: `2026/Jun/SET50-SET100-H2-2026.pdf`
- Revised: `2026/Jul/SET50_SET100_H2_2026_revise.pdf`
- ทั้งสองไฟล์มี SET50 rows 1-50 จำนวน 50 symbols และ 50 unique symbols
- `Added` จาก original ไป revised: ไม่มี
- `Removed` จาก original ไป revised: ไม่มี
- Full SET50 membership จึงเหมือนกัน
- Revised PDF เปลี่ยน `Update` date จาก June 17, 2026 เป็น August 3, 2026
- Reserve List และ change-related sections มีความแตกต่าง

Decision สำหรับ Snapshot:

- ใช้ revised PDF เป็น source หลัก เพราะเป็นไฟล์ที่ archive แสดงเป็น `between the periodic review update`
- ไม่ลบ original และไม่แก้ raw files
- เก็บ original URL ไว้เพื่อ audit trail
- สถานะยังเป็น `NEEDS_REVIEW` สำหรับ provenance ของ revision แม้ full SET50 rows จะเหมือนกัน

## Unresolved Issues

1. ยังไม่มี canonical policy ว่าจะรวม ticker identity ของ `TRUEE` กับ `TRUE` หรือเก็บเป็น event-time symbol แยกกัน
2. ยังไม่มี canonical policy ว่าจะรวม `BANPUU` กับ `BANPU` หรือเก็บเป็น temporary Corporate Action symbol แยกกัน
3. `TIDLOR` มี company-name continuity issue แต่ยังไม่มีเหตุผลให้เปลี่ยน symbol
4. ยังไม่ได้ทำ Yahoo Ticker audit ตาม scope ของงานนี้
5. Coverage ก่อน 2023_H1 ยังไม่มีใน folder จึงไม่ควรอ้างว่า historical coverage ครบตั้งแต่ 2016
6. `SAWAD` ที่หายจากบาง Snapshot ต้องไม่ถูกตีความเป็น ticker change โดยไม่มี Corporate Action source

## Decision

**NOT_READY_FOR_CSV**

เหตุผล:

- `TRUEE` และ `BANPUU` ยังต้องมี policy สำหรับ ticker identity กับ company identity
- 2026_H2 มี original/revised provenance ที่ต้องบันทึกใน data model แม้ full SET50 list จะเหมือนกัน
- `TIDLOR` ต้องเก็บ company name แบบ period-specific
- Historical coverage ก่อน 2023_H1 ยังขาด
- ยังไม่ได้ทำ Yahoo Ticker mapping ตาม scope ที่ผู้ใช้กำหนด

ไม่มีการแก้ symbol เดาเอง และไม่มีการสร้าง final CSV

## Next Step

1. กำหนด policy สำหรับ event-time ticker และ canonical company identity
2. เก็บ `source_url`, `revision_status`, `effective_from`, `effective_to` และ `company_name` ต่อ Snapshot row
3. ตรวจสอบ Corporate Action source เพิ่มสำหรับ `TRUEE`, `BANPUU` และ `TIDLOR`
4. ค้นหา Official SET PDFs ก่อน 2023_H1 หากต้องการขยาย historical coverage
5. ทำ Yahoo Ticker audit เป็นงานแยกเมื่อได้รับอนุญาต

**สรุป:** ตอนนี้ยังไม่พร้อมสร้าง historical constituent CSV
