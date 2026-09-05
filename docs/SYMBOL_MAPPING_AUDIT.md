# SET50 Symbol Mapping & Revision Audit

## Summary

ตรวจสอบ Official SET50 PDF ทั้ง 8 periods จากโฟลเดอร์:

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

- อ่าน `SET50 rows 1-50` จาก PDF text layer ด้วย `pypdf`
- ไม่รวม SET100, Reserve List และข้อความ `Inclusion` / `Exclusion` เป็น full Snapshot
- ไม่แก้ ticker symbol
- ไม่ดาวน์โหลด Yahoo Finance
- ไม่สร้าง final CSV
- ไม่ทำ Backtest และไม่ทำ Strategy

ผลหลัก:

- ทุก period มี 50 symbols และ 50 unique symbols
- ไม่พบ duplicate ใน SET50 rows 1-50
- พบ 63 unique symbols ตลอดทั้ง 8 Snapshot
- `INDEX` ที่ปรากฏจาก raw text extraction เป็น header artifact และไม่ใช่ SET50 symbol
- `SAWAD` และ `MRDIYT` ปรากฏใน full SET50 Snapshot จริง
- `TRUEE` และ `BANPUU` ไม่ปรากฏใน full SET50 rows 1-50 ของช่วงที่ตรวจสอบ แต่ปรากฏใน change-related text
- จึงห้ามใช้ `TRUEE` หรือ `BANPUU` เป็น full membership โดยไม่มี policy และ source เพิ่มเติม

---

## Symbol Appearance Table

`Periods Present` แสดง period ที่ symbol อยู่ใน SET50 rows 1-50 จริง ส่วน `Periods Missing` แสดง period ที่ไม่พบใน full Snapshot

