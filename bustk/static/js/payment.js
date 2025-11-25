// static/js/payment.js

document.addEventListener("DOMContentLoaded", function () {
  const cfg = document.getElementById("payment-config");
  if (!cfg) return;

  const expiresAt    = new Date(cfg.dataset.expiresAt);
  const statusUrl    = cfg.dataset.statusUrl;
  const myTicketsUrl = cfg.dataset.myTicketsUrl;

  const countdownEl = document.getElementById("countdown");
  const statusBox   = document.getElementById("status-box");
  const overlay     = document.getElementById("qr-expired-overlay");

  const successModal   = document.getElementById("payment-success-modal");
  const viewBtn        = document.getElementById("payment-success-view-btn");
  const closeBtn       = document.getElementById("payment-success-close-btn");

  let countdownTimer       = null;
  let pollingTimer         = null;
  let expiredRedirectTimer = null;

  // ====== HẾT HẠN: CHE QR + TỰ QUAY LẠI ======
  function showExpiredOverlay() {
    if (overlay) {
      overlay.style.display = "flex";
    }
    if (statusBox) {
      statusBox.textContent = "Mã QR đã hết hiệu lực. Vui lòng quay lại trang đặt vé.";
      statusBox.className   = "status-box status-expired";
    }

    // Sau 30s tự quay lại trang trước
    expiredRedirectTimer = setTimeout(function () {
      if (document.referrer) {
        window.history.back();
      } else {
        window.location.href = "/";
      }
    }, 30000);
  }

  // ====== ĐẾM NGƯỢC 5 PHÚT ======
  function updateCountdown() {
    const now  = new Date();
    let diff   = Math.floor((expiresAt - now) / 1000); // giây

    if (diff <= 0) {
      if (countdownEl) countdownEl.textContent = "00:00";

      clearInterval(countdownTimer);
      clearInterval(pollingTimer);
      showExpiredOverlay();
      return false;
    }

    const m = String(Math.floor(diff / 60)).padStart(2, "0");
    const s = String(diff % 60).padStart(2, "0");
    if (countdownEl) countdownEl.textContent = m + ":" + s;
    return true;
  }

  // ====== HIỂN THỊ POPUP THÀNH CÔNG ======
  function showSuccess() {
    clearInterval(countdownTimer);
    clearInterval(pollingTimer);
    if (expiredRedirectTimer) clearTimeout(expiredRedirectTimer);

    if (overlay) overlay.style.display = "none";

    if (statusBox) {
      statusBox.textContent = "Thanh toán thành công! Bạn đã đặt vé thành công.";
      statusBox.className   = "status-box status-success";
    }

    if (successModal) {
      successModal.style.display = "flex"; // Che cả màn hình, popup giữa
    } else if (myTicketsUrl) {
      window.location.href = myTicketsUrl;
    }
  }

  // ====== POLLING TRẠNG THÁI TỪ SERVER ======
  function checkStatus() {
    fetch(statusUrl)
      .then((resp) => resp.json())
      .then((data) => {
        if (!data || !data.status) return;

        if (data.status === "paid") {
          showSuccess();
        } else if (data.status === "expired") {
          clearInterval(pollingTimer);
          clearInterval(countdownTimer);
          showExpiredOverlay();
        }
      })
      .catch((err) => {
        console.error("Lỗi check trạng thái thanh toán:", err);
      });
  }

  // ====== EVENT NÚT POPUP ======
  if (viewBtn && myTicketsUrl) {
    viewBtn.addEventListener("click", function () {
      window.location.href = myTicketsUrl;
    });
  }

  if (closeBtn && successModal) {
    closeBtn.addEventListener("click", function () {
      successModal.style.display = "none";
    });
  }

  // ====== KHỞI ĐỘNG ======
  updateCountdown();                           // cập nhật lần đầu
  countdownTimer = setInterval(updateCountdown, 1000); // mỗi 1s

  checkStatus();                               // check ngay 1 lần
  pollingTimer = setInterval(checkStatus, 5000);       // rồi 5s/lần
});
