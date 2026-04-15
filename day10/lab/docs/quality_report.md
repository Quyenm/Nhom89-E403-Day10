# Quality report - Lab Day 10

**run_id:** `ci-smoke`  
**Ngày:** 2026-04-14

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước inject | Sau clean (`ci-smoke`) | Ghi chú |
|--------|--------------|------------------------|---------|
| `raw_records` | 10 | 10 | Cùng một raw export |
| `cleaned_records` | 6 | 6 | Sau clean giữ lại corpus phục vụ retrieval |
| `quarantine_records` | 4 | 4 | Duplicate, missing date, stale HR 2025, unknown doc_id |
| Expectation halt? | Có khi inject stale refund + skip validate | Không | Run chuẩn yêu cầu refund window sạch và đủ coverage |

---

## 2. Before / after retrieval

Artifact tham chiếu:

- `artifacts/eval/after_inject_bad.csv`
- `artifacts/eval/before_after_eval.csv`
- `artifacts/eval/grading_run.jsonl`

**Câu hỏi then chốt:** refund window (`q_refund_window`)

**Trước inject-bad:** `contains_expected=no`, `hits_forbidden=yes`, `top1_doc_id=policy_refund_v4`  
**Sau ci-smoke:** `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_id=policy_refund_v4`

**Merit:** versioning HR - `q_leave_version`

**Trước inject-bad:** top-k còn `10 ngày phép năm`, `top1_doc_expected=no`  
**Sau ci-smoke:** `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`

Interpretation:

- Refund question chứng minh stale chunk không chỉ làm answer sai mà còn làm top-k mang forbidden evidence.
- HR question chứng minh versioning là vấn đề retrieval/data, không phải prompt. Khi quarantine bản `2025-01-01`, top-1 quay lại đúng `hr_leave_policy`.

---

## 3. Freshness & monitor

Run `ci-smoke` có `latest_exported_at=2026-04-10T08:00:00`. Với `sla_hours=24`, snapshot mẫu sẽ `FAIL` nếu đo theo thời điểm chấm sau nhiều ngày. Điều này được giữ nguyên có chủ đích để dạy rõ sự khác nhau giữa:

- freshness của snapshot upstream
- freshness của pipeline run

Reference implementation chọn đo ở boundary `publish`, rồi giải thích trong runbook rằng demo dataset có thể FAIL hợp lệ vì bản export cố ý cũ.

---

## 4. Corruption inject (Sprint 3)

Kịch bản inject reference:

- chạy `python etl_pipeline.py run --run-id inject-bad --no-refund-fix --skip-validate`
- refund stale row vẫn giữ `14 ngày làm việc`
- top-k trả về forbidden chunk ở câu `q_refund_window`
- HR stale row làm `q_leave_version` có nguy cơ top-1 lệch hoặc chứa `10 ngày phép năm`

Detection path:

1. expectation `refund_no_stale_14d_window` fail
2. CSV eval xuất hiện `hits_forbidden=yes`
3. grading JSONL fail `gq_d10_01` hoặc `gq_d10_03`

---

## 5. Hạn chế & việc chưa làm

- Chưa log thêm freshness boundary `ingest`; đây là hướng Distinction rõ nhất nếu cần mở rộng.
- Chưa chạy LLM-judge; toàn bộ evidence hiện dùng retrieval + keyword để giữ chi phí thấp và dễ chấm.
