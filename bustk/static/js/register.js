document.addEventListener('DOMContentLoaded', function () {

    function closeOTPModal() {
        document.getElementById('otpModal').style.display = 'none';
        document.getElementById('otpInput').value = '';
        hideModalMessages();
    }

    function hideModalMessages() {
        document.getElementById('modalError').style.display = 'none';
        document.getElementById('modalSuccess').style.display = 'none';
    }

    document.getElementById('closeModal').onclick = closeOTPModal;

    document.getElementById('otpModal').onclick = function (e) {
        if (e.target === this) closeOTPModal();
    };

    // ================= GỬI OTP ====================
    document.getElementById('btnSendOTP').onclick = async () => {
        const fullname = document.getElementById('fullname').value.trim();
        const email = document.getElementById('email').value.trim();
        const phone = document.getElementById('phone').value.trim();
        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;

        if (!fullname || !email || !phone || !username || !password) {
            return showError('Vui lòng điền đầy đủ thông tin!');
        }
        if (password.length < 8) {
            return showError('Mật khẩu phải ít nhất 8 ký tự!');
        }
        if (!/^\d{10,11}$/.test(phone)) {
            return showError('Số điện thoại phải có 10–11 chữ số!');
        }

        const btn = document.getElementById('btnSendOTP');
        btn.disabled = true;
        btn.textContent = 'Đang gửi...';

        try {
            const res = await fetch('/send-otp/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({ email, username, phone })
            });

            const data = await res.json();

            if (data.status === 'ok') {
                document.getElementById('otpModal').style.display = 'flex';
                showModalSuccess('OTP đã được gửi! Kiểm tra email.');
            } else {
                showError(data.message || 'Gửi OTP thất bại!');
            }
        } catch (err) {
            showError('Lỗi kết nối. Vui lòng thử lại.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Gửi mã OTP';
        }
    };

    // ================= XÁC NHẬN OTP ====================
    document.getElementById('btnVerifyOTP').onclick = async () => {
        const otp = document.getElementById('otpInput').value.trim();

        if (!otp || otp.length !== 6 || !/^\d+$/.test(otp)) {
            return showModalError('Vui lòng nhập đúng 6 số OTP!');
        }

        const btn = document.getElementById('btnVerifyOTP');
        btn.disabled = true;
        btn.textContent = 'Đang xác nhận...';

        const email = document.getElementById('email').value;
        const fullname = document.getElementById('fullname').value;
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const phone = document.getElementById('phone').value;

        try {
            const res = await fetch('/verify-otp/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                body: new URLSearchParams({
                    email, otp, fullname, username, password, phone
                })
            });

            const data = await res.json();

            if (data.status === 'ok') {
                showModalSuccess('Đăng ký thành công! Đang chuyển...');
                setTimeout(() => {
                    closeOTPModal();
                    window.location.replace('/login/');
                }, 1500);
            } else {
                showModalError(data.message || 'Mã OTP không đúng!');
            }
        } catch (err) {
            showModalError('Lỗi kết nối. Vui lòng thử lại.');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Xác nhận';
        }
    };

    // ================ HÀM THÔNG BÁO ================
    function showError(msg) {
        const e = document.getElementById('errorMsg');
        e.textContent = msg;
        e.style.display = 'block';
        setTimeout(() => e.style.display = 'none', 4000);
    }

    function showSuccess(msg) {
        const s = document.getElementById('successMsg');
        s.textContent = msg;
        s.style.display = 'block';
        setTimeout(() => s.style.display = 'none', 4000);
    }

    function showModalError(msg) {
        const e = document.getElementById('modalError');
        e.textContent = msg;
        e.style.display = 'block';
        setTimeout(() => e.style.display = 'none', 4000);
    }

    function showModalSuccess(msg) {
        const s = document.getElementById('modalSuccess');
        s.textContent = msg;
        s.style.display = 'block';
        setTimeout(() => s.style.display = 'none', 4000);
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie) {
            const cookies = document.cookie.split(';');
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.split('=')[1]);
                }
            }
        }
        return cookieValue;
    }
});
