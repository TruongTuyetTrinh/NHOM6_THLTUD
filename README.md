DaNaGO là hệ thống đặt vé xe bus trực tuyến hiện đại, được xây dựng trên framework Django. Dự án tập trung vào việc tự động hóa quy trình từ tìm kiếm, đặt vé, xác nhận thanh toán (thông qua Webhook) đến quản lý vòng đời vé (hủy, đánh giá) một cách minh bạch và hiệu quả.


I. Quản Lý Tài Khoản và Bảo Mật
Đăng ký & Đăng nhập: Người dùng có thể tạo tài khoản và đăng nhập vào hệ thống.
Xác thực OTP: Thực hiện xác minh qua Mã OTP gửi qua Email trong quá trình đăng ký.
Quản lý Hồ sơ: Cập nhật thông tin cá nhân (Họ tên, SĐT, Ngày sinh, Giới tính, Địa chỉ) và đổi mật khẩu.
II. Tìm Kiếm và Đặt Vé
Tìm kiếm Chuyến đi: Dễ dàng tìm kiếm các chuyến xe theo tuyến đường (Điểm đi, Điểm đến) và ngày khởi hành mong muốn.
Chọn ghế: Xem sơ đồ ghế, chọn các ghế còn trống cho chuyến đi.
Thanh toán: Thực hiện thanh toán qua quét Mã QR code và nhận xác nhận thanh toán tự động ngay sau khi giao dịch thành công.
III. Quản Lý Vé và Hậu mãi
Xem vé: Theo dõi các vé đã đặt theo ba trạng thái:
  Sắp đi (upcoming): Vé chưa tới giờ khởi hành.
  Đã đi (completed): Vé đã qua giờ khởi hành (cập nhật tự động).
  Đã hủy (cancelled): Vé đã bị hủy.
Hủy vé: Hủy vé sắp đi và nhận thông báo về phí hủy và số tiền được hoàn lại dựa trên chính sách thời gian.
Tải vé: Tải file PDF của vé (có Mã QR check-in) về thiết bị.
Đặt lại vé (Rebook): Dùng thông tin chuyến đi cũ để tìm kiếm và đặt vé mới nhanh chóng.
Đánh giá: Gửi đánh giá (rating) và phản hồi cho các chuyến đi đã hoàn thành (completed).
Xem đánh giá tuyến: Xem các đánh giá của người dùng khác cho cùng một tuyến đường.
IV. Thông báo và Hỗ trợ
Nhận Thông báo: Nhận các thông báo quan trọng về vé, xác nhận đặt/hủy thành công.
Nhắn tin Hỗ trợ: Gửi tin nhắn và hình ảnh tới bộ phận hỗ trợ khách hàng.
