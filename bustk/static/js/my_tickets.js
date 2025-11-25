// static/js/my_tickets.js

document.addEventListener('DOMContentLoaded', function () {

    // ================== HÀM LẤY CSRF TOKEN ==================
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // ========================================================
    // 1. HỦY VÉ (TAB SẮP ĐI)
    // ========================================================
    const cancelButtons = document.querySelectorAll('.js-cancel-ticket');

    cancelButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const ticketId   = this.dataset.ticketId;
            const cancelUrl  = this.dataset.cancelUrl;

            if (!cancelUrl) {
                alert('Không tìm thấy URL hủy vé.');
                return;
            }

            const confirmText = `
Bạn có chắc chắn muốn hủy vé #${ticketId} không?

- Hủy trước 24 giờ: hoàn 100% giá vé
- Hủy trước 12 giờ: hoàn 50% giá vé
- Sau 12 giờ trước giờ xuất bến: không hoàn tiền

Tiền hoàn (nếu có) sẽ được xử lý trong 3-5 ngày làm việc.
            `.trim();

            if (!confirm(confirmText)) {
                return;
            }

            fetch(cancelUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    reason: 'user_cancel',
                }),
            })
            .then(function (response) {
                return response.json();
            })
            .then(function (data) {
                if (data.success) {
                    let msg = data.message || 'Hủy vé thành công.';

                    if (data.refund_percent !== undefined) {
                        msg += `\nHoàn tiền: ${data.refund_percent}%`;
                    }
                    if (data.refund_amount !== undefined) {
                        msg += ` (${data.refund_amount.toLocaleString('vi-VN')}đ)`;
                    }

                    alert(msg);
                    // Reload lại để cập nhật tab
                    window.location.reload();
                } else {
                    alert(data.message || 'Không thể hủy vé. Vui lòng thử lại sau.');
                }
            })
            .catch(function (err) {
                console.error(err);
                alert('Có lỗi xảy ra khi hủy vé. Vui lòng thử lại sau.');
            });
        });
    });

    // ========================================================
    // 2. HIỂN THỊ QR VÉ (TAB SẮP ĐI & ĐÃ ĐI NẾU CẦN)
    // ========================================================
    const qrModal      = document.getElementById('ticket-qr-modal');
    const qrImg        = document.getElementById('ticket-qr-image');
    const qrCodeSpan   = document.getElementById('ticket-qr-code');
    const qrCloseBtns  = document.querySelectorAll('.js-close-qr-modal');
    const qrButtons    = document.querySelectorAll('.js-show-ticket-qr');

    function openQrModal(ticketCode) {
        if (!qrModal || !qrImg || !qrCodeSpan) return;

        // QR check-in: chỉ encode ticket_code, KHÔNG liên quan thanh toán nữa
        const qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=220x220&data='
            + encodeURIComponent(ticketCode);

        qrImg.src = qrUrl;
        qrCodeSpan.textContent = ticketCode;
        qrModal.classList.add('active');
    }

    function closeQrModal() {
        if (!qrModal) return;
        qrModal.classList.remove('active');
    }

    qrButtons.forEach(function (btn) {
        btn.addEventListener('click', function () {
            const code = this.dataset.ticketCode;
            if (!code) {
                alert('Không tìm thấy mã vé để tạo QR.');
                return;
            }
            openQrModal(code);
        });
    });

    qrCloseBtns.forEach(function (btn) {
        btn.addEventListener('click', function () {
            closeQrModal();
        });
    });

    if (qrModal) {
        // click ra ngoài để đóng
        qrModal.addEventListener('click', function (e) {
            if (e.target === qrModal) {
                closeQrModal();
            }
        });
    }

    // ========================================================
    // 3. (OPTIONAL) TÔ MÀU TAB THEO URL – đã xử lý bằng template
    // ========================================================
    // bạn đã dùng current_tab trong template nên JS không cần làm thêm
});
