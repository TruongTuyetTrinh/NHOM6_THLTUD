function openReviewModal(ticketId) {
  const modal = document.getElementById("review-modal");
  document.getElementById("review-ticket-id").value = ticketId;
  modal.classList.add("show");
}

function closeReviewModal() {
  const modal = document.getElementById("review-modal");
  modal.classList.remove("show");
}

function submitReview() {
  const ticketId = document.getElementById("review-ticket-id").value;
  const rating   = document.getElementById("review-rating").value;
  const title    = document.getElementById("review-title").value.trim();
  const content  = document.getElementById("review-content").value.trim();
  const imageInp = document.getElementById("review-image");

  if (!title || !content) {
    alert("Vui lòng nhập tiêu đề và nội dung.");
    return;
  }

  const url = `/ticket/${ticketId}/review/`;
  const formData = new FormData();
  formData.append("rating", rating);
  formData.append("title", title);
  formData.append("content", content);
  if (imageInp.files[0]) {
    formData.append("image", imageInp.files[0]);
  }

  formData.append("csrfmiddlewaretoken", getCookie("csrftoken"));

  fetch(url, {
    method: "POST",
    body: formData,
  })
    .then((res) => res.json())
    .then((data) => {
      alert(data.message || "Đã gửi đánh giá.");
      if (data.success) {
        closeReviewModal();
        // reset
        document.getElementById("review-title").value = "";
        document.getElementById("review-content").value = "";
        imageInp.value = "";
      }
    })
    .catch((err) => {
      console.error(err);
      alert("Có lỗi xảy ra, vui lòng thử lại.");
    });
}
