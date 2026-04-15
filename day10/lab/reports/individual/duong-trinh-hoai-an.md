# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Dương Trịnh Hoài An  
**Vai trò:** Ingestion / Run Owner  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách entrypoint `etl_pipeline.py` ở góc nhìn vận hành run, tức là đảm bảo nhóm có một lệnh chạy được end-to-end và mọi artifact sinh ra đều truy vết được bằng `run_id`. Phần tôi theo dõi trực tiếp gồm log số record, tên file output cleaned/quarantine, manifest JSON, và cách đặt tên cho các run như `final-clean`, `final-pass`, `inject-bad`. Tôi là người gom evidence từ các lần chạy để cả nhóm không bị lẫn giữa run sạch dùng để chấm và run bẩn dùng để demo Sprint 3.

Phần của tôi nối trực tiếp với bạn phụ trách cleaning, expectations và grading. Nếu tôi không chốt đúng `run_id` hoặc không lưu đúng manifest, các bạn còn lại có file eval nhưng không chứng minh được chúng đến từ pipeline run nào.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật chính của tôi là coi `run_id` như khóa truy vết bắt buộc, không phải chỉ là nhãn để dễ nhìn. Trong `etl_pipeline.py`, mỗi lần chạy đều phải log `run_id`, `raw_records`, `cleaned_records`, `quarantine_records`, đường dẫn cleaned CSV, đường dẫn quarantine CSV và manifest. Lý do là Day 10 không chỉ chấm code chạy được mà còn chấm khả năng quan sát hệ thống. Khi retrieval sai, nhóm phải chứng minh được dữ liệu nào đã feed vào index chứ không được nói chung chung.

Tôi cũng giữ hai loại run tách biệt: `final-pass` dùng để chấm và `inject-bad` dùng để chứng minh before/after. Nhờ vậy, nhóm tránh việc dùng nhầm collection hoặc manifest bẩn cho grading JSONL cuối cùng.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly rõ nhất mà tôi gặp là sau khi demo `inject-bad`, collection `day10_kb` có thể vẫn chứa snapshot bẩn nếu nhóm quên chạy lại pipeline sạch. Triệu chứng là `eval_retrieval.py` hoặc `grading_run.py` có thể cho kết quả xấu hơn dù code không đổi. Tôi phát hiện vấn đề này bằng cách so lại `run_id`, manifest và số lượng vector sau từng lần chạy. Khi rerun `final-clean` và `final-pass`, log xuất hiện `embed_prune_removed=1`, chứng tỏ pipeline đã xóa vector stale từ snapshot inject trước đó.

Fix của tôi là chuẩn hóa flow thao tác: luôn chạy run sạch sau run inject, rồi mới tạo eval và grading cuối. Đây là quyết định vận hành quan trọng vì nếu bỏ qua bước này, nhóm rất dễ nộp artifact sai dù code clean vẫn đúng.

---

## 4. Bằng chứng trước / sau

Ở run sạch `final-pass`, `manifest_final-pass.json` ghi `raw=10`, `clean=6`, `quar=4` và `instructor_quick_check.py` xác nhận cả ba `MERIT_CHECK` đều `OK`. Trước đó, ở run `inject-bad`, expectation `refund_no_stale_14d_window` fail và pipeline phải dùng `--skip-validate` để đi tiếp. Khác biệt này cho tôi bằng chứng rõ rằng cùng một corpus nguồn, chỉ cần thay đổi dữ liệu ở bước clean là flow chấm điểm cuối cùng đã đổi trạng thái từ fail có chủ đích sang pass hoàn toàn.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm một script nhỏ để đóng gói toàn bộ flow Day 10 thành một lệnh duy nhất: run sạch, eval, grading và quick check. Như vậy việc demo và nộp bài sẽ ít lỗi thao tác hơn rất nhiều.
