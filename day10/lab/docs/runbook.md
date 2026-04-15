# Runbook - Lab Day 10

---

## Symptom

Agent trả lời theo version cũ hoặc retrieval top-k còn chunk stale, ví dụ trả lời "14 ngày làm việc" thay vì `7 ngày làm việc` cho refund window.

---

## Detection

Các tín hiệu nên xem theo đúng thứ tự Day 10:

1. `freshness_check` trong log hoặc `python etl_pipeline.py freshness --manifest ...`
2. `quarantine_records` tăng bất thường hoặc `cleaned_records` giảm mạnh
3. expectation halt:
   - `refund_no_stale_14d_window`
   - `hr_leave_no_stale_10d_annual`
   - `exported_at_iso8601`
   - `required_doc_coverage`
4. `artifacts/eval/*.csv` có `hits_forbidden=yes` hoặc `top1_doc_expected=no`

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Mở `artifacts/manifests/manifest_<run_id>.json` | Xác định run đang serve, boundary freshness và counts |
| 2 | So `raw_records`, `cleaned_records`, `quarantine_records` với log | Biết lỗi đến từ ingest hay transform |
| 3 | Mở `artifacts/quarantine/quarantine_<run_id>.csv` | Thấy rõ row nào bị loại và vì sao |
| 4 | Xem expectation lines trong `artifacts/logs/run_<run_id>.log` | Biết halt do rule nào |
| 5 | Chạy lại `python eval_retrieval.py --out artifacts/eval/before_after_eval.csv` | Xác nhận top-k đã sạch hay chưa |

Timebox đề xuất:

- 0-5 phút: freshness + manifest
- 5-12 phút: volume/errors + quarantine
- 12-20 phút: schema/versioning + eval
- Quá 20 phút mà chưa rõ root cause: rollback về run sạch gần nhất hoặc treo banner "data stale"

---

## Mitigation

- Nếu expectation halt do stale refund hoặc stale HR version: sửa source export hoặc rerun với dữ liệu sạch, không dùng `--skip-validate`.
- Nếu index còn mồi cũ sau inject: chạy lại `python etl_pipeline.py run` để trigger prune snapshot.
- Nếu freshness FAIL vì snapshot cũ: thống nhất lại SLA đang đo ở `publish`, hoặc cập nhật raw export đúng timestamp nếu đây là run demo.
- Nếu buộc phải demo inject corruption: dùng `--skip-validate` có chủ đích, ghi rõ trong quality report và không dùng run đó để tạo `grading_run.jsonl`.

---

## Prevention

- Giữ `required_doc_coverage` ở mức `halt` để tránh publish corpus thiếu doc chủ chốt.
- Chuẩn hóa `exported_at` về ISO trước khi vào monitor.
- Không commit artifact inject làm artifact grading cuối; phải rerun pipeline sạch trước khi nộp.
- Với bản production, nên thêm ingest freshness boundary và alert riêng cho upstream export job.
