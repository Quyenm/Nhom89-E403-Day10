# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Mạnh Quyền  
**Vai trò:** Quality / Expectations Owner  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách `quality/expectations.py`, tức là lớp quality gate giữa cleaned data và bước embed. Mục tiêu của phần tôi làm là biến các rủi ro dữ liệu thành rule có thể chạy tự động và có semantics rõ: rule nào chỉ cảnh báo, rule nào phải chặn publish. Tôi chịu trách nhiệm các expectation baseline như refund stale window, HR stale annual leave, effective date ISO, đồng thời mở rộng thêm exported_at ISO, required doc coverage và migration marker.

Phần của tôi nằm ngay sau cleaning và ngay trước embedding. Điều đó có nghĩa là nếu tôi đặt rule sai mức độ, collection có thể bị bẩn hoặc pipeline có thể halt không cần thiết. Vì vậy tôi phải cân bằng giữa bảo vệ corpus và giữ flow lab chạy được.

---

## 2. Một quyết định kỹ thuật

Quyết định quan trọng nhất của tôi là phân biệt nghiêm giữa `halt` và `warn`. Tôi đặt `required_doc_coverage` và `exported_at_iso8601` ở mức `halt` vì đây là lỗi có thể làm retrieval và monitor sai ngay ở mức hệ thống. Nếu thiếu `hr_leave_policy` hoặc timestamp không parse được, cho phép publish tiếp là rất nguy hiểm. Ngược lại, tôi giữ `refund_no_migration_marker` ở mức `warn` vì nó phản ánh hygiene issue hơn là lỗi nghiệp vụ cốt lõi, và nhóm vẫn có thể dùng nó như tín hiệu để cải thiện clean.

Tôi chọn cách này để expectation suite thực sự đóng vai trò quality gate chứ không chỉ là checklist cho đẹp.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Lỗi tôi tái hiện rõ nhất là run `inject-bad` với `--no-refund-fix --skip-validate`. Khi đó log trả về `expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1`. Đây là dấu hiệu rằng expectation đang bắt đúng vấn đề stale refund policy. Nếu expectation không fail ở bước này, trước/sau ở Sprint 3 sẽ không còn giá trị vì pipeline sẽ vô tình coi dữ liệu bẩn là hợp lệ.

Sau đó tôi kiểm tra lại run sạch `final-pass` và xác nhận toàn bộ expectation severity `halt` đều pass, bao gồm `required_doc_coverage` và `exported_at_iso8601`. Điều đó chứng minh pipeline sạch không bị chặn oan, còn pipeline inject-bad thì vẫn bị phát hiện đúng.

---

## 4. Bằng chứng trước / sau

Ở `inject-bad`, refund stale rule fail còn migration marker rule cảnh báo fail, trong khi `final-pass` cho toàn bộ expectation halt pass và warning rule cũng pass. Ngoài ra, ở quick check cuối, cả ba `MERIT_CHECK` đều `OK`, cho thấy expectation suite đang hỗ trợ trực tiếp cho grading outcome chứ không phải kiểm tra rời rạc.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ viết thêm một expectation cho consistency giữa `effective_date` và `exported_at`, ví dụ exported timestamp không được sớm hơn effective date một cách bất thường. Rule này giúp bắt các snapshot versioning sai tinh vi hơn.
