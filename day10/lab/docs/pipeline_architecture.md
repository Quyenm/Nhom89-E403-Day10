# Kiến trúc pipeline - Lab Day 10

**Nhóm:** Day 10 Reference Implementation  
**Cập nhật:** 2026-04-15

---

## 1. Sơ đồ luồng

```text
policy_export_dirty.csv
  -> load_raw_csv()
  -> clean_rows()
      -> normalize doc_id / chunk_text
      -> normalize effective_date / exported_at
      -> quarantine unknown, duplicate, stale, malformed rows
      -> fix refund stale window 14d -> 7d
  -> run_expectations()
      -> halt on broken corpus / warn on weaker hygiene issues
  -> Chroma upsert by chunk_id
      -> prune ids missing from cleaned snapshot
  -> manifest.json + freshness_check
  -> retrieval serving for Day 08 / Day 09
```

Điểm đo quan sát:

- `raw_records`, `cleaned_records`, `quarantine_records` được log ngay trong `etl_pipeline.py run`.
- `run_id` đi qua log, manifest và metadata của vector.
- `freshness_check` đo trên mốc `publish`, tức manifest sau khi embed xong.
- `artifacts/quarantine/*.csv` là boundary rõ giữa record bị giữ lại để debug và record được publish.

---

## 2. Ranh giới trách nhiệm

| Thành phần | Input | Output | Trách nhiệm |
|-----------|-------|--------|-------------|
| Ingest | `data/raw/policy_export_dirty.csv` | danh sách row raw | Đọc export, log số record, đóng gói `run_id` |
| Transform | row raw | cleaned rows + quarantine rows | Chuẩn hóa schema, fix stale refund, loại duplicate, cô lập record lỗi |
| Quality | cleaned rows | expectation results + halt/warn | Chặn publish khi corpus thiếu doc trọng yếu hoặc timestamp/schema sai |
| Embed | cleaned CSV | Chroma collection `day10_kb` | Upsert idempotent theo `chunk_id`, prune vector stale |
| Monitor | manifest + cleaned summary | PASS/WARN/FAIL freshness | Kiểm freshness SLA theo boundary publish |

---

## 3. Idempotency va rerun

Pipeline dùng `chunk_id` ổn định dựa trên `doc_id`, `chunk_text`, và thứ tự chunk sau clean. Với cùng cleaned snapshot:

- `col.upsert(ids=ids, ...)` không tạo duplicate vector khi rerun.
- `col.get()` rồi `col.delete(ids=drop)` xóa vector không còn xuất hiện ở cleaned snapshot hiện tại.
- Manifest mới luôn ghi lại `run_id`, `raw_records`, `cleaned_records`, `quarantine_records`, giúp so lại giữa hai lần chạy.

Điều này khớp tiêu chí scoring: rerun phải không phình tài nguyên và không giữ "mồi cũ" trong top-k sau publish.

---

## 4. Liên hệ Day 09

Day 10 không tạo corpus mới tách rời use case mà làm sạch chính knowledge base của Day 08/09:

- `policy_refund_v4` cung cấp câu trả lời chuẩn cho worker retrieval khi hỏi về refund window.
- `sla_p1_2026` và `it_helpdesk_faq` tiếp tục là nguồn cho helpdesk worker.
- `hr_leave_policy` cho thấy nếu versioning sai thì supervisor Day 09 vẫn route đúng nhưng synthesis vẫn trả lời sai vì context stale.

Nói ngắn gọn: Day 09 tối ưu orchestration; Day 10 đảm bảo orchestration đó đọc đúng dữ liệu.

---

## 5. Rủi ro đã biết

- Lần chạy embed đầu tiên có thể cần tải model `all-MiniLM-L6-v2`, nên môi trường offline chỉ verify được code/tests chứ chưa chắc chạy full embedding.
- `chunk_id` hiện dùng `seq` sau clean; nếu chiến lược chunking thay đổi lớn, vector ids sẽ thay đổi theo snapshot mới. Đây là chấp nhận được cho lab nhưng production có thể cần natural key mạnh hơn.
- `freshness_check` đang đo một boundary `publish`; muốn đạt Distinction có thể log thêm boundary `ingest`.
