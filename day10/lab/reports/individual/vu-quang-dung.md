# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Vũ Quang Dũng  
**Vai trò:** Embed / Retrieval Eval Owner  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách phần embedding snapshot sạch vào Chroma collection `day10_kb` và chạy retrieval evaluation. Các file tôi bám sát nhất là `etl_pipeline.py` ở phần `cmd_embed_internal()`, `eval_retrieval.py`, và các artifact trong `artifacts/eval/`. Nhiệm vụ của tôi là bảo đảm sau khi clean xong, collection được upsert idempotent theo `chunk_id`, đồng thời các vector không còn thuộc cleaned snapshot hiện tại phải bị prune để tránh mồi cũ còn nằm trong top-k.

Phần tôi làm nối thẳng với Sprint 3. Nếu embedding không prune snapshot cũ hoặc eval không quét toàn top-k, nhóm sẽ không chứng minh được before/after một cách đáng tin.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật tôi tập trung nhất là dùng snapshot publish thay vì append mãi vào collection. Trong `cmd_embed_internal()`, collection lấy toàn bộ `prev_ids`, so với `ids` mới và xóa phần thừa trước khi upsert. Điều này rất quan trọng vì sau run `inject-bad`, nếu chỉ upsert chồng lên mà không prune, stale vector vẫn tồn tại và làm `grading_run.py` fail dù cleaned data mới đã đúng.

Ở lớp eval, tôi đồng ý với cách quét `hits_forbidden` trên toàn blob top-k, không chỉ top-1. Đây là điểm sát tinh thần observability nhất của Day 10, vì câu trả lời nhìn đúng chưa chắc nghĩa là corpus sạch.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly chính của tôi là collection `day10_kb` có thể bị nhiễm snapshot xấu sau khi nhóm chạy `inject-bad`. Triệu chứng là `eval_retrieval.py` hoặc `grading_run.py` cho ra kết quả xấu dù code clean không đổi. Tôi xác minh việc này bằng cách theo dõi log `embed_prune_removed`. Ở run sạch sau inject, log ghi `embed_prune_removed=1`, nghĩa là pipeline đã xóa một vector stale khỏi snapshot trước đó.

Sau khi rerun `final-pass`, `eval_retrieval.py` ghi được `final_pass_eval.csv` và `grading_run.py` sinh `final_pass_grading_run.jsonl` với đủ 3 dòng chấm. Điều đó cho thấy collection đã trở lại trạng thái sạch.

---

## 4. Bằng chứng trước / sau

Ở file `artifacts/eval/after_inject_bad.csv`, câu `q_refund_window` có `contains_expected=no` và `hits_forbidden=yes`. Sau khi rerun sạch và ghi `final_pass_eval.csv`, cùng câu hỏi chuyển sang `contains_expected=yes` và `hits_forbidden=no`. Trong `final_pass_grading_run.jsonl`, `gq_d10_03` còn đạt thêm `top1_doc_matches=true`, chứng minh top-1 đã quay về đúng `hr_leave_policy`.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm một script compare hai file eval để tự động highlight dòng nào tốt hơn/xấu hơn giữa clean run và inject run, thay vì nhóm phải đọc CSV thủ công.
