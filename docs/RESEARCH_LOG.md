# Research Log กูเขียนเองแต่ AI เรียบเรียงย้ำๆๆ

## Project Overview

โปรเจกต์นี้ทำงานเกี่ยวกับการวางระบบ Data Pipeline และ Backtest สำหรับการแข่งขันเทรดหุ้น SET50 แบบ Long-only ใน Python โดยมีเป้าหมายเพื่อให้ทีมสามารถเลือกหุ้นที่เหมาะสม สร้าง Signal และบริหาร Portfolio ตามกฎของการแข่งขันได้อย่างมีระบบและสามารถตรวจสอบได้

เป้าหมายของการแข่งขันคือการสร้าง Strategy ที่สามารถทำกำไรได้จริงภายใต้กฎที่กำหนด เช่น Initial Capital เท่ากับ 10,000,000 THB, SET50 Universe, Long-only, Commission, VAT, Slippage, และ Allowed Order Types ที่ถูกกำหนดไว้

เราใช้เงินเริ่มต้น 10,000,000 THB และมุ่งเน้นไปที่หุ้นใน SET50 เท่านั้น โดยใช้ Python เป็นภาษาหลักในการพัฒนา Data Pipeline, Backtest, และ Logic ที่เกี่ยวข้องกับ Strategy ต่อไป

กฎสำคัญที่ทีมต้องคำนึงถึง ได้แก่:

- SET50 Universe เท่านั้น
- Long-only
- Initial Capital = 10,000,000 THB
- Commission = 0.157%
- VAT = 7% ของ Commission
- Slippage = 1 Tick Size
- Allowed Order Types = Limit Order และ Market-to-Limit IOC
- Minimum 5 stocks ที่ต้องมีการเทรดจริง

ตอนนี้โปรเจกต์อยู่ใน Phase ของการสร้างพื้นฐาน Data Pipeline และ Validation ก่อนเริ่มพัฒนา Strategy อย่างจริงจัง

---

## Current Status

### Completed

- โครงสร้างโปรเจกต์พื้นฐานถูกสร้างขึ้นแล้ว
- Data Pipeline สำหรับ Historical SET50 Constituents เริ่มมีอยู่แล้ว
- ระบบการค้นหา Symbol ที่ต้องโหลดจาก historical universe ถูกสร้างขึ้นแล้ว
- ระบบ Yahoo Finance ถูกแยกเป็น Data Source layer เพื่อให้สามารถเปลี่ยนเป็น official SET data หรือ data source อื่นในอนาคตได้
- Raw Data และ Processed Data ถูกแยกการจัดเก็บ
- Data Validation มีการตรวจสอบ Missing Values, Duplicate Data, Invalid Price, Timestamp, และ Chronological Order
- มีการสร้าง CLI สำหรับคำสั่ง data download และ data validate
- มีการเขียน Test สำหรับ pipeline ส่วนใหญ่แล้วผ่านจริง

### In Progress

- การเตรียม Historical SET50 constituent CSV จริงจาก source ที่สามารถใช้งานได้
- การทดสอบความถูกต้องของ Data Pipeline กับ dataset จริงมากขึ้น
- การประเมินว่าระบบ validation และ cleaning มีความเหมาะสมกับข้อมูลทางการหรือยัง
- การวางแผน Feature Engineering ก่อนเริ่ม Strategy จริง

### Not Started

- Strategy ที่มีการ Backtest จริง
- Feature Engineering ที่เป็นทางเลือกของ Strategy
- Portfolio Construction แบบมี Position Sizing จริง
- Risk Management แบบครบวงจร
- Execution Simulation แบบสมบูรณ์
- Performance Report ของ Strategy ที่ผ่านการทดสอบ
- Walk-forward Validation หรือ Out-of-Sample Testing

### Current Best Strategy

ยังไม่มี Strategy ที่ผ่านการทดสอบ

### Current Best Result

ยังไม่มีผลการทดลอง

### Biggest Current Risk

