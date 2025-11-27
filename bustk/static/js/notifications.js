// static/js/notifications.js

function switchTab(tabId, buttonEl) {
    // Ẩn tất cả tab content
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(el => el.classList.remove('active'));

    // Hiện tab được chọn
    const target = document.getElementById(tabId);
    if (target) {
        target.classList.add('active');
    }

    // Reset trạng thái nút
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Đánh dấu nút được chọn
    if (buttonEl) {
        buttonEl.classList.add('active');
    }
}

function goToPage(page) {
    // Hiện chỉ dùng cho UI: đổi dot active
    const dots = document.querySelectorAll('.pagination-dot');
    dots.forEach(dot => dot.classList.remove('active'));

    if (dots[page - 1]) {
        dots[page - 1].classList.add('active');
    }

    // Nếu sau này bạn phân trang thật (Django), chỗ này có thể
    // window.location = '?page=' + page;
}

document.addEventListener('DOMContentLoaded', function () {
    // Nếu muốn tab mặc định, đã set bằng class "active" bên template rồi
    // nên ở đây không cần làm gì thêm.
});