| Symbol | First Seen Period | Last Seen Period | Periods Present | Periods Missing |
|---|---|---|---|---|
| ADVANC | 2023_H1 | 2026_H2 | ทุก period | - |
| AOT | 2023_H1 | 2026_H2 | ทุก period | - |
| AWC | 2023_H1 | 2026_H2 | ทุก period | - |
| BANPU | 2023_H1 | 2026_H2 | 2023_H1, 2023_H2, 2024_H1, 2025_H1, 2025_H2, 2026_H1, 2026_H2 | 2024_H2 |
| BBL | 2023_H1 | 2026_H2 | ทุก period | - |
| BCP | 2024_H2 | 2026_H2 | 2024_H2, 2025_H2, 2026_H2 | 2023_H1, 2023_H2, 2024_H1, 2025_H1, 2026_H1 |
| BDMS | 2023_H1 | 2026_H2 | ทุก period | - |
| BEM | 2023_H1 | 2026_H2 | ทุก period | - |
| BGRIM | 2023_H1 | 2025_H1 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1 | 2025_H2, 2026_H1, 2026_H2 |
| BH | 2023_H1 | 2026_H2 | ทุก period | - |
| BJC | 2024_H2 | 2026_H2 | 2024_H2, 2025_H1, 2025_H2, 2026_H1, 2026_H2 | 2023_H1, 2023_H2, 2024_H1 |
| BTS | 2023_H1 | 2026_H1 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1 | 2026_H2 |
| CBG | 2023_H1 | 2026_H1 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1 | 2026_H2 |
| CCET | 2025_H1 | 2026_H2 | 2025_H1, 2025_H2, 2026_H1, 2026_H2 | 2023_H1, 2023_H2, 2024_H1, 2024_H2 |
| CENTEL | 2023_H1 | 2026_H1 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1, 2026_H1 | 2025_H2, 2026_H2 |
| CHG | 2024_H2 | 2024_H2 | 2024_H2 | ทุกช่วงอื่น |
| COM7 | 2023_H1 | 2026_H2 | 2023_H1, 2023_H2, 2024_H1, 2025_H1, 2025_H2, 2026_H1, 2026_H2 | 2024_H2 |
| CPALL | 2023_H1 | 2026_H2 | ทุก period | - |
| CPF | 2023_H1 | 2026_H2 | ทุก period | - |
| CPN | 2023_H1 | 2026_H2 | ทุก period | - |
| CRC | 2023_H1 | 2026_H2 | ทุก period | - |
| DELTA | 2023_H1 | 2026_H2 | ทุก period | - |
| EA | 2023_H1 | 2024_H2 | 2023_H1, 2023_H2, 2024_H1, 2024_H2 | 2025_H1, 2025_H2, 2026_H1, 2026_H2 |
| EGCO | 2023_H1 | 2026_H2 | ทุก period | - |
| GLOBAL | 2023_H1 | 2025_H1 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1 | 2025_H2, 2026_H1, 2026_H2 |
| GPSC | 2023_H1 | 2026_H2 | ทุก period | - |
| GULF | 2023_H1 | 2026_H2 | ทุก period | - |
| HMPRO | 2023_H1 | 2026_H2 | ทุก period | - |
| INTUCH | 2023_H1 | 2025_H1 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1 | 2025_H2, 2026_H1, 2026_H2 |
| IVL | 2023_H1 | 2026_H2 | ทุก period | - |
| JMART | 2023_H1 | 2023_H1 | 2023_H1 | ทุกช่วงอื่น |
| JMT | 2023_H1 | 2023_H1 | 2023_H1 | ทุกช่วงอื่น |
| KBANK | 2023_H1 | 2026_H2 | ทุก period | - |
| KCE | 2024_H1 | 2024_H1 | 2024_H1 | ทุกช่วงอื่น |
| KKP | 2025_H2 | 2026_H2 | 2025_H2, 2026_H1, 2026_H2 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1 |
| KTB | 2023_H1 | 2026_H2 | ทุก period | - |
| KTC | 2023_H1 | 2026_H2 | ทุก period | - |
| LH | 2023_H1 | 2026_H2 | ทุก period | - |
| MINT | 2023_H1 | 2026_H2 | ทุก period | - |
| MRDIYT | 2026_H2 | 2026_H2 | 2026_H2 | ทุกช่วงอื่น |
| MTC | 2023_H1 | 2026_H2 | ทุก period | - |
| OR | 2023_H1 | 2026_H2 | ทุก period | - |
| OSP | 2023_H1 | 2026_H2 | ทุก period | - |
| PTT | 2023_H1 | 2026_H2 | ทุก period | - |
| PTTEP | 2023_H1 | 2026_H2 | ทุก period | - |
| PTTGC | 2023_H1 | 2026_H2 | ทุก period | - |
| RATCH | 2023_H1 | 2026_H2 | ทุก period | - |
| SAWAD | 2023_H1 | 2026_H1 | 2023_H1, 2023_H2, 2024_H1, 2025_H1, 2026_H1 | 2024_H2, 2025_H2, 2026_H2 |
| SCB | 2023_H1 | 2026_H2 | ทุก period | - |
| SCC | 2023_H1 | 2026_H2 | ทุก period | - |
| SCGP | 2023_H1 | 2026_H2 | ทุก period | - |
| TCAP | 2025_H2 | 2026_H2 | 2025_H2, 2026_H1, 2026_H2 | 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1 |
| TFG | 2026_H2 | 2026_H2 | 2026_H2 | ทุกช่วงอื่น |
| THAI | 2026_H2 | 2026_H2 | 2026_H2 | ทุกช่วงอื่น |
| TIDLOR | 2023_H1 | 2026_H2 | 2023_H1, 2023_H2, 2024_H2, 2025_H2, 2026_H1, 2026_H2 | 2024_H1, 2025_H1 |
| TISCO | 2023_H1 | 2026_H2 | ทุก period | - |
| TLI | 2023_H2 | 2026_H2 | 2023_H2, 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1, 2026_H2 | 2023_H1 |
| TOP | 2023_H1 | 2026_H2 | ทุก period | - |
| TRUE | 2023_H1 | 2026_H2 | ทุก period | - |
| TTB | 2023_H1 | 2026_H2 | ทุก period | - |
| TU | 2023_H2 | 2026_H2 | 2023_H2, 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1, 2026_H2 | 2023_H1 |
| VGI | 2025_H2 | 2025_H2 | 2025_H2 | ทุกช่วงอื่น |
| WHA | 2024_H1 | 2026_H2 | 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1, 2026_H2 | 2023_H1, 2023_H2 |

หมายเหตุ: การที่ symbol หายจาก period หนึ่งไม่ได้แปลว่าเป็น ticker change เสมอไป อาจเป็น index membership change, Corporate Action หรือการเปลี่ยน composition ของ SET50

---

## Symbol Mapping Table

