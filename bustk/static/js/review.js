// Gói trong IIFE để tránh rác global, nhưng gán hàm lên window
(function () {
    function getCsrfToken() {
        const form = document.getElementById("review-form");
        if (!form) return "";
        const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        return input ? input.value : "";
    }

    // ----- MỞ MODAL -----
    function openReviewModal(ticketId, submitUrl) {
        const modal = document.getElementById("review-modal");
        const form = document.getElementById("review-form");

        if (!modal || !form) {
            console.error("Không tìm thấy review-modal hoặc review-form");
            return;
        }

        // set hidden values
        const ticketInput = document.getElementById("review-ticket-id");
        const submitUrlInput = document.getElementById("review-submit-url");

        if (ticketInput) ticketInput.value = ticketId;
        if (submitUrlInput) submitUrlInput.value = submitUrl;

        // reset form
        form.reset();

        // mặc định 5 sao
        const star5 = document.getElementById("star-5");
        if (star5) {
            star5.checked = true;
        }

        modal.classList.add("show");
    }

    // ----- ĐÓNG MODAL -----
    function closeReviewModal() {
        const modal = document.getElementById("review-modal");
        if (modal) {
            modal.classList.remove("show");
        }
    }

    // ----- GỬI ĐÁNH GIÁ -----
   function submitReview() {
    const ticketId = document.getElementById("review-ticket-id").value;
    if (!ticketId) {
        alert("Không xác định được vé để đánh giá.");
        return;
    }

    const ratingInput = document.querySelector('input[name="rating"]:checked');
    const rating = ratingInput ? ratingInput.value : "";
    const title = document.getElementById("review-title").value;
    const content = document.getElementById("review-content").value;
    const imageInput = document.getElementById("review-image");

    if (!rating) {
        alert("Vui lòng chọn số sao đánh giá.");
        return;
    }

    const fd = new FormData();
    fd.append("rating", rating);
    fd.append("title", title);
    fd.append("content", content);
    if (imageInput.files.length > 0) {
        fd.append("image", imageInput.files[0]);
    }

    const submitUrl = `/ticket/${ticketId}/review/`;

    fetch(submitUrl, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: fd,
    })
        .then(res => res.json().then(data => ({ ok: res.ok, data })))
        .then(({ ok, data }) => {
            if (!ok) {
                alert(data.message || "Có lỗi khi gửi đánh giá.");
                return;
            }
            if (data.status === "success" && data.redirect_url) {
                window.location.href = data.redirect_url;
            } else {
                alert(data.message || "Có lỗi khi gửi đánh giá.");
            }
        })
        .catch(err => {
            console.error(err);
            alert("Không gửi được đánh giá, vui lòng thử lại.");
        });
}
function getCsrfToken() {
    const name = "csrftoken=";
    const cookies = document.cookie.split(";");
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name)) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}


    // ĐƯA HÀM RA GLOBAL ĐỂ onclick="" GỌI ĐƯỢC
    window.openReviewModal = openReviewModal;
    window.closeReviewModal = closeReviewModal;
    window.submitReview = submitReview;
})();
