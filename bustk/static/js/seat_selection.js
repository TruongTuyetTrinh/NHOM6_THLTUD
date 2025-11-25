// seat_selection.js

document.addEventListener("DOMContentLoaded", () => {
  // ====== LẤY CẤU HÌNH TỪ HTML ======
  const configEl = document.getElementById("seat-config");
  if (!configEl) {
    console.error("Không tìm thấy #seat-config");
    return;
  }

  const IMG_SOLD      = configEl.dataset.imgSold;
  const IMG_AVAILABLE = configEl.dataset.imgAvailable;
  const IMG_SELECTED  = configEl.dataset.imgSelected;
  const INDEX_URL     = configEl.dataset.indexUrl;
  const PAYMENT_URL   = configEl.dataset.paymentUrl;

  // ====== ĐỌC PARAM TRÊN URL ======
  const urlParams     = new URLSearchParams(window.location.search);

  // KHÔNG dùng default Đà Nẵng – Đà Lạt nữa
  const fromLocation  = urlParams.get("from")  || "";
  const toLocation    = urlParams.get("to")    || "";
  const departureDate = urlParams.get("date")  || "";
  const departureTime = urlParams.get("time")  || "";
  const priceParam    = parseInt(urlParams.get("price"), 10);
  const price         = Number.isNaN(priceParam) ? 45000 : priceParam;

  // tripId chỉ dùng để hỏi API ghế đã đặt
  const tripId        = urlParams.get("trip_id") || urlParams.get("id");

  const selectedSeats = new Set();
  let seatsData       = { lower: [] }; // sẽ build ở dưới

  // ====== HÀM TẠO DANH SÁCH GHẾ A01..A17, B01..B17 ======
  function buildAllSeats(bookedSet = new Set()) {
    const result = [];

    // Tầng dưới: A01..A17
    for (let i = 1; i <= 17; i++) {
      const id = "A" + String(i).padStart(2, "0");
      result.push({
        id,
        status: bookedSet.has(id) ? "sold" : "available",
      });
    }

    // Tầng trên: B01..B17
    for (let i = 1; i <= 17; i++) {
      const id = "B" + String(i).padStart(2, "0");
      result.push({
        id,
        status: bookedSet.has(id) ? "sold" : "available",
      });
    }

    seatsData.lower = result;
  }

  // ====== GỌI API LẤY GHẾ ĐÃ ĐẶT (NẾU CÓ tripId) ======
  async function loadBookedSeats() {
    if (!tripId) {
      // Không có tripId → coi như chưa ai đặt
      buildAllSeats(new Set());
      initializeAll();
      return;
    }

    try {
      // *** ĐƯỜNG DẪN PHẢI TRÙNG VỚI urls.py: "api/trip/<int:trip_id>/seats/" ***
      const res = await fetch(`/api/trip/${tripId}/seats/`);
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      const bookedSet = new Set(data.booked_seats || []);
      buildAllSeats(bookedSet);
    } catch (err) {
      console.error("Lỗi khi lấy danh sách ghế đã đặt:", err);
      // nếu lỗi API vẫn build hết available
      buildAllSeats(new Set());
    }

    initializeAll();
  }

  // ====== HIỂN THỊ INFO CHUYẾN ĐI ======
  function initializeDisplay() {
    const routeEl  = document.getElementById("route-display");
    const departEl = document.getElementById("departure-display");

    if (routeEl && fromLocation && toLocation) {
      routeEl.textContent = `${fromLocation} - ${toLocation}`;
    }
    if (departEl && departureTime && departureDate) {
      departEl.textContent = `${departureTime} ${departureDate}`;
    }
  }

  // ====== CHỌN ẢNH / MÀU THEO TRẠNG THÁI ======
  function getImageForStatus(status) {
    switch (status) {
      case "sold":      return IMG_SOLD;
      case "selected":  return IMG_SELECTED;
      case "available":
      default:          return IMG_AVAILABLE;
    }
  }

  function getColorForStatus(status) {
    switch (status) {
      case "sold":      return "var(--color-sold)";
      case "selected":  return "var(--color-selected)";
      case "available":
      default:          return "var(--color-available)";
    }
  }

  // ====== RENDER GHẾ ======
  function renderSeats() {
    const lowerFloor = document.getElementById("lower-floor");
    const upperFloor = document.getElementById("upper-floor");

    if (!lowerFloor || !upperFloor) {
      console.error("Không tìm thấy #lower-floor hoặc #upper-floor");
      return;
    }

    lowerFloor.innerHTML = "";
    upperFloor.innerHTML = "";

    const lowerSeats = seatsData.lower.filter((s) => s.id.startsWith("A"));
    const upperSeats = seatsData.lower.filter((s) => s.id.startsWith("B"));

    lowerSeats.forEach((seat) => {
      const isSelected = selectedSeats.has(seat.id);
      const status     = isSelected ? "selected" : seat.status;

      const seatEl = document.createElement("div");
      seatEl.className = `seat ${status}`;
      seatEl.id = `seat-${seat.id}`;
      seatEl.innerHTML = `
        <img src="${getImageForStatus(status)}" alt="${seat.id}">
        <div class="seat-number" style="color: ${getColorForStatus(status)}">${seat.id}</div>
      `;

      if (seat.status !== "sold") {
        seatEl.addEventListener("click", () => toggleSeat(seat.id));
      }

      lowerFloor.appendChild(seatEl);
    });

    upperSeats.forEach((seat) => {
      const isSelected = selectedSeats.has(seat.id);
      const status     = isSelected ? "selected" : seat.status;

      const seatEl = document.createElement("div");
      seatEl.className = `seat ${status}`;
      seatEl.id = `seat-${seat.id}`;
      seatEl.innerHTML = `
        <img src="${getImageForStatus(status)}" alt="${seat.id}">
        <div class="seat-number" style="color: ${getColorForStatus(status)}">${seat.id}</div>
      `;

      if (seat.status !== "sold") {
        seatEl.addEventListener("click", () => toggleSeat(seat.id));
      }

      upperFloor.appendChild(seatEl);
    });
  }

  function toggleSeat(seatId) {
    if (selectedSeats.has(seatId)) {
      selectedSeats.delete(seatId);
    } else {
      selectedSeats.add(seatId);
    }
    updateUI();
  }

  function updateUI() {
    renderSeats();
    updateSummary();
  }

  // ====== SUMMARY / TIỀN ======
  function updateSummary() {
    const count = selectedSeats.size;
    const total = count * price;
    const seats = Array.from(selectedSeats).sort().join(", ");

    const seatCountEl   = document.getElementById("seat-count");
    const selectedEl    = document.getElementById("selected-seats");
    const tripTotalEl   = document.getElementById("trip-total");
    const ticketPriceEl = document.getElementById("ticket-price");
    const paymentFeeEl  = document.getElementById("payment-fee");
    const totalSumEl    = document.getElementById("total-summary");
    const totalPriceEl  = document.getElementById("total-price");

    if (seatCountEl)   seatCountEl.textContent   = `${count} Ghế`;
    if (selectedEl)    selectedEl.textContent    = seats || "-";
    if (tripTotalEl)   tripTotalEl.textContent   = `${total.toLocaleString("vi-VN")}đ`;
    if (ticketPriceEl) ticketPriceEl.textContent = `${total.toLocaleString("vi-VN")}đ`;
    if (paymentFeeEl)  paymentFeeEl.textContent  = `0đ`;
    if (totalSumEl)    totalSumEl.textContent    = `${total.toLocaleString("vi-VN")}đ`;
    if (totalPriceEl)  totalPriceEl.textContent  = `${total.toLocaleString("vi-VN")}đ`;
  }

  // ====== ĐIỂM ĐÓN / TRẢ ======
  function initializePickupDropoff() {
    const pickupLocEl  = document.getElementById("pickup-location-display");
    const dropoffLocEl = document.getElementById("dropoff-location-display");
    const pickupTimeEl = document.getElementById("pickup-time-display");

    if (!pickupLocEl || !dropoffLocEl || !pickupTimeEl) return;

    if (fromLocation)  pickupLocEl.textContent  = fromLocation;
    if (toLocation)    dropoffLocEl.textContent = toLocation;

    if (departureTime && departureDate) {
      const [hourStr, minuteStr] = departureTime.split(":");
      const arrival = new Date();
      arrival.setHours(parseInt(hourStr, 10), parseInt(minuteStr, 10) - 30, 0, 0);

      const arrivalHour   = arrival.getHours().toString().padStart(2, "0");
      const arrivalMinute = arrival.getMinutes().toString().padStart(2, "0");

      pickupTimeEl.textContent = `Trước ${arrivalHour}:${arrivalMinute} ${departureDate}`;
    }
  }

  // ====== NÚT HỦY / THANH TOÁN ======
  const cancelBtn  = document.getElementById("cancel-btn");
  const paymentBtn = document.getElementById("payment-btn");

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      if (window.history.length > 1) {
        window.history.back();
      } else {
        window.location.href = INDEX_URL;
      }
    });
  }

  if (paymentBtn) {
    paymentBtn.addEventListener("click", () => {
      if (selectedSeats.size === 0) {
        alert("Vui lòng chọn ít nhất 1 ghế!");
        return;
      }
      if (!document.getElementById("terms-agree").checked) {
        alert("Vui lòng chấp nhận điều khoản!");
        return;
      }

      const gmail = document.getElementById("gmail-input").value.trim();
      const gmailRegex = /^[a-zA-Z0-9._%+-]+@gmail\.com$/;

      if (!gmail) {
        alert("Vui lòng nhập email Gmail!");
        return;
      }
      if (!gmailRegex.test(gmail)) {
        alert("Email phải là Gmail hợp lệ (ví dụ: abc@gmail.com)!");
        return;
      }

      const phone = document.getElementById("phone-input").value.trim();
      const phoneRegex = /^(0|\+84)\d{9,10}$/;

      if (!phone) {
        alert("Vui lòng nhập số điện thoại!");
        return;
      }
      if (!phoneRegex.test(phone)) {
        alert("Số điện thoại không hợp lệ! Ví dụ: 0912345678 hoặc +84912345678");
        return;
      }

      const seats = Array.from(selectedSeats).join(",");

      const paymentUrl =
        PAYMENT_URL +
        "?seats=" + encodeURIComponent(seats) +
        "&from=" + encodeURIComponent(fromLocation) +
        "&to=" + encodeURIComponent(toLocation) +
        "&date=" + encodeURIComponent(departureDate) +
        "&time=" + encodeURIComponent(departureTime) +
        "&price=" + encodeURIComponent(price) +
        "&gmail=" + encodeURIComponent(gmail) +
        "&phone=" + encodeURIComponent(phone) +
        (tripId ? "&trip_id=" + encodeURIComponent(tripId) : "");

      window.location.href = paymentUrl;
    });
  }

  // ====== HÀM KHỞI TẠO CHUNG ======
  function initializeAll() {
    initializeDisplay();
    renderSeats();
    initializePickupDropoff();
    updateSummary();
  }

  // Bắt đầu: load ghế đã đặt (nếu có), rồi init
  loadBookedSeats();
});
