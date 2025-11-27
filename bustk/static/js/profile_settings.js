// static/js/profile_settings.js
document.addEventListener("DOMContentLoaded", function () {
    const editBtn      = document.getElementById("editToggleBtn");
    const form         = document.getElementById("profileForm");
    const alertBox     = document.getElementById("profileAlert");
    const saveBtn      = document.getElementById("saveProfileBtn");
    const editableEls  = document.querySelectorAll(".js-editable");
    const pwd1Input    = document.getElementById("newPassword1Input");
    const pwd2Input    = document.getElementById("newPassword2Input");

    let isEditing = false;

    function showAlert(message, type = "success") {
        if (!alertBox) return;
        alertBox.textContent = message;
        alertBox.style.display = "block";
        alertBox.className = "profile-alert " + (type === "error" ? "error" : "success");
        setTimeout(() => {
            alertBox.style.display = "none";
        }, 4000);
    }

    function toggleEditing(on) {
        isEditing = on;
        editableEls.forEach(el => {
            el.disabled = !on;
        });
        if (saveBtn) saveBtn.disabled = !on;
        if (editBtn) editBtn.textContent = on ? "Hủy" : "Chỉnh sửa";
    }

    if (editBtn) {
        editBtn.addEventListener("click", function () {
            toggleEditing(!isEditing);
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie("csrftoken");

    if (form) {
        form.addEventListener("submit", async function (e) {
            e.preventDefault();
            if (!isEditing) return;

            // kiểm tra mật khẩu mới
            if (pwd1Input && pwd2Input) {
                const p1 = pwd1Input.value.trim();
                const p2 = pwd2Input.value.trim();
                if (p1 || p2) {
                    if (p1 !== p2) {
                        showAlert("Mật khẩu mới và nhập lại không khớp.", "error");
                        return;
                    }
                }
            }

            const formData = new FormData(form);
            const payload = {};
            formData.forEach((value, key) => {
                payload[key] = value;
            });

            try {
                if (saveBtn) {
                    saveBtn.disabled = true;
                    saveBtn.textContent = "Đang lưu...";
                }

                const resp = await fetch(PROFILE_UPDATE_URL, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": csrftoken,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                const data = await resp.json();

                if (data.status === "success") {
                    showAlert(data.message || "Cập nhật thành công.");

                    if (data.require_relogin) {
                        setTimeout(() => {
                            window.location.href = "/login/";
                        }, 1500);
                    } else {
                        setTimeout(() => {
                            window.location.reload();
                        }, 1000);
                    }
                } else {
                    showAlert(data.message || "Có lỗi xảy ra khi cập nhật.", "error");
                }
            } catch (err) {
                console.error(err);
                showAlert("Lỗi hệ thống. Vui lòng thử lại.", "error");
            } finally {
                if (saveBtn) {
                    saveBtn.disabled = false;
                    saveBtn.textContent = "Lưu thay đổi";
                }
            }
        });
    }
});
