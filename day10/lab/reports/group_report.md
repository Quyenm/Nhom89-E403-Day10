# Báo Cáo Nhóm - Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Day 10 - Team 6  
**Thành viên:**

| Tên | MSSV | Vai trò (Day 10) | Email |
|-----|------|------------------|-------|
| Dương Trịnh Hoài An | 2A202600050 | Ingestion / Run Owner | anduongtrinhhoai@gmail.com |
| Nguyễn Tiến Đạt | 2A202600217 | Cleaning Rules Owner | nguyendatdtqn@gmail.com |
| Nguyễn Mạnh Quyền | 2A202600481 | Quality / Expectations Owner | anhquyen9a10a@gmail.com |
| Vũ Quang Dũng | 2A202600442 | Embed / Retrieval Eval Owner | vuquangdung71104@gmail.com |
| Trần Ngọc Hùng | 2A202600429 | Grading / Verification Owner | tranngochungb046@gmail.com |
| Bùi Đức Thắng | 2A202600002 | Monitoring / Docs Owner | buiducthang2005@gmail.com |

**Ngày nộp:** 2026-04-15  
**Repo:** `Lecture-Day-08-09-10`

---

## 1. Pipeline tổng quan

Nhóm dùng một entrypoint duy nhất là `python etl_pipeline.py run --run-id ci-smoke`. Lệnh này đọc `data/raw/policy_export_dirty.csv`, chạy clean, expectation suite, rồi publish snapshot sang Chroma collection `day10_kb`. Sau publish, pipeline ghi manifest vào `artifacts/manifests/manifest_ci-smoke.json` và log số record tại `artifacts/logs/run_ci-smoke.log`.

`run_id` là chìa khóa truy vết xuyên suốt. Trong log có `run_id`, `raw_records`, `cleaned_records`, `quarantine_records`. Trong manifest có cùng `run_id`, kèm `latest_exported_at`, `cleaned_csv`, `chroma_collection`. Trong vector metadata cũng có `run_id`, nên khi Day 09 truy vấn sai context thì nhóm có thể lần ngược về đúng pipeline run đã feed index.

Lệnh chạy một dòng:

```bash
python etl_pipeline.py run --run-id ci-smoke
```

---

## 2. Cleaning & expectation

Baseline đã có allowlist, chuẩn hóa `effective_date`, quarantine HR stale version, dedupe, và fix refund 14 ngày về 7 ngày. Nhóm mở rộng thêm ba nhóm rule có tác động đo được:

- Chuẩn hóa `exported_at` về ISO `YYYY-MM-DDTHH:MM:SS`; row timestamp lỗi sẽ vào quarantine thay vì làm freshness sai ngầm.
- Bóc BOM/zero-width khỏi `doc_id` và `chunk_text` để tránh sinh `chunk_id` giả khi source export lẫn ký tự ẩn.
- Xóa migration note `policy-v3` sau khi fix refund stale row để top-k không còn dấu vết bản cũ.

Expectation suite được nâng thêm:

- `exported_at_iso8601` ở mức `halt`
- `required_doc_coverage` ở mức `halt`
- `refund_no_migration_marker` ở mức `warn`

### 2a. Bảng metric_impact

| Rule / Expectation mới | Trước (số liệu) | Sau / khi inject (số liệu) | Chứng cứ |
|------------------------|-----------------|----------------------------|----------|
| Normalize `exported_at` | Timestamp dạng `2026-04-10 08:00:00` chưa dùng ổn cho monitor | Chuẩn hóa thành `2026-04-10T08:00:00` | test `test_clean_rows_normalizes_exported_at...` |
| Remove refund migration note | Refund row còn marker `policy-v3` trong cleaned snapshot cũ | Marker bị loại, top-k sạch hơn | `cleaning_rules.py`, `quality_report.md` |
| `exported_at_iso8601` halt | Corpus có thể publish dù freshness parse lỗi | Corpus bị chặn nếu timestamp không ISO | test `test_expectations_halt...` |
| `required_doc_coverage` halt | Missing doc trọng yếu vẫn có thể lọt qua | Thiếu `sla_p1_2026` hoặc `hr_leave_policy` sẽ halt | test `test_expectations_halt...` |

Ví dụ expectation fail có chủ đích: khi chạy inject với `--no-refund-fix --skip-validate`, rule `refund_no_stale_14d_window` fail nhưng pipeline vẫn tiếp tục để sinh evidence before/after cho Sprint 3.

---

## 3. Before / after ảnh hưởng retrieval hoặc agent

Kịch bản inject của nhóm là bỏ refund fix bằng `--no-refund-fix` và cho phép continue bằng `--skip-validate`. Mục tiêu là tái hiện đúng bài toán Day 10: model không đổi, route Day 09 không đổi, nhưng retrieval vẫn kéo stale context.

Evidence định lượng:

- `artifacts/eval/after_inject_bad.csv` cho `q_refund_window`: `contains_expected=no`, `hits_forbidden=yes`
- `artifacts/eval/before_after_eval.csv` cho `q_refund_window`: `contains_expected=yes`, `hits_forbidden=no`
- `artifacts/eval/grading_run.jsonl` cho `gq_d10_03`: `contains_expected=true`, `hits_forbidden=false`, `top1_doc_matches=true`

Điểm quan trọng là nhóm không chỉ so top-1. `hits_forbidden` quét toàn bộ top-k nên bắt được trường hợp câu trả lời nhìn có vẻ đúng nhưng corpus vẫn còn chunk stale. Đây là đúng tinh thần observability mà slide Day 10 nhấn mạnh: phải nhìn evidence trong retrieval path, không chỉ nhìn final answer.

---

## 4. Freshness & monitoring

Nhóm giữ `sla_hours=24` và đo freshness ở boundary `publish`. Với snapshot mẫu có `latest_exported_at=2026-04-10T08:00:00`, kết quả có thể FAIL nếu chạy sau nhiều ngày. Nhóm coi đây là behavior hợp lệ của dataset demo và ghi rõ trong `docs/runbook.md`: pipeline xanh không đồng nghĩa upstream data còn tươi.

PASS/WARN/FAIL được hiểu như sau:

- PASS: snapshot mới hơn hoặc bằng SLA
- WARN: manifest thiếu timestamp
- FAIL: timestamp có nhưng đã vượt SLA

---

## 5. Liên hệ Day 09

Day 10 feed thẳng vào retrieval layer của Day 09. Khi refund chunk còn `14 ngày làm việc`, supervisor Day 09 vẫn route đúng câu hỏi sang retrieval worker nhưng synthesis worker sẽ trả lời dựa trên context sai. Sau khi clean đúng, không cần đổi prompt hay route logic mà output đã trở về đúng. Điều này chứng minh pipeline dữ liệu là tầng nền của multi-agent quality.

---

## 6. Rủi ro còn lại & việc chưa làm

- Chưa thêm ingest freshness boundary riêng, nên hiện mới đạt chuẩn scoring cơ bản chứ chưa đẩy lên bonus/Distinction.
- Chưa có eval mở rộng trên 5+ câu hoặc LLM judge.
- `chunk_id` hiện phụ thuộc thứ tự cleaned rows; production nên cân nhắc natural key mạnh hơn nếu chunking strategy thay đổi thường xuyên.
