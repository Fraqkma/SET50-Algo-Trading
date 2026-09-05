# Historical SET50 Constituents Research อันนี้กูไม่ได้เขียน

## เป้าหมาย

เรากำลังหา Historical SET50 Constituents เพื่อให้ทราบว่า:

- หุ้นตัวไหนอยู่ใน SET50
- อยู่ในช่วงเวลาไหน
- membership เริ่มมีผลเมื่อไหร่
- membership สิ้นสุดเมื่อไหร่

ข้อมูลนี้จำเป็นสำหรับการทำ Data Pipeline ที่ไม่ใช้ข้อมูลปัจจุบันไปแทน historical period และเพื่อหลีกเลี่ยง Survivorship Bias ก่อนเริ่ม Backtest หรือ Strategy

เป้าหมายของการวิจัยนี้ไม่ใช่เพื่อสร้าง CSV สุดท้ายทันที แต่เพื่อค้นหา source ที่เชื่อถือได้และตรวจสอบว่ามีข้อมูลในช่วงเวลาไหนจริงหรือไม่

---

## Sources Found

### 1) SET50 Index Overview
- ชื่อ Source: SET50 Index Overview
- Organization: Stock Exchange of Thailand (SET)
- URL: https://www.set.or.th/th/market/index/SET50
- ช่วงเวลาที่มีข้อมูล: ปัจจุบันและข้อมูลล่าสุดที่หน้าเว็บแสดง
- ประเภทข้อมูล: Current index dashboard, current constituents list, price, index statistics
- ความน่าเชื่อถือ: สูงมากสำหรับข้อมูลปัจจุบันของ SET
- ข้อสังเกต: เป็นแหล่งข้อมูลทางการของ SET และมีความน่าเชื่อถือสูงสำหรับข้อมูลปัจจุบัน แต่ไม่ใช่แหล่งที่ชัดเจนสำหรับ historical constituent archive แบบ end-to-end

### 2) SET Index / Factsheets / Indices
- ชื่อ Source: SET Index Factsheets / Indices
- Organization: Stock Exchange of Thailand (SET)
- URL: https://www.set.or.th/th/index/factsheets/indices
- ช่วงเวลาที่มีข้อมูล: ไม่ชัดเจนจากการตรวจสอบหน้าเว็บครั้งนี้
- ประเภทข้อมูล: Index information, factsheets, index reference materials
- ความน่าเชื่อถือ: สูงสำหรับข้อมูลทางการของ SET
- ข้อสังเกต: ดูเหมือนจะมีข้อมูล index ภาพรวม แต่ไม่พบการยืนยันชัดเจนว่าเป็น source ที่เก็บ historical constituent list แบบรายเดือน/รายปีในรูปแบบที่พร้อมใช้งานสำหรับ data engineering

### 3) SET50 Constituents Path
- ชื่อ Source: SET50 Constituents Page
- Organization: Stock Exchange of Thailand (SET)
- URL: https://www.set.or.th/th/index/set50/constituents
- ช่วงเวลาที่มีข้อมูล: ไม่พบข้อมูลที่สรุปได้จากการตรวจสอบครั้งนี้
- ประเภทข้อมูล: ตัวอย่างชัดเจนว่าเป็นหน้าที่ตั้งใจไว้สำหรับ constituents
- ความน่าเชื่อถือ: สูงหากหน้าเว็บมีข้อมูลจริง แต่ในปัจจุบัน page นี้แสดง “ไม่พบข้อมูลที่ท่านต้องการ” หรือไม่มีข้อมูลที่ใช้งานได้
- ข้อสังเกต: นี่เป็นตัวอย่างที่ชัดเจนว่าการค้นหา historical constituents จาก SET ไม่ใช่เรื่องที่มีการจัดวางเป็น file CSV หรือ archive ที่พร้อมใช้งานอย่างตรงไปตรงมาเสมอไป

### 4) SET Market Structure / Index Rules
- ชื่อ Source: SET Market Structure / Index Rules
- Organization: Stock Exchange of Thailand (SET)
- URL: https://www.set.or.th/th/market/index/market-structure
- ช่วงเวลาที่มีข้อมูล: ปัจจุบัน
- ประเภทข้อมูล: ระเบียบและโครงสร้างดัชนี
- ความน่าเชื่อถือ: สูงมาก
- ข้อสังเกต: เป็น source ที่ช่วยอธิบายกติกาและโครงสร้างของ index แต่ไม่ใช่ historical constituent archive โดยตรง