ความเสี่ยงที่ใหญ่ที่สุดตอนนี้คือความไม่แน่นอนของ Historical SET50 constituent data ที่ยังไม่มีไฟล์จริงใน repository สำหรับใช้เป็น universe ในแต่ละช่วงเวลา หากเราใช้ข้อมูลไม่ถูกต้อง เราจะเกิด Survivorship Bias และประเมินผล Backtest ผิดได้ง่ายมาก

อีกปัญหาหนึ่งคือยังไม่มี Strategy ที่มีผล Backtest จริง จึงยังไม่สามารถบอกได้ว่าแบบใดมีประสิทธิภาพ

### Next Milestone

ทีมควรเริ่มด้วยการจัดเตรียม Historical SET50 constituent CSV จริงใน data/raw/constituents, ตรวจสอบว่าระบบสามารถอ่านข้อมูลได้จริง, แล้วค่อยเริ่ม Feature Engineering และ Strategy ขั้นต่อไป โดยไม่ทำการ Backtest แบบไม่มั่นใจ

---

## Experiment Log

## EXP-001 — Historical SET50 Data Pipeline Setup

### เป้าหมาย

เราต้องการรู้ว่าระบบสามารถระบุหุ้นที่ต้องโหลดจาก historical universe ได้หรือไม่ และสามารถแยก Raw Data กับ Processed Data ได้อย่างถูกต้องหรือไม่

### สมมติฐาน

เราคิดว่าการใช้ Historical SET50 Constituents เพื่อกำหนด universe ในแต่ละช่วงเวลา จะช่วยลด Survivorship Bias และลดการโหลดข้อมูลที่ไม่จำเป็นได้

### ข้อมูลที่ใช้

- Data Source: Yahoo Finance via yfinance
- Universe: Historical SET50 constituent membership
- ช่วงเวลา: ขึ้นอยู่กับการกำหนดของ user ในแต่ละรอบงาน
- Timeframe: 1d
- Dataset: Research Data แบบสภาพแวดล้อม local

### วิธีทดลอง

เราสร้าง Data Pipeline ที่เริ่มจาก historical constituent CSV, ค้นหาสมาชิกที่มีสิทธิ์ในช่วงเวลาที่ต้องการ, รีเทิร์น union ของ symbols, normalize เป็น ticker ที่ใช้กับ Yahoo Finance, ตรวจสอบ cache, แล้ว download เฉพาะข้อมูลที่ขาดเท่านั้น

### หลักการที่ใช้

- Historical Universe
- Symbol Discovery
- Raw Data vs Processed Data
- Data Validation
- Survivorship Bias Control

หลักการเหล่านี้ช่วยให้ทีมไม่ใช้รายชื่อ SET50 ปัจจุบันไป Backtest ย้อนหลังแบบผิด ๆ

### กฎการแข่งขันที่เกี่ยวข้อง

- SET50 Universe
- Initial Capital = 10,000,000 THB
- Long-only
- Minimum 5 stocks
- Commission
- VAT
- Slippage
- Allowed Order Types

### ผลลัพธ์

จากการทดสอบจริงมีผลดังนี้:

- Test Result: 15 passed, 1 skipped

หมายเหตุ: ผลนี้เป็นผลจากการทดสอบ Data Pipeline และ Validation เท่านั้น ไม่ใช่ผล Backtest หรือ Strategy

### เราได้เรียนรู้อะไร

สิ่งที่เห็นจากข้อมูล:

- โครงสร้าง Data Pipeline พื้นฐานทำงานได้
- Historical constituent logic สามารถทำงานได้ตามการทดสอบ
- Cache logic ช่วยลดการโหลดข้อมูลซ้ำได้

การตีความ:

- Phase ปัจจุบันเหมาะสำหรับการสร้าง Data Foundation ก่อนเริ่ม Strategy
- เราไม่ควรข้ามไปทำ Strategy หรือ Backtest แบบไม่มีกลไกการตรวจสอบโครงสร้างข้อมูล

สิ่งที่ยังสรุปไม่ได้:

- ผลลัพธ์ทางการเงินของ Strategy ยังไม่ทราบ
- ประสิทธิภาพของ universe ที่ใช้จาก historical constituent ยังต้องมีข้อมูลจริงเพิ่มเติม

