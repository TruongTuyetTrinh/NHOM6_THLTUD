// static/js/messages.js

// Khởi tạo khi DOM đã load xong
document.addEventListener('DOMContentLoaded', function() {
    initializeChat();
});

/**
 * Khởi tạo chức năng chat
 */
function initializeChat() {
    scrollToBottom();
    setupFormSubmit();
    setupDeleteButtons();
    setupTextareaAutoResize();
}

/**
 * Tự động scroll xuống tin nhắn mới nhất
 */
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

/**
 * Xử lý submit form gửi tin nhắn
 */
function setupFormSubmit() {
    const form = document.getElementById('messageForm');
    const textarea = form.querySelector('textarea');
    const sendButton = document.getElementById('sendButton');
    const errorMessage = document.getElementById('errorMessage');

    form.addEventListener('submit', function(e) {
        // Validate trước khi submit
        const content = textarea.value.trim();
        
        if (!content) {
            e.preventDefault();
            showError('Vui lòng nhập nội dung tin nhắn!');
            textarea.focus();
            return false;
        }

        // Disable button để tránh submit nhiều lần
        sendButton.disabled = true;
        sendButton.classList.add('loading');
        
        // Clear error message
        hideError();
    });

    // Clear error khi người dùng bắt đầu gõ
    textarea.addEventListener('input', function() {
        hideError();
    });

    // Cho phép gửi tin nhắn bằng Ctrl/Cmd + Enter
    textarea.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            form.submit();
        }
    });
}

/**
 * Xử lý các nút xóa tin nhắn
 */
function setupDeleteButtons() {
    const deleteForms = document.querySelectorAll('.delete-form');
    
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const confirmation = confirm('Bạn có chắc muốn xóa tin nhắn này?');
            
            if (confirmation) {
                const messageId = this.dataset.messageId;
                deleteMessage(messageId, this);
            }
        });
    });
}

/**
 * Xóa tin nhắn
 */
function deleteMessage(messageId, form) {
    const messageElement = document.querySelector(`.message[data-message-id="${messageId}"]`);
    
    // Thêm hiệu ứng fade out
    if (messageElement) {
        messageElement.style.opacity = '0.5';
        messageElement.style.transform = 'scale(0.95)';
    }

    // Submit form để xóa
    form.submit();
}

/**
 * Tự động điều chỉnh chiều cao textarea
 */
function setupTextareaAutoResize() {
    const textarea = document.querySelector('.message-form textarea');
    
    if (textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
}

/**
 * Hiển thị thông báo lỗi
 */
function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
}

/**
 * Ẩn thông báo lỗi
 */
function hideError() {
    const errorElement = document.getElementById('errorMessage');
    if (errorElement) {
        errorElement.style.display = 'none';
        errorElement.textContent = '';
    }
}

/**
 * Thêm tin nhắn mới vào giao diện (dùng cho AJAX)
 */
function addNewMessage(messageData) {
    const messagesContainer = document.getElementById('messagesContainer');
    const emptyState = messagesContainer.querySelector('.empty-state');
    
    // Xóa empty state nếu có
    if (emptyState) {
        emptyState.remove();
    }
    
    const messageHTML = createMessageHTML(messageData);
    messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
    
    // Scroll xuống tin nhắn mới
    scrollToBottom();
    
    // Setup delete button cho tin nhắn mới
    const newMessage = messagesContainer.lastElementChild;
    const deleteForm = newMessage.querySelector('.delete-form');
    if (deleteForm) {
        setupSingleDeleteButton(deleteForm);
    }
}

/**
 * Tạo HTML cho tin nhắn mới
 */
function createMessageHTML(data) {
    const isUser = data.is_from_user;
    const messageClass = isUser ? 'user' : 'support';
    
    let deleteButtonHTML = '';
    if (isUser) {
        deleteButtonHTML = `
            <form method="post" action="/messages/delete/${data.id}/" class="delete-form" data-message-id="${data.id}">
                <button type="submit" class="btn-delete">
                    <i class="fas fa-trash"></i>
                </button>
            </form>
        `;
    }
    
    return `
        <div class="message ${messageClass}" data-message-id="${data.id}">
            <div class="message-bubble">
                <div class="message-content">${escapeHtml(data.content)}</div>
                <div class="message-info">
                    <span class="message-sender">${escapeHtml(data.sender_name)}</span>
                    <span class="message-time">${data.created_at}</span>
                    ${deleteButtonHTML}
                </div>
            </div>
        </div>
    `;
}

/**
 * Setup delete button cho một form cụ thể
 */
function setupSingleDeleteButton(form) {
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const confirmation = confirm('Bạn có chắc muốn xóa tin nhắn này?');
        
        if (confirmation) {
            const messageId = this.dataset.messageId;
            deleteMessage(messageId, this);
        }
    });
}

/**
 * Escape HTML để tránh XSS
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Gửi tin nhắn qua AJAX (tùy chọn)
 */
function sendMessageAjax(content, csrfToken) {
    const formData = new FormData();
    formData.append('content', content);
    formData.append('csrfmiddlewaretoken', csrfToken);

    return fetch('/messages/send/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            return data.message;
        } else {
            throw new Error(data.error || 'Có lỗi xảy ra');
        }
    });
}

/**
 * Lấy danh sách tin nhắn mới (polling)
 */
function fetchNewMessages() {
    fetch('/messages/get/', {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Xử lý tin nhắn mới nếu cần
            updateMessages(data.messages);
        }
    })
    .catch(error => {
        console.error('Error fetching messages:', error);
    });
}

/**
 * Cập nhật danh sách tin nhắn
 */
function updateMessages(messages) {
    const messagesContainer = document.getElementById('messagesContainer');
    const currentMessageIds = Array.from(
        messagesContainer.querySelectorAll('.message')
    ).map(msg => msg.dataset.messageId);

    messages.forEach(message => {
        if (!currentMessageIds.includes(message.id.toString())) {
            addNewMessage(message);
        }
    });
}

/**
 * Khởi động polling (tùy chọn - để lấy tin nhắn mới từ support)
 */
function startPolling(interval = 5000) {
    setInterval(fetchNewMessages, interval);
}

// Uncomment dòng dưới nếu muốn tự động cập nhật tin nhắn mới
// startPolling();