### 5) Reputable Financial Data Providers (Cross-check only)
- ชื่อ Source: Refinitiv / FactSet / Bloomberg / Investing.com / TradingView / other major vendors
- Organization: Reputable financial data vendors
- URL: หลายแหล่งตาม vendor ที่ใช้งาน
- ช่วงเวลาที่มีข้อมูล: ขึ้นอยู่กับ vendor แต่โดยทั่วไปมี historical index membership และ constituent history บางส่วน
- ประเภทข้อมูล: Constituent list, index methodology, historical rebalancing info
- ความน่าเชื่อถือ: สูงสำหรับข้อมูลทางการ/ commercial data แต่ต้องพิจารณา license, scope, และการอ้างอิงว่ามาจาก source ใด
- ข้อสังเกต: เหมาะสำหรับ cross-check แต่ไม่ควรใช้เป็น source หลักถ้ายังมี source ทางการของ SET ที่สามารถยืนยันได้

---

## Recommended Primary Source

### แหล่งหลักที่แนะนำ: SET Official Index Pages + SET Announcements / Index official documentation

เหตุผล:

- เป็น source ทางการของ SET
- มีความน่าเชื่อถือสูงกว่าระดับ website ทั่วไป
- เป็นแหล่งที่ควรใช้เป็น reference หลักสำหรับคำถามเรื่อง SET50 membership
- หาก SET มี announcement หรือ index change announcement เกี่ยวกับ constituent changes ก็จะเป็นหลักฐานที่สามารถยืนยันได้อย่างเป็นระบบ

อย่างไรก็ตาม จากการตรวจสอบเบื้องต้น เราพบว่า:

- page สำหรับ current SET50 overview มีอยู่จริง
- page สำหรับ constituents แบบย้อนหลังหรือ archive ไม่ใช่แหล่งที่ชัดเจนและพร้อมใช้งานในรูปแบบ file CSV อย่างตรงไปตรงมา
- ดังนั้น source ทางการของ SET ควรใช้เป็น primary source แต่ต้องมีการตรวจสอบ mechanism ที่แน่ชัดว่าทำอย่างไรเพื่อดึง historical membership history

---

## Cross-check Sources

แหล่งที่สามารถใช้ตรวจสอบซ้ำได้:

1. SET official index pages
   - https://www.set.or.th/th/market/index/SET50

2. SET official announcements / index-related documents
   - ควรค้นหาเอกสารหรือ announcement ที่เกี่ยวกับ SET50 composition changes, rebalancing, หรือ constituent additions/removals

3. Reputable financial data vendors
   - Refinitiv
   - FactSet
   - Bloomberg
   - Investing.com / TradingView (ใช้เป็น cross-check ไม่ใช่ primary source)

4. Archived public news / press release
   - ใช้เพื่อยืนยันวันที่และ stock ที่เปลี่ยน membership
   - แต่ต้องระวังว่า news article ไม่ใช่ source ทางการโดยตรงเสมอ

---

## Coverage

| Period | Source | Available? | Verified? | Notes |
|---|---|---|---|---|
| Current snapshot | SET50 Overview | Yes | Partially | Current index membership appears available on official SET page |
| Historical constituent archive | SET official pages | Unclear | Not yet verified | Not clearly exposed as a downloadable historical CSV |
| Major rebalancing announcements | SET announcements | Possibly | Not yet verified | Need manual search and validation |
| Long historical period | Cross-check vendors | Possibly | Not yet verified | Useful for cross-check, not primary |
| Full daily historical membership | Single official source | Unclear | Not yet verified | Likely requires combining multiple official announcements |

หมายเหตุ: ตารางนี้แสดงเฉพาะสิ่งที่มีหลักฐานจริงจากการตรวจสอบเบื้องต้นเท่านั้น ไม่ได้ยืนยันว่ามี historical coverage ครบทุกช่วงเวลา

---

## Data Extraction Method

ขั้นตอนที่คาดว่าจะใช้เมื่อมี source ที่ถูกต้อง:

1. รวบรวม official constituent changes จาก SET หรือ source ที่เชื่อถือได้
2. บันทึกแต่ละ event เป็นตัวอย่าง:
   - stock symbol
   - effective date
   - event type (added / removed)
   - reason (rebalancing / index review / corporate action)
3. แปลงข้อมูลนั้นให้เป็น format:

```csv
effective_from,effective_to,symbol
2024-01-01,2024-06-30,AOT
2024-01-01,2024-06-30,ADVANC
```

4. สำหรับแต่ละ symbol ให้กำหนดช่วง membership ที่มีผลจริง โดยใช้ช่วงที่เริ่มจาก effective_from จนถึง effective_to
5. ถ้ามีข้อมูลซ้ำหรือ overlap ให้ตรวจสอบด้วย manual review ก่อนนำไปใช้ใน Backtest

---

## Potential Problems

### 1) Survivorship Bias