| Original Symbol | Normalized Symbol | Effective From | Effective To | Reason | Source | Confidence | Status |
|---|---|---|---|---|---|---|---|
| TRUEE | ยังไม่ normalize | ไม่ยืนยัน | ไม่ยืนยัน | Official SET notice ระบุ old symbol `TRUE` และ new symbol `TRUEE`; เป็น symbol change / temporary symbol ใน source แต่ยังไม่มี policy สำหรับรวม price history | https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2023015414&symbol=TRUEE | High สำหรับ symbol change; Low สำหรับ normalization | PARTIAL |
| BANPUU | ยังไม่ normalize | 2026-07-17 ตาม official notice context | ไม่ยืนยัน | Temporary symbol ระหว่าง Corporate Action / amalgamation ของ BANPU และ BPP | https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105409300&symbol=BPP | High สำหรับ temporary symbol; Low สำหรับ normalization | PARTIAL |
| SAWAD | SAWAD | 2023_H1 ในชุด PDF นี้ | 2026_H1 ในชุด PDF นี้ | เป็น valid SET ticker ที่อยู่ใน full Snapshot บางช่วง ไม่พบหลักฐานว่าเป็น typo หรือ ticker change | https://www.set.or.th/en/market/product/stock/quote/sawad/ | High | VERIFIED |
| MRDIYT | MRDIYT | 2026_H2 ในชุด PDF นี้ | 2026_H2 ในชุด PDF นี้ | เป็น valid SET ticker และอยู่ใน full SET50 rows 1-50 | https://www.set.or.th/en/market/product/stock/quote/mrdiyt/ | High สำหรับ SET symbol | VERIFIED |
| TIDLOR | TIDLOR | 2023_H1 ในชุด PDF นี้ | 2026_H2 ในชุด PDF นี้ | Company name เปลี่ยนใน PDF บาง period แต่ symbol ยังเป็น TIDLOR; ยังไม่ normalize เป็นชื่ออื่น | Official SET PDFs ใน `data/raw/constituents/set50_archive/` | Medium | PARTIAL |

กฎของ audit นี้คือไม่ map `TRUEE -> TRUE`, `BANPUU -> BANPU` หรือ map เป็น Yahoo Ticker เพราะยังไม่ได้ทำ price-source audit และไม่อนุญาตให้เดา

---

## Suspicious Symbols

### TRUEE

- ไม่พบใน SET50 rows 1-50 ของ 8 full Snapshots
- พบใน `SET50 Exclusion` ของ 2023_H1 PDF
- Official SET notice ระบุ `TRUE` เป็น old symbol และ `TRUEE` เป็น new symbol
- จัดเป็น symbol change / temporary symbol ไม่ใช่ typo ที่เราจะแก้เอง
- ยังไม่ normalize เพราะต้องกำหนด policy ว่าจะเก็บ ticker identity แบบ event-time หรือ canonical company identity
- Status: `PARTIAL`

### SAWAD

- พบใน full SET50 Snapshot ของ 2023_H1, 2023_H2, 2024_H1, 2025_H1 และ 2026_H1
- Official SET source มี company name เป็น Srisawad Corporation Public Company Limited
- ไม่พบหลักฐานว่าเป็น typo, share class issue หรือ symbol change
- การหายจากบาง period จัดเป็น membership change จนกว่าจะมี Corporate Action evidence อื่น
- Status: `VERIFIED` ในฐานะ SET symbol; ยังไม่ทำ Yahoo Ticker mapping

### BANPUU

- ไม่พบใน SET50 rows 1-50
- พบใน change-related text ของ 2026_H2 PDF
- Official SET notice สนับสนุนว่าเป็น temporary symbol ที่เกี่ยวข้องกับ BANPU/BPP amalgamation
- ไม่ควรนำเข้า full SET50 Snapshot และไม่ควรแทนเป็น BANPU โดยอัตโนมัติ
- Status: `PARTIAL`

### MRDIYT

- พบจริงใน 2026_H2 SET50 rows 1-50
- Company name ใน PDF คือ MR. D.I.Y. Holding (Thailand) Public Company Limited
- Official issuer information ระบุการเริ่มซื้อขายบน SET ภายใต้ symbol `MRDIYT`
- เป็น symbol ที่ SET ใช้จริง ไม่ใช่ OCR issue จากหลักฐานที่มี
- Status: `VERIFIED` สำหรับ SET symbol; Yahoo Ticker ยังไม่ตรวจสอบ

### INDEX

- ปรากฏจาก raw PDF text extraction บางครั้งในบริบท header เช่น `SET50 INDEX CONSTITUENTS`
- ไม่อยู่ใน numbered SET50 rows 1-50
- เป็น extraction artifact ไม่ใช่ symbol
- Status: `VERIFIED` ว่าไม่ใช่ constituent

---

## Revision Audit

