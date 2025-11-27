// static/js/messages.js

document.addEventListener('DOMContentLoaded', function() {
    initializeChat();

    // Bấm icon ảnh thì mở hộp chọn file
    const imageBtn = document.getElementById('imageButton');
    const imageInput = document.getElementById('id_image');

    if (imageBtn && imageInput) {
        imageBtn.addEventListener('click', function(e) {
            e.preventDefault();
            imageInput.click();
        });
    }
});


/**
 * Khởi tạo toàn bộ chức năng ở trang chat
 */
function initChatPage() {
    setupChatList();        // highlight item bên trái
    setupSendArea();        // gửi tin nhắn
    autoScrollMessages();   // cuộn xuống cuối
    // Nếu muốn auto cập nhật tin nhắn mới từ server thì bật:
    // startPolling();
}

/* ==========================
 * 1. LIST CHAT BÊN TRÁI
 * ========================== */

function setupChatList() {
    const chatItems = document.querySelectorAll('.chat-item');
    if (!chatItems.length) return;

    chatItems.forEach(item => {
        item.addEventListener('click', () => {
            chatItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Sau này nếu bạn có nhiều phòng chat
            // thì có thể dùng item.dataset.conversationId
            // để load đúng lịch sử phòng đó qua AJAX
        });
    });
}

/* ==========================
 * 2. GỬI TIN NHẮN
 * ========================== */

function setupSendArea() {
    const input      = document.querySelector('.chat-input');
    const sendBtn    = document.querySelector('.send-btn');
    const imageInput = document.getElementById('chatImage'); // có thì dùng, không có thôi

    if (!input || !sendBtn) return;

    // Click nút gửi
    sendBtn.addEventListener('click', function (e) {
        e.preventDefault();
        handleSendMessage(input, imageInput, sendBtn);
    });

    // Enter để gửi, Shift+Enter để xuống dòng
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(input, imageInput, sendBtn);
        }
    });
}

/**
 * Xử lý gửi tin nhắn (text + optional image)
 */
function handleSendMessage(input, imageInput, sendBtn) {
    const content = (input.value || '').trim();
    const file    = imageInput && imageInput.files ? imageInput.files[0] : null;

    if (!content && !file) {
        alert('Vui lòng nhập tin nhắn hoặc chọn ảnh.');
        input.focus();
        return;
    }

    // Chuẩn bị dữ liệu gửi tới view send_message
    const formData = new FormData();
    formData.append('content', content);
    if (file) {
        formData.append('image', file);
    }

    sendBtn.disabled = true;

    fetch('/messages/send/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.message) {
                appendMessageToUI(data.message);
                input.value = '';
                if (imageInput) {
                    imageInput.value = '';
                }
                autoScrollMessages();
            } else {
                alert(data.error || 'Không gửi được tin nhắn, vui lòng thử lại.');
            }
        })
        .catch(err => {
            console.error(err);
            alert('Không gửi được tin nhắn, vui lòng thử lại.');
        })
        .finally(() => {
            sendBtn.disabled = false;
        });
}

/* ==========================
 * 3. HIỂN THỊ / CẬP NHẬT TIN NHẮN
 * ========================== */

/**
 * Tự động cuộn xuống cuối khung messages
 */
function autoScrollMessages() {
    const container =
        document.getElementById('messagesContainer') ||
        document.querySelector('.messages');

    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

/**
 * Thêm 1 tin nhắn mới vào UI (sau khi gửi xong hoặc lấy từ AJAX)
 * Cấu trúc HTML khớp với template chat của bạn
 */
function appendMessageToUI(message) {
    const container =
        document.getElementById('messagesContainer') ||
        document.querySelector('.messages');
    if (!container) return;

    const isUser = message.is_from_user;
    const text   = escapeHtml(message.content || '');
    const time   = message.created_at || '';
    const sender = message.sender_name || '';

    // Lấy chữ cái đầu làm avatar
    const avatarText = sender ? sender.charAt(0).toUpperCase() : 'Me';

    let html = '';

    if (isUser) {
        // Tin nhắn của chính user (bên phải)
        html = `
        <div class="message own" data-message-id="${message.id}">
            <div class="message-content">
                <p class="message-text">${text}</p>
                ${message.image_url ? `<p class="mt-1"><img src="${message.image_url}" alt="Ảnh" style="max-width: 180px; border-radius: 6px;"></p>` : ''}
                <p class="message-time">${time}</p>
            </div>
            <div class="message-avatar">${avatarText}</div>
        </div>`;
    } else {
        // Tin nhắn từ hệ thống / support (bên trái)
        html = `
        <div class="message" data-message-id="${message.id}">
            <div class="message-avatar">${avatarText}</div>
            <div class="message-content">
                <p class="message-text">${text}</p>
                ${message.image_url ? `<p class="mt-1"><img src="${message.image_url}" alt="Ảnh" style="max-width: 180px; border-radius: 6px;"></p>` : ''}
                <p class="message-time">${time}</p>
            </div>
        </div>`;
    }

    container.insertAdjacentHTML('beforeend', html);
}

/**
 * Escape HTML để chống XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function (m) {
        return map[m];
    });
}

/* ==========================
 * 4. CSRF & POLLING (TÙY CHỌN)
 * ========================== */

/**
 * Lấy CSRF token từ cookie (chuẩn Django)
 */
function getCsrfToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie || '');
    const parts = decodedCookie.split(';');
    for (let i = 0; i < parts.length; i++) {
        let c = parts[i].trim();
        if (c.indexOf(name) === 0) {
            return c.substring(name.length, c.length);
        }
    }
    return '';
}

/**
 * Lấy danh sách tin nhắn mới từ server (dùng cho polling)
 */
function fetchNewMessages() {
    return fetch('/messages/get/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
        .then(response => response.json())
        .then(data => {
            if (!data.success || !Array.isArray(data.messages)) return;

            const container =
                document.getElementById('messagesContainer') ||
                document.querySelector('.messages');
            if (!container) return;

            const currentIds = Array.from(
                container.querySelectorAll('.message')
            ).map(el => el.dataset.messageId);

            data.messages.forEach(msg => {
                if (!currentIds.includes(String(msg.id))) {
                    appendMessageToUI(msg);
                }
            });

            autoScrollMessages();
        })
        .catch(err => {
            console.error('Error fetch messages:', err);
        });
}

/**
 * Bật polling để tự động cập nhật tin nhắn mới
 * (tùy chọn – nếu chưa cần thì đừng gọi hàm này)
 */
function startPolling(interval = 5000) {
    setInterval(fetchNewMessages, interval);
}

/* ==========================
 * 5. XÓA TIN NHẮN (NẾU DÙNG)
 * ========================== */

/**
 * Gọi khi bạn có nút xóa (delete) trên từng message.
 * Ví dụ: <button onclick="deleteMessage(123)">...</button>
 */
function deleteMessage(messageId) {
    if (!confirm('Bạn có chắc muốn xóa tin nhắn này?')) return;

    fetch(`/messages/delete/${messageId}/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': getCsrfToken()
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const el = document.querySelector(`.message[data-message-id="${messageId}"]`);
                if (el) el.remove();
            } else {
                alert(data.error || 'Không xóa được tin nhắn.');
            }
        })
        .catch(err => {
            console.error(err);
            alert('Không xóa được tin nhắn.');
        });
}
