# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trần Ngọc Hùng  
**Vai trò:** Grading / Verification Owner  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách lớp kiểm chứng cuối cùng của Day 10, gồm `grading_run.py`, `instructor_quick_check.py`, và toàn bộ artifact JSONL dùng để đối chiếu với rubric chấm bài. Vai trò của tôi là bảo đảm nhóm không chỉ chạy được pipeline mà còn sinh đúng output mà giảng viên hoặc script check mong đợi. Tôi kiểm tra số dòng grading, tên các câu `gq_d10_01` đến `gq_d10_03`, và xác nhận các điều kiện merit như `contains_expected`, `hits_forbidden`, `top1_doc_matches`.

Phần của tôi là chốt cuối trước khi nộp. Nếu grading JSONL sai format hoặc quick check không khớp manifest, cả flow phía trước làm đúng vẫn có thể mất điểm.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật tôi thấy quan trọng nhất là không tin cảm giác “eval nhìn ổn” mà phải có thêm lớp quick check tự động. `grading_run.py` sinh JSONL theo đúng schema chấm, còn `instructor_quick_check.py` giúp phát hiện ngay trường hợp thiếu câu, sai khóa, hoặc top-1 của `gq_d10_03` không về đúng tài liệu HR. Tôi cũng sửa logic nhận diện merit fail để script không bỏ sót trường hợp `MERIT_CHECK[...] FAIL`.

Với Day 10, tôi coi quick check như một version tối giản của CI dành cho artifact. Nó biến kết luận “nhìn có vẻ đúng” thành kết luận có log và rule rõ ràng.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Lỗi tôi tập trung xử lý là bug ở phần quick check: script cũ có thể không đánh dấu merit fail đúng cách nếu câu `MERIT_CHECK[...] FAIL :: ...` xuất hiện nhưng pattern kiểm tra không khớp chính xác. Điều này nguy hiểm vì nhóm có thể tin rằng grading ổn trong khi một điều kiện merit quan trọng thực ra đã fail.

Sau khi sửa, tôi dùng test `test_check_grading_jsonl_fails_on_merit_regression()` để tái hiện case `gq_d10_01` fail có chủ đích. Test xác nhận script trả về code lỗi đúng như mong đợi. Khi chạy với artifact thật `final_pass_grading_run.jsonl`, cả ba merit check đều `OK`, nên tôi có đủ cơ sở để chốt artifact cuối.

---

## 4. Bằng chứng trước / sau

Bằng chứng mạnh nhất là output cuối cùng:

- `MERIT_CHECK[gq_d10_01] OK`
- `MERIT_CHECK[gq_d10_02] OK`
- `MERIT_CHECK[gq_d10_03] OK`
- `OK manifest run_id=final-pass raw=10 clean=6 quar=4`

Ngoài ra, `final_pass_grading_run.jsonl` có đúng 3 dòng và mỗi dòng đều chứa các trường cần cho chấm điểm, đặc biệt `gq_d10_03` có `top1_doc_matches=true`.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm một script tổng hợp duy nhất chạy grading và quick check một lần, rồi in ra status Pass/Merit rõ ràng để nhóm không phải ghép nhiều lệnh thủ công.
