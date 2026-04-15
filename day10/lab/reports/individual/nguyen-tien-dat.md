# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Tiến Đạt  
**Vai trò:** Cleaning Rules Owner  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách `transform/cleaning_rules.py`, tức là nơi chuyển raw export thành cleaned snapshot và quarantine snapshot. Việc của tôi gồm xác định record nào được publish, record nào phải bị cô lập, và cleaned row nào sẽ trở thành nguồn thật để embed vào collection `day10_kb`. Trong bài này, phần tôi làm quan trọng nhất là chuẩn hóa `exported_at`, bóc ký tự ẩn khỏi `doc_id` và `chunk_text`, dọn migration note cũ trong refund policy, và giữ logic dedupe để cùng nội dung không sinh nhiều vector.

Phần của tôi kết nối trực tiếp với expectation suite. Nếu cleaning quá lỏng, expectations sẽ phải gánh lỗi dữ liệu thô. Nếu cleaning quá gắt, cleaned corpus có thể thiếu mất tài liệu cần cho retrieval.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật tôi thấy quan trọng nhất là không drop im lặng bất kỳ row lỗi nào. Mọi row bị loại đều được đưa sang quarantine với lý do rõ ràng như `unknown_doc_id`, `missing_effective_date`, `duplicate_chunk_text`, `stale_hr_policy_effective_date`. Tôi chọn cách này vì Day 10 nhấn mạnh observability. Nếu chỉ để cleaned CSV đẹp mà không giữ bằng chứng rows lỗi, nhóm sẽ không trả lời được vì sao `raw_records=10` nhưng `cleaned_records=6`.

Tôi cũng quyết định xóa migration note `policy-v3` sau khi fix refund stale row. Nếu chỉ thay `14 ngày` thành `7 ngày` mà vẫn để note cũ, top-k có thể còn mang dấu vết version cũ và gây nhiễu khi debug retrieval.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly tôi xử lý là row refund stale ban đầu vừa chứa nội dung `14 ngày làm việc`, vừa kèm chú thích migration từ `policy-v3`. Nếu để nguyên row này, expectation về refund sẽ fail và retrieval có thể kéo chunk stale vào top-k. Tôi phát hiện lỗi khi đọc raw CSV và đối chiếu với cleaned snapshot cũ: row refund được sửa số ngày nhưng note cũ vẫn còn.

Fix của tôi là bổ sung bước `_clean_chunk_text()` trong `cleaning_rules.py`. Hàm này chuẩn hóa text, thay `14 ngày làm việc` thành `7 ngày làm việc`, rồi xóa phần note migration trước khi tạo `chunk_id`. Sau fix, cleaned snapshot sạch hơn và expectation `refund_no_migration_marker` chuyển về pass ở run chuẩn.

---

## 4. Bằng chứng trước / sau

Trước khi clean đúng, kịch bản `inject-bad` cho thấy `expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1` và `refund_no_migration_marker FAIL (warn) :: violations=1`. Sau khi chạy `final-pass`, log chuyển thành `refund_no_stale_14d_window OK` và `refund_no_migration_marker OK`. Đồng thời cleaned snapshot `cleaned_final-pass.csv` chỉ còn refund text đã được sửa sạch, không còn note migration cũ.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm vài test dữ liệu bẩn có BOM hoặc zero-width thật trong raw CSV riêng để chứng minh tác động của rule hidden-character rõ hơn, thay vì chỉ mô tả trong metric impact.
