document.addEventListener("DOMContentLoaded", () => {

    const checkbox = document.getElementById("agree_checkbox");
    const confirmBtn = document.getElementById("confirm_btn");
    const form = document.getElementById("cancel_form");

    // ✅ THÊM ĐIỀU KIỆN CHECK TỒN TẠI
    if (checkbox && confirmBtn) {
        checkbox.addEventListener("change", () => {
            confirmBtn.disabled = !checkbox.checked;
        });
    }

    if (form) {
        form.addEventListener("submit", (e) => {
            if (!confirm("Bạn chắc chắn muốn hủy vé này?")) {
                e.preventDefault();
            }
        });
    }

});
