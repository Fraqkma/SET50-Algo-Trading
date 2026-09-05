# Official SET50 Constituent Archive

โฟลเดอร์นี้เก็บ Official SET Constituents List PDFs และ extracted text ที่ใช้ตรวจสอบ Historical SET50 Snapshot

ไฟล์ `*.pdf` เป็น source documents จาก SET โดยตรง
ไฟล์ `*.txt` เป็น text extraction จาก PDF ด้วย `pypdf` เพื่อให้อ่านและค้นหาได้ง่าย

## Periods

| File | Effective period | Official source URL |
|---|---|---|
| 2023_H1.pdf | 2023-01-01 ถึง 2023-06-30 | https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf |
| 2023_H2.pdf | 2023-07-01 ถึง 2023-12-31 | https://media.set.or.th/set/Documents/2023/Jun/SET50-SET100_H2_2023.pdf |
| 2024_H1.pdf | 2024-01-02 ถึง 2024-06-30 | https://media.set.or.th/set/Documents/2023/Dec/SET50_100_H1_2024.pdf |
| 2024_H2.pdf | 2024-07-01 ถึง 2024-12-31 | https://media.set.or.th/set/Documents/2024/Jun/SET50_100_H2_2024.pdf |
| 2025_H1.pdf | 2025-01-01 ถึง 2025-06-30 | https://media.set.or.th/set/Documents/2024/Dec/SET50_100_H1_2025.pdf |
| 2025_H2.pdf | 2025-07-01 ถึง 2025-12-31 | https://media.set.or.th/set/Documents/2025/Jun/SET50_100_H2_2025.pdf |
| 2026_H1.pdf | 2026-01-01 ถึง 2026-06-30 | https://media.set.or.th/set/Documents/2025/Dec/SET50_100_H1_2026.pdf |
| 2026_H2.pdf | 2026-07-01 ถึง 2026-12-31 | https://media.set.or.th/set/Documents/2026/Jul/SET50_SET100_H2_2026_revise.pdf |

Archive page:

https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100

## Audit Status

- ทุก PDF มี SET50 rows 1-50 ครบ 50 symbols
- ทุก Snapshot มี 50 unique symbols และไม่พบ duplicate ใน rows 1-50
- ยังไม่ใช่ final CSV
- ยังไม่มี Yahoo Finance data ในโฟลเดอร์นี้
- Symbol Mapping และ revision issues ติดตามไว้ที่ `docs/CONSTITUENT_AUDIT.md`
