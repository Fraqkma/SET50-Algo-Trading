# Data Report กูเขียนเองแต่ AI เรียบเรียงย้ำๆๆ

## Data Sources

### Research Data

ข้อมูลที่ใช้สำหรับการพัฒนาระบบและทดลองในระยะเริ่มต้นคือ Yahoo Finance ผ่าน package ชื่อ yfinance

ข้อมูลนี้ใช้สำหรับ:

- การดาวน์โหลด OHLCV แบบ historical
- การทดสอบ Data Pipeline
- การตรวจสอบความถูกต้องของ Data Validation
- การพัฒนาระบบที่สามารถเปลี่ยน Data Source ได้ในอนาคต

ข้อมูลที่ได้มีลักษณะเป็น market data แบบ day-level และเหมาะสำหรับการพัฒนาใน research environment เท่านั้น

ข้อจำกัด:

- Yahoo Finance ไม่ใช่ Official SET Data
- การใช้ข้อมูลนี้มีไว้สำหรับการวิจัยและพัฒนาเท่านั้น
- อาจมีข้อจำกัดเรื่องตลาด, missing trading days, หรือ data quality ตาม source

### Competition Data

ยังไม่ดำเนินการ

ตอนนี้ยังไม่มีข้อมูลจาก official competition หรือ official SET source ที่ถูกผนวกเข้ากับ repository

---

## Historical SET50 Constituents

หุ้นใน SET50 ไม่ได้เป็นหุ้นชุดเดิมตลอดเวลา

ความหมายคือ หุ้นบางตัวอาจอยู่ใน SET50 ในช่วงหนึ่ง แต่ไม่อยู่ในช่วงถัดไป ดังนั้นถ้าเราใช้รายชื่อหุ้น SET50 ในปัจจุบันแล้วนำไป Backtest ย้อนหลัง เราจะมีปัญหาเรื่อง Survivorship Bias

ตัวอย่างง่าย ๆ คือ:

"ถ้าเราใช้รายชื่อ SET50 ปี 2026 แล้วเอาไป Backtest ย้อนหลังถึงปี 2020 เราอาจจะใช้หุ้นที่ตอนปี 2020 ยังไม่ใช่ SET50 แล้วทำให้ผลดูดีเกินความจริง"

ดังนั้นระบบต้องระบุให้ชัดว่าหุ้นตัวไหนอยู่ใน SET50 ในช่วงเวลาไหน เพื่อให้ historical universe ถูกต้อง และไม่ใช้เอาตัวปัจจุบันไปแทนทุกช่วงเวลาโดยไม่ตรวจสอบ

---

## Data Pipeline

Workflow ของ Data Pipeline มีลักษณะดังนี้:

Historical SET50 Constituents
→ Symbol Discovery
→ Download
→ Raw Data
→ Validation
→ Cleaning
→ Processed Data
→ Feature Engineering

แต่ละขั้นตอนมีความหมายดังนี้:

1. Historical SET50 Constituents
   - เริ่มจากข้อมูล historical membership ของหุ้นใน SET50
   - ต้องรู้ว่าแต่ละช่วงเวลา มีหุ้นอะไรอยู่ใน universe

2. Symbol Discovery
   - ระบบหาสมาชิกที่ต้องโหลดในช่วงเวลานั้น
   - เอา union ของหุ้นทั้งหมดที่มีสิทธิ์แล้วลบซ้ำ

3. Download
   - โหลดเฉพาะหุ้นที่จำเป็น เท่านั้น
   - ไม่โหลดข้อมูลเกินกว่าช่วงเวลาที่ต้องใช้

4. Raw Data
   - เก็บข้อมูลที่ได้จาก source โดยตรง
   - ไม่แก้ไขหรือปรับข้อมูลในขั้นนี้

5. Validation
   - ตรวจว่า Data ถูกต้องหรือไม่ เช่น Timestamp, Missing Value, Price, Volume, Sequence

6. Cleaning
   - แก้ไขหรือปรับรูปแบบที่จำเป็นให้เข้ากับ Data Model แบบ consistent

7. Processed Data
   - เก็บข้อมูลที่ผ่าน validation และ cleaning แล้ว

8. Feature Engineering
   - ใช้ข้อมูลที่ผ่านการ cleaning แล้วในการสร้าง Feature สำหรับ Strategy ต่อไป

---

## Data Validation

ระบบตรวจสอบว่า Data มีความถูกต้องหรือไม่ เช่น:

- Missing Values
- Duplicate Data
- Invalid Price
- Negative Price
- Zero หรือ Invalid Volume
- Invalid Timestamp
- Chronological Order
- Missing Trading Days
- Invalid Symbol

เหตุผลที่ต้องตรวจสอบคือ ถ้าข้อมูลมีปัญหาเล็กน้อยแต่เราใช้ต่อไป จะทำให้ผล Strategy และ Backtest สูญเสียความน่าเชื่อถือได้ง่ายมาก

การ validate ที่เป็นรูปแบบนี้ช่วยให้ทีมรู้ว่า Data ไหนพร้อมใช้งาน และ Data ไหนต้องแก้ไขหรือ reject

---

## Raw vs Processed Data

Raw Data คือ ข้อมูลที่ได้จาก Source โดยตรง เช่น Yahoo Finance

Processed Data คือ ข้อมูลที่ผ่านการตรวจสอบและจัดรูปแบบแล้ว เช่น:

- ชื่อคอลัมน์ถูก normalize
- index ถูกจัดเรียงตามเวลา
- เรื่อง Duplicate ถูกจัดการ
- ข้อมูลที่ไม่มี หรือผิดพลาดถูกแยกออก

เหตุผลที่ต้องแยก 2 แบบคือ:

- เราต้องเก็บข้อมูลดิบเอาไว้เพื่อการตรวจสอบย้อนหลัง
- เราต้องไม่แก้ไข Raw Data ไปพร้อมกันในกระบวนการ cleaning
- ทำให้ทีมสามารถรู้ว่า Data ถูกปรับอะไรบ้าง และทำไม

---

## Data Limitations

ข้อมูลที่มีอยู่ใน repo ณ ปัจจุบันมีข้อจำกัดดังนี้:

- Historical SET50 constituent CSV จริงยังไม่ถูกเพิ่มเข้า repository
- Data Source ปัจจุบันเป็น Yahoo Finance สำหรับ research เท่านั้น
- ยังไม่มี official competition data ที่ใช้ใน production
- ยังไม่มี Strategy หรือ Backtest ที่ใช้ dataset จริงในระดับ full evaluation
- การเตรียม Historical universe ยังต้องอาศัยข้อมูลจริงจาก source ก่อนจึงจะสามารถให้ความเชื่อถือสูงได้

---

## Conclusion

Pipeline ของข้อมูลเริ่มมีความเป็นระบบแล้ว แต่ยังต้องใช้ data จริงจาก historical SET50 constituent source และ official data source ในอนาคต เพื่อให้ความถูกต้องและความน่าเชื่อถือสูงขึ้นตามข้อกำหนดของการแข่งขัน
