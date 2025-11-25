// Đổi chỗ điểm đi / điểm đến trong form tìm kiếm
function swapLocations() {
    const fromInput = document.querySelector('input[name="from"]');
    const toInput   = document.querySelector('input[name="to"]');

    if (!fromInput || !toInput) return;

    const tmp = fromInput.value;
    fromInput.value = toInput.value;
    toInput.value = tmp;
}