ถ้าเราใช้รายชื่อ SET50 ปัจจุบันแล้วเอาไป Backtest ย้อนกลับ เราจะใช้หุ้นที่ไม่ได้อยู่ใน SET50 ในอดีต จนทำให้ผล Backtest ดูดีเกินจริง

### 2) Missing historical periods

บาง source อาจมีเฉพาะข้อมูลปัจจุบันหรือข้อมูลตั้งแต่ช่วงหลังเท่านั้น และไม่มี historical archive แบบเต็ม

### 3) Symbol changes

หุ้นบางตัวอาจเปลี่ยนชื่อย่อ หรือมีการเปลี่ยนรหัสตาม corporate action หรือการรวมบริษัท ดังนั้นต้องระวังเรื่อง symbol mapping

### 4) Company name changes

ชื่อบริษัท อาจเปลี่ยนจากชื่อเก่าไปอีกชื่อหนึ่ง แต่ ticker ไม่จำเป็นต้องเปลี่ยนเสมอไป

### 5) Corporate actions

เรื่อง merger, acquisition, restructuring, stock split, หรือการย้ายกลุ่มอาจทำให้ historical membership ต้องตีความใหม่

### 6) SET50 rebalancing dates

วันที่ member เปลี่ยนแปลงอาจไม่ตรงกับวันปิดตลาดหรือวันทำการปกติ ต้องตรวจสอบ effective date ให้ชัดเจน

### 7) Ambiguous effective dates

บาง source อาจระบุว่า “effective from announcement date” หรือ “effective from next trading day” ซึ่งต้องแยกให้ชัดก่อนนำไปใช้

---

## Verification Plan

ก่อนที่จะใช้ชุดข้อมูล Historical SET50 Constituents สำหรับ Backtesting ต้องมีการตรวจสอบแบบ manual ดังนี้:

1. ตรวจสอบ source ทางการของ SET ก่อนทุกอย่าง
   - ดูว่ามี announcement หรือ index review ที่ระบุ stock additions/removals หรือไม่

2. ตรวจสอบ date ของแต่ละ event
   - ให้แน่ใจว่า effective_from และ effective_to เป็นวันที่ที่มีหลักฐานชัดเจน

3. Cross-check กับ at least 1 source อื่น
   - ใช้ vendor หรือข่าวทางการ หรือ data provider ที่น่าเชื่อถือ

4. ตรวจสอบว่าช่วงเวลาไม่ว่างหรือไม่ซ้อนกันผิดปกติ
   - ถ้ามี overlap หรือ gap ให้อธิบายว่าเกิดจากอะไร

5. ตรวจสอบ symbol mapping
   - ชื่อย่อและชื่อบริษัทต้องตรงกับข้อมูล official source

6. ตรวจสอบความเป็นไปได้ของ historical continuity
   - ถ้าไม่มี data สำหรับช่วงหนึ่ง ให้ระบุชัดว่า missing period และไม่เติมตามความคิดของทีม

7. ก่อนนำไปใช้ Backtest
   - ต้องมี manual review บน sample subset ก่อน
   - ต้องมี list ของ symbol ที่ยืนยันแล้วว่ามี effective date ถูกต้อง

---

## สรุปเบื้องต้น

จากการสำรวจเบื้องต้น เราพบว่า:

- SET official pages มีข้อมูลปัจจุบันของ SET50 และมีความน่าเชื่อถือสูง
- แต่ historical constituent archive แบบเรียบร้อยและพร้อมใช้งานสำหรับ data engineering ยังไม่ชัดเจนจากการตรวจสอบในช่วงนี้
- การจัดหาข้อมูล historical constituent ที่แท้จริงจะต้องใช้การรวมข้อมูลจาก official announcements, historical index documents, และ cross-check sources
- ก่อนสร้าง final CSV ต้องมีการ manual verification อย่างละเอียดเพื่อป้องกัน Survivorship Bias และ misdated membership

---

## Next Recommended Step

Next step ที่เหมาะสมที่สุดคือ:

1. เริ่มจาก SET official index pages และ SET announcements ด้วย keyword ที่เกี่ยวกับ SET50 rebalancing และ constituent change
2. รวบรวมทุก event ที่ระบุ stock เพิ่ม/ลด จาก SET50
3. ตรวจสอบ effective date อย่างละเอียด
4. Cross-check กับ vendor หรือ source อื่นที่เชื่อถือได้
5. จัดทำ spreadsheet หรือ CSV draft แบบ provisional เพื่อให้ทีม review ก่อนสร้าง final dataset

> สิ่งสำคัญ: ไม่ควรสร้าง final constituent CSV จนกว่าจะได้ตรวจสอบ source และ effective dates ที่ชัดเจนแล้ว