### ปัญหาและข้อจำกัด

- Historical constituent CSV จริงยังไม่มีใน repository
- Yahoo Finance เป็น Research Data เท่านั้น ไม่ใช่ Official SET Data
- ยังไม่มีข้อมูล Backtest จริงสำหรับ Strategy
- ข้อมูลที่ใช้ยังจำกัดในขอบเขตของ research environment
- Potential risk ของ Survivorship Bias หากผู้ใช้ใส่ข้อมูลไม่ตรงตาม historical period

### การตัดสินใจ

Decision: KEEP

เหตุผล: Data Pipeline หลักที่สร้างขึ้นมีโครงสร้างที่ถูกต้องและผ่านการทดสอบเบื้องต้นแล้ว เราควรเก็บไว้และต่อยอดต่อไป

### ขั้นตอนต่อไป

- เตรียม Historical SET50 constituent CSV จริง
- ตรวจสอบการอ่านไฟล์และ date-aware universe
- เริ่มวางแผน Feature Engineering
- เตรียม Strategy template ก่อนเริ่ม Backtest อย่างเป็นระบบ

---

## Experiment Log

## EXP-002 — Documentation Review and Repository Status Check

### เป้าหมาย

เราต้องการทราบว่า Repository ในปัจจุบันมีอะไรที่พร้อมใช้งานจริง อะไรที่ยังต้องทำต่อ และอะไรที่ยังไม่ควรสรุปว่าเสร็จ

### สมมติฐาน

ถ้าทีมระบุสถานะจริงของ repository อย่างชัดเจน จะช่วยหลีกเลี่ยงการสรุปผลลัพธ์ที่ยังไม่มีฐานข้อมูลรองรับ

### ข้อมูลที่ใช้

- Data Source: Repository และ source code ที่มีอยู่จริง
- Universe: ไม่เกี่ยวข้องกับ stock universe ของการแข่งขันในระดับ strategy
- ช่วงเวลา: ปัจจุบัน
- Timeframe: N/A
- Dataset: Project source files

### วิธีทดลอง

อ่าน AGENTS.md, README, และโครงสร้าง repository เพื่อกำหนดสถานะปัจจุบันและสรุปสิ่งที่มีจริงใน repo

### หลักการที่ใช้

- Repository Status Review
- Documentation Discipline
- Evidence-based Reporting

### กฎการแข่งขันที่เกี่ยวข้อง

- ไม่ควรสร้าง Performance ปลอม
- ไม่ควรสรุป Strategy สำเร็จ ถ้ายังไม่มีผล Backtest
- ไม่ควรใช้ข้อมูลที่ไม่มีอยู่จริง

### ผลลัพธ์

ยังไม่ได้ทดสอบในเชิง financial

แต่การตรวจสอบ repository หลักยืนยันว่า:

- Data Pipeline เบื้องต้นมีอยู่
- Strategy ยังไม่ได้เริ่มจริง
- Backtest ยังไม่เริ่ม

### เราได้เรียนรู้อะไร

สิ่งที่เห็นจากข้อมูล:

- Repo อยู่ในสถานะที่เริ่มจาก skeleton และเพิ่ม Data Layer อย่างมีระบบแล้ว

การตีความ:

- โปรเจกต์ยังอยู่ในจุดเริ่มต้นของ pipeline และยังไม่ถึง stage ของ Strategy หรือ Backtest ที่สมบูรณ์

### ปัญหาและข้อจำกัด

- เอกสารต้องล้อมรอบข้อมูลจริงเท่านั้น
- เป็นเรื่องสำคัญที่ต้องไม่เพิ่มผลลัพธ์ปลอม

### การตัดสินใจ

Decision: KEEP

เหตุผล: เราควรรักษาความโปร่งใสและรายงานสถานะตามความจริง

### ขั้นตอนต่อไป

- ดำเนินการต่อด้วย Documentation อย่างครบถ้วน
- เตรียม Historical constituent dataset จริง
- เริ่ม Feature Engineering หลังจากมี Data Foundation ที่แข็งแรงแล้ว