| Period | File | Revision Evidence | Selected Source | Status |
|---|---|---|---|---|
| 2023_H1 | `2023_H1.pdf` | Filename มี `_revise`; PDF ระบุ Published on Apr 7, 2023 | `2023_H1.pdf` | VERIFIED |
| 2023_H2 | `2023_H2.pdf` | Filename ไม่มี revision marker; PDF ระบุ Published on Jun 16, 2023 | `2023_H2.pdf` | NO_ISSUE |
| 2024_H1 | `2024_H1.pdf` | Filename ไม่มี revision marker; PDF ระบุ Update on Dec 18, 2023 | `2024_H1.pdf` | NO_ISSUE |
| 2024_H2 | `2024_H2.pdf` | Filename ไม่มี revision marker; PDF ระบุ Update on Jun 17, 2024 | `2024_H2.pdf` | NO_ISSUE |
| 2025_H1 | `2025_H1.pdf` | Filename ไม่มี revision marker; PDF ระบุ Update on Dec 18, 2024 | `2025_H1.pdf` | NO_ISSUE |
| 2025_H2 | `2025_H2.pdf` | Filename ไม่มี revision marker; PDF ระบุ Update on Jun 16, 2025 | `2025_H2.pdf` | NO_ISSUE |
| 2026_H1 | `2026_H1.pdf` | Filename ไม่มี revision marker; PDF ระบุ Update on Dec 15, 2025 | `2026_H1.pdf` | NO_ISSUE |
| 2026_H2 | `2026_H2.pdf` | Filename มี `_revise`; PDF ระบุ Update on Aug 3, 2026 | `2026_H2.pdf` | PARTIAL: ต้องเก็บ revised source เป็น authoritative แต่ยังควรตรวจ original link เพิ่มเติม |

หลักการเลือก source:

- ใช้ PDF ที่อยู่ใน Official SET archive และมี period/effective information ชัดเจน
- ใช้ `_revise` version เมื่อ archive ระบุเป็นฉบับ revised
- ไม่ลบ original file และไม่แก้ไข PDF หรือ extracted text
- ถ้ามีหลาย version ต้องเก็บทุก version และบันทึกว่า version ใด authoritative

---

## Unresolved Issues

1. ยังไม่ยืนยัน canonical normalization ของ `TRUEE` และ `BANPUU`
2. ยังไม่ทราบ Yahoo Ticker mapping เพราะงานนี้ห้ามดาวน์โหลด Yahoo Finance
3. `TIDLOR` มี company-name continuity issue ระหว่าง Ngern Tid Lor และ TIDLOR Holdings
4. 2026_H2 เป็น revised PDF แต่ยังไม่ได้เก็บ original 2026 H2 PDF ใน repository เพื่อเปรียบเทียบ
5. Symbol ที่หายจาก Snapshot เช่น `SAWAD`, `EA`, `INTUCH`, `BGRIM` อาจเป็น membership change หรือ Corporate Action แต่ไม่ควรสรุปเป็น ticker change จาก appearance table อย่างเดียว
6. Period ก่อน 2023_H1 ยังไม่มี Snapshot ใน folder นี้ จึงยังมี historical coverage gap และอาจเกิด Survivorship Bias หากนำไปใช้กับช่วงก่อนหน้า

---

## Decision

**NOT_READY_FOR_CSV**

ยังไม่พร้อมสร้าง historical constituent CSV เพราะ:

- ยังมี unresolved Symbol Mapping policy สำหรับ `TRUEE` และ `BANPUU`
- ยังไม่มี Yahoo Ticker mapping audit สำหรับเชื่อม price data
- 2026_H2 revised-document provenance ยังต้องตรวจสอบ original/revised pair
- TIDLOR มี company-name continuity issue
- Coverage ก่อน 2023_H1 ยังไม่ครบ และอาจกระทบ Survivorship Bias

การตัดสินใจนี้ไม่ใช่การแก้ symbol เดาเอง แต่เป็นการคง symbol ตาม Official SET PDF และบันทึกสถานะไว้

---

## Next Step

1. เก็บ Official original/revised PDFs ของ 2026_H2 ถ้ามีทั้งสอง version
2. ตรวจสอบ effective date ของ `TRUEE` และ `BANPUU` จาก official SET Corporate Action notices เพิ่มเติม
3. กำหนด Symbol Mapping policy แยก ticker identity, company identity และ index membership
4. ตรวจสอบ period ก่อน 2023_H1 จาก Official SET archive
5. ทำ Yahoo Ticker audit เป็นงานแยก หลังจากอนุญาตให้ใช้ Yahoo Finance
6. สร้าง final CSV ได้เมื่อ source coverage และ Symbol Mapping policy ผ่าน manual review

**สรุป:** ตอนนี้ยังไม่พร้อมสร้าง historical constituent CSV
