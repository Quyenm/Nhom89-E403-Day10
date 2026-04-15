# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Bùi Đức Thắng  
**Vai trò:** Monitoring / Docs Owner  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách monitoring và phần tài liệu bắt buộc của Day 10. File tôi bám chính là `monitoring/freshness_check.py`, `contracts/data_contract.yaml`, `docs/pipeline_architecture.md`, `docs/data_contract.md`, `docs/runbook.md`, `docs/quality_report.md`, cùng `reports/group_report.md`. Tôi là người chuyển các quyết định kỹ thuật của nhóm thành tài liệu có thể đọc, có source map, có giải thích PASS/WARN/FAIL, và có liên hệ rõ với Day 09.

Phần của tôi là chỗ giảng viên hoặc người review nhìn vào để hiểu nhóm làm gì và vì sao làm vậy. Nếu code chạy được nhưng docs không khớp behavior, Day 10 vẫn bị mất điểm ở mục documentation.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật tôi phải giải thích rõ nhất là boundary của freshness. Nhóm chọn đo ở `publish`, tức là thời điểm snapshot đã sẵn sàng cho retrieval, thay vì chỉ đo khi ingest bắt đầu. Tôi ghi rõ điều này trong `data_contract.yaml`, `data_contract.md` và `runbook.md` vì nếu không chốt boundary, cùng một dataset có thể bị diễn giải khác nhau giữa các thành viên.

Tôi cũng ghi rõ rằng dataset mẫu có thể `FAIL` freshness theo SLA 24 giờ dù pipeline vẫn `PIPELINE_OK`. Đây là điểm quan trọng về observability: monitor có thể phát hiện dữ liệu stale trong khi code kỹ thuật vẫn chạy đúng.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly tôi xử lý là việc mọi người dễ hiểu nhầm `freshness_check=FAIL` là pipeline bị hỏng. Khi chạy `final-clean`, output báo `freshness_sla_exceeded` vì `latest_exported_at` của dữ liệu mẫu đã cũ hơn 24 giờ. Nếu không giải thích rõ trong runbook, nhóm rất dễ kết luận sai rằng code freshness bị lỗi.

Tôi xử lý bằng cách viết rõ trong `runbook.md` và `quality_report.md` rằng đây là fail nghiệp vụ của snapshot theo SLA, không phải fail kỹ thuật. Sau đó nhóm còn thử nới `FRESHNESS_SLA_HOURS=200` để chứng minh monitor chuyển sang `PASS` khi policy SLA thay đổi. Nhờ vậy, chúng tôi phân biệt được lỗi dữ liệu với lỗi hệ thống.

---

## 4. Bằng chứng trước / sau

Trước khi nới SLA, lệnh `python day10/lab/etl_pipeline.py freshness --manifest ...manifest_final-clean.json` trả về `FAIL` cùng lý do `freshness_sla_exceeded`. Sau khi đặt `FRESHNESS_SLA_HOURS=200` và chạy `final-pass`, cùng logic monitor trả về:

`PASS {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 120.81, "sla_hours": 200.0}`

Bằng chứng này cho thấy monitoring đang hoạt động đúng theo contract, không phải trả kết quả ngẫu nhiên.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ mở rộng monitor để log cả hai boundary `ingest` và `publish` trong manifest. Đây là cải tiến có giá trị nhất để đẩy Day 10 lên mức Distinction mà vẫn bám đúng use case hiện tại.
