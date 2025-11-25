document.getElementById('loginForm').onsubmit = async (e) => {
    e.preventDefault();

    const formData = new FormData(e.target);
    const errorBox = document.getElementById('errorMsg');
    errorBox.style.display = 'none';

    // LẤY CSRF TOKEN TỪ INPUT ẨN
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
        const res = await fetch('/login/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,     // Gửi CSRF lên đúng chuẩn Django
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await res.json();

        if (data.status === 'success') {
            window.location.href = data.redirect;
        } else {
            errorBox.innerHTML = data.message;
            errorBox.style.display = 'block';
        }
    } catch (err) {
        errorBox.textContent = 'Lỗi kết nối. Vui lòng thử lại.';
        errorBox.style.display = 'block';
    }
};
