# Data contract - Lab Day 10

Tài liệu này cụ thể hóa `contracts/data_contract.yaml` để người vận hành biết rõ source map, rule quarantine, và source of truth cho corpus Day 10.

---

## 1. Nguồn dữ liệu

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|--------------------|--------------------|----------------|
| `data/raw/policy_export_dirty.csv` | Batch export CSV từ hệ canonical | duplicate row, `doc_id` lạ, ngày không ISO, stale version | `raw_records`, `quarantine_records`, expectation halt |
| `data/docs/policy_refund_v4.txt` | Canonical text snapshot từ policy PDF | stale refund window, migration note còn sót | `refund_no_stale_14d_window`, `hits_forbidden` |
| `data/docs/hr_leave_policy.txt` | Canonical text snapshot từ HR PDF | trộn version 2025/2026 | `hr_leave_no_stale_10d_annual`, `required_doc_coverage` |
| `data/docs/sla_p1_2026.txt` | Canonical text snapshot từ IT SLA PDF | corpus thiếu doc hoặc top-k sai doc | `required_doc_coverage`, grading `gq_d10_02` |
| `data/docs/it_helpdesk_faq.txt` | Markdown export từ helpdesk knowledge base | missing chunk, duplicate content | `required_doc_coverage`, eval `q_lockout` |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| `chunk_id` | string | Có | ID ổn định để upsert Chroma và tránh duplicate khi rerun |
| `doc_id` | string | Có | Logical source id, phải thuộc allowlist trong contract |
| `chunk_text` | string | Có | Nội dung đã được clean, không còn stale marker hoặc duplicate |
| `effective_date` | date | Có | Chuẩn ISO `YYYY-MM-DD` sau transform |
| `exported_at` | datetime | Có | Chuẩn ISO `YYYY-MM-DDTHH:MM:SS`, dùng cho freshness |

---

## 3. Quy tắc quarantine va drop

- `unknown_doc_id`: đưa vào quarantine để giữ bằng chứng source map sai, không drop im lặng.
- `missing_effective_date`, `invalid_effective_date_format`, `invalid_exported_at_format`: quarantine vì nếu publish sẽ làm freshness và versioning sai.
- `stale_hr_policy_effective_date`: quarantine để tránh top-k còn bản 2025 khi đang hỏi chính sách 2026.
- `duplicate_chunk_text`: quarantine record đến sau, giữ record đầu tiên để pipeline có thể repeatable.

Không có nhánh "drop không dấu vết" trong reference implementation; mọi record bị loại đều phải còn lại trong `artifacts/quarantine/*.csv` để phục vụ triage.

---

## 4. Phiên bản va canonical

- Refund canonical source: `data/docs/policy_refund_v4.txt`, effective date `2026-02-01`, refund window chuẩn là `7 ngày làm việc`.
- HR leave canonical source: `data/docs/hr_leave_policy.txt`, minimum accepted effective date là `2026-01-01`.
- SLA canonical source: `data/docs/sla_p1_2026.txt`, P1 first response chuẩn là `15 phút`, resolution là `4 giờ`.

Scoring-ready decision:

- Freshness đo tại boundary `publish` thay vì `ingest`, vì Day 09 chỉ nhìn thấy dữ liệu sau khi embed xong.
- Alert channel mặc định: `slack://#day10-data-alerts`.
- Owner team mặc định: `AI Enablement / Helpdesk Knowledge Ops`.
