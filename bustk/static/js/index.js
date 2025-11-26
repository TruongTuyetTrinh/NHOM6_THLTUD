// Danh sách 63 tỉnh/thành Việt Nam
const provinces = [
    "Hà Nội", "TP Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ",
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu",
    "Bắc Ninh", "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước",
    "Bình Thuận", "Cà Mau", "Cao Bằng", "Đắk Lắk", "Đắk Nông",
    "Điện Biên", "Đồng Nai", "Đồng Tháp", "Gia Lai", "Hà Giang",
    "Hà Nam", "Hà Tĩnh", "Hải Dương", "Hậu Giang", "Hòa Bình",
    "Hưng Yên", "Khánh Hòa", "Kiên Giang", "Kon Tum", "Lai Châu",
    "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định",
    "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên",
    "Quảng Bình", "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị",
    "Sóc Trăng", "Sơn La", "Tây Ninh", "Thái Bình", "Thái Nguyên",
    "Thanh Hóa", "Thừa Thiên Huế", "Tiền Giang", "Trà Vinh", "Tuyên Quang",
    "Vĩnh Long", "Vĩnh Phúc", "Yên Bái"
];

$(document).ready(function () {
    const $from = $('#from_location');
    const $to = $('#to_location');

    // ================== 0. ĐỌC QUERY STRING (dùng cho ĐẶT LẠI) ==================
    // URL kiểu: /?from=TP Hồ Chí Minh&to=Bà Rịa - Vũng Tàu
    const urlParams   = new URLSearchParams(window.location.search);
    const fromPrefill = urlParams.get("from");  // dùng from
    const toPrefill   = urlParams.get("to");    // dùng to

    // ================== 1. GÁN OPTIONS TỈNH/THÀNH ==================
    provinces.forEach(function (p) {
        $from.append(new Option(p, p, false, false));
        $to.append(new Option(p, p, false, false));
    });

    // ================== 2. MATCHER KHÔNG DẤU CHO SELECT2 ==================
    function accentInsensitiveMatcher(params, data) {
        if ($.trim(params.term) === '') {
            return data;
        }
        if (!data.text) {
            return null;
        }
        const normalizedTerm = params.term.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
        const normalizedText = data.text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
        if (normalizedText.indexOf(normalizedTerm) > -1) {
            return data;
        }
        return null;
    }

    // ================== 3. INIT SELECT2 ==================
    const select2Config = {
        theme: 'bootstrap-5',
        language: 'vi',
        placeholder: 'Chọn tỉnh/thành',
        allowClear: true,
        width: '100%',
        dropdownParent: $('.search-form'),
        minimumResultsForSearch: 0,
        matcher: accentInsensitiveMatcher
    };

    $('.select2').select2(select2Config);

    // Không cho Điểm đến trùng Điểm đi
    function refreshToOptions() {
        const fromVal = $from.val();
        $to.find('option').prop('disabled', false);
        if (fromVal) {
            $to.find('option[value="' + fromVal + '"]').prop('disabled', true);
            if ($to.val() === fromVal) {
                $to.val(null).trigger('change');
            }
        }
        $to.trigger('change.select2');
    }

    $from.on('change', function () {
        refreshToOptions();
    });

    $to.on('change', function () {
        if ($(this).val() === $from.val()) {
            alert('Điểm đi và điểm đến không được trùng nhau!');
            $(this).val(null).trigger('change');
            setTimeout(() => $(this).select2('open'), 0);
        }
    });

    refreshToOptions();

    // ================== 4. ẨN/HIỆN NGÀY VỀ – CĂN LẠI FORM ==================
    function updateAlignment() {
        const isOneWay = $('#one_way').is(':checked');
        $('#return_date_group').toggle(!isOneWay);
        $('#input-row').toggleClass('centered', isOneWay);
    }
    updateAlignment();
    $('input[name="trip_type"]').on('change', updateAlignment);

    // ================== 5. GIỚI HẠN NGÀY KHÔNG CHO CHỌN QUÁ KHỨ ==================
    const today = new Date().toISOString().split('T')[0];
    $('#departure_date, #return_date').attr('min', today);

    // ================== 5.1 PREFILL from/to TỪ URL & AUTO TÌM ==================
    const $form = $('.search-form form');

    if (fromPrefill) {
        $from.val(fromPrefill).trigger('change');
    }
    if (toPrefill) {
        $to.val(toPrefill).trigger('change');
    }

    // Nếu có from & to → tự set ngày = hôm nay + tự submit form tìm chuyến
    if (fromPrefill && toPrefill) {
        $('#departure_date').val(today);
        // cho Select2 render xong rồi mới submit để tránh race
        setTimeout(function () {
            $form.trigger('submit');
        }, 100);
    }

    // ================== 6. LOGIC TÌM KIẾM GIẢ LẬP + FILTER ==================
    const resultsContainer = $('#search-results-container');
    const resultsDiv = $('#search-results');
    const noResultsDiv = $('#no-results');
    const popularSection = $('.popular-routes');
    const backButton = $('#back-to-search');
    const routeTitle = $('#search-route-title');
    const metaInfo = $('#search-meta-info');
    const resultsSummary = $('#search-results-summary');

    let allTrips = [];
    let tripsData = {};

    function randomInt(min, max) {
        return Math.floor(Math.random() * (max - min + 1)) + min;
    }

    function isSameDate(a, b) {
        return a.getFullYear() === b.getFullYear() &&
               a.getMonth()    === b.getMonth() &&
               a.getDate()     === b.getDate();
    }

    function generateRandomTrips(fromLocation, toLocation, departureDate, numTrips) {
        const vehicleTypes = ['Giường nằm', 'Ghế ngồi', 'Limousine', 'Xe giường VIP', 'Xe khách 45 chỗ'];
        const vehicleTypeMap = {
            'Ghế ngồi': 'Ghế',
            'Giường nằm': 'Giường',
            'Xe giường VIP': 'Giường',
            'Limousine': 'Limousine',
            'Xe khách 45 chỗ': 'Ghế'
        };

        const seatRows = ['front', 'middle', 'back'];
        const floors   = ['upper', 'lower'];

        const trips = [];
        const now   = new Date();

        // cho phép loop thêm để đủ số chuyến hợp lệ
        let tries = 0;
        const maxTries = numTrips * 3;

        while (trips.length < numTrips && tries < maxTries) {
            tries++;

            const departureHour   = randomInt(5, 22);
            const departureMinute = randomInt(0, 59);

            const durationHours   = randomInt(2, 12);
            const durationMinutes = randomInt(0, 59);

            const departureDateTime = new Date(departureDate);
            departureDateTime.setHours(departureHour, departureMinute, 0, 0);

            // NẾU LÀ NGÀY HÔM NAY và thời gian khởi hành < 40 phút nữa → bỏ qua
            if (isSameDate(departureDateTime, now)) {
                const diffMin = (departureDateTime - now) / 60000; // phút
                if (diffMin < 40) {
                    continue; // không push chuyến này
                }
            }

            const arrivalDateTime = new Date(departureDateTime);
            arrivalDateTime.setHours(arrivalDateTime.getHours() + durationHours);
            arrivalDateTime.setMinutes(arrivalDateTime.getMinutes() + durationMinutes);

            const vehicleType = vehicleTypes[randomInt(0, vehicleTypes.length - 1)];

            trips.push({
                id: randomInt(1000, 9999),
                departure_location: fromLocation,
                arrival_location: toLocation,
                departure_time: departureDateTime.toISOString(),
                arrival_time: arrivalDateTime.toISOString(),
                vehicle_type: vehicleType,
                vehicle_type_filter: vehicleTypeMap[vehicleType] || 'Ghế',
                available_seats: randomInt(8, 45),
                price: randomInt(250000, 1500000),
                seat_row: seatRows[randomInt(0, seatRows.length - 1)],
                floor: floors[randomInt(0, floors.length - 1)]
            });
        }

        // sắp xếp theo giờ đi
        return trips.sort((a, b) => new Date(a.departure_time) - new Date(b.departure_time));
    }

    // Submit form tìm kiếm
    $form.on('submit', function (e) {
        e.preventDefault();

        const fromLocation = $('#from_location').val();
        const toLocation = $('#to_location').val();
        const departureDate = $('#departure_date').val();
        const returnDate = $('#return_date').val();
        const passengers = $('#passengers').val();
        const isRoundTrip = $('#round_trip').is(':checked');

        if (!fromLocation || !toLocation || !departureDate) {
            alert('Vui lòng điền đầy đủ thông tin tìm kiếm!');
            return;
        }

        // Không cho chọn ngày quá khứ (nếu người dùng tự gõ tay)
        if (departureDate < today) {
            alert('Ngày đi không được nhỏ hơn hôm nay!');
            $('#departure_date').val(today);
            return;
        }
        if (isRoundTrip && returnDate && returnDate < departureDate) {
            alert('Ngày về phải sau hoặc bằng ngày đi!');
            return;
        }

        routeTitle.text(fromLocation + ' → ' + toLocation);

        const metaPieces = ['Ngày đi ' + formatDate(departureDate)];
        if (isRoundTrip && returnDate) {
            metaPieces.push('Ngày về ' + formatDate(returnDate));
        }
        metaPieces.push(passengers + ' hành khách');
        metaInfo.text(metaPieces.join(' • '));

        const numTrips = randomInt(5, 10);
        allTrips = generateRandomTrips(fromLocation, toLocation, departureDate, numTrips);

        $('.filter-chip').removeClass('active');
        updateFilterCounts(allTrips);
        applyFilters();

        popularSection.hide();
        resultsContainer.show();
        window.scrollTo({ top: resultsContainer.offset().top - 80, behavior: 'smooth' });
    });

    function updateFilterCounts(trips) {
        const timeCounts = { '0-6': 0, '6-12': 0, '12-18': 0, '18-24': 0 };
        const vehicleCounts = {};
        const seatRowCounts = {};
        const floorCounts = {};

        trips.forEach(function (trip) {
            const hour = new Date(trip.departure_time).getHours();
            if (hour >= 0 && hour < 6) timeCounts['0-6']++;
            else if (hour >= 6 && hour < 12) timeCounts['6-12']++;
            else if (hour >= 12 && hour < 18) timeCounts['12-18']++;
            else if (hour >= 18 && hour < 24) timeCounts['18-24']++;

            const type = trip.vehicle_type_filter;
            vehicleCounts[type] = (vehicleCounts[type] || 0) + 1;

            const row = trip.seat_row;
            seatRowCounts[row] = (seatRowCounts[row] || 0) + 1;

            const floor = trip.floor;
            floorCounts[floor] = (floorCounts[floor] || 0) + 1;
        });

        $('.filter-chip[data-filter="time"]').each(function () {
            const value = $(this).data('value');
            $(this).find('.filter-count').text('(' + (timeCounts[value] || 0) + ')');
        });
        $('.filter-chip[data-filter="vehicle"]').each(function () {
            const value = $(this).data('value');
            $(this).find('.filter-count').text('(' + (vehicleCounts[value] || 0) + ')');
        });
        $('.filter-chip[data-filter="seat_row"]').each(function () {
            const value = $(this).data('value');
            $(this).find('.filter-count').text('(' + (seatRowCounts[value] || 0) + ')');
        });
        $('.filter-chip[data-filter="floor"]').each(function () {
            const value = $(this).data('value');
            $(this).find('.filter-count').text('(' + (floorCounts[value] || 0) + ')');
        });
    }

    function applyFilters() {
        if (allTrips.length === 0) return;

        const activeFilters = {
            time: [],
            vehicle: [],
            seat_row: [],
            floor: []
        };

        $('.filter-chip.active').each(function () {
            const filterType = $(this).data('filter');
            const filterValue = $(this).data('value');
            if (activeFilters[filterType]) {
                activeFilters[filterType].push(filterValue);
            }
        });

        let filteredTrips = allTrips.filter(function (trip) {
            if (activeFilters.time.length > 0) {
                const hour = new Date(trip.departure_time).getHours();
                let matchesTime = false;
                activeFilters.time.forEach(function (timeRange) {
                    const parts = timeRange.split('-');
                    const min = parseInt(parts[0], 10);
                    const max = parseInt(parts[1], 10);
                    if (hour >= min && hour < max) {
                        matchesTime = true;
                    }
                });
                if (!matchesTime) return false;
            }

            if (activeFilters.vehicle.length > 0 &&
                !activeFilters.vehicle.includes(trip.vehicle_type_filter)) {
                return false;
            }

            if (activeFilters.seat_row.length > 0 &&
                !activeFilters.seat_row.includes(trip.seat_row)) {
                return false;
            }

            if (activeFilters.floor.length > 0 &&
                !activeFilters.floor.includes(trip.floor)) {
                return false;
            }

            return true;
        });

        if (filteredTrips.length > 0) {
            noResultsDiv.hide();
            resultsDiv.show();
            renderTrips(filteredTrips);
            resultsSummary.text(filteredTrips.length + ' chuyến xe phù hợp');
        } else {
            noResultsDiv.show();
            resultsDiv.hide();
            resultsSummary.text('0 chuyến xe phù hợp');
        }
    }

    $(document).on('click', '.filter-chip', function () {
        $(this).toggleClass('active');
        applyFilters();
    });

    $(document).on('click', '.filter-reset', function () {
        $('.filter-chip').removeClass('active');
        applyFilters();
    });

    backButton.on('click', function () {
        resultsContainer.hide();
        popularSection.show();
        resultsDiv.empty();
        resultsSummary.text('');
        metaInfo.text('');
        allTrips = [];
    });

    function renderTrips(trips) {
        tripsData = {};
        const cardsHtml = trips.map(function (trip) {
            const duration = calculateDuration(trip.departure_time, trip.arrival_time);
            tripsData[trip.id] = trip;
            return `
                <div class="trip-card">
                    <div class="trip-card-header">
                        <div class="trip-time-col">
                            <span class="time">${formatTime(trip.departure_time)}</span>
                            <span class="station">${trip.departure_location}</span>
                        </div>
                        <div class="trip-card-divider">
                            <span class="duration">${duration}</span>
                            <span class="divider-line"></span>
                            <span class="duration-note">Trung chuyển</span>
                        </div>
                        <div class="trip-time-col end text-end">
                            <span class="time">${formatTime(trip.arrival_time)}</span>
                            <span class="station">${trip.arrival_location}</span>
                        </div>
                    </div>
                    <div class="trip-card-meta">
                        <span><i class="fas fa-bus me-1"></i>${trip.vehicle_type}</span>
                        <span class="separator">•</span>
                        <span>${trip.available_seats} chỗ trống</span>
                        <span class="separator">•</span>
                        <span>Không ghép khách</span>
                    </div>
                    <div class="trip-chip-list">
                        <span class="trip-chip"><i class="fas fa-random"></i> Trung chuyển</span>
                        <span class="trip-chip"><i class="fas fa-file-contract"></i> Chính sách linh hoạt</span>
                    </div>
                    <div class="trip-card-footer">
                        <div class="trip-card-price">${formatPrice(trip.price)}</div>
                        <button class="btn btn-select-trip" onclick="selectTrip(${trip.id})">
                            Chọn chuyến
                        </button>
                    </div>
                </div>
            `;
        }).join('');
        resultsDiv.html(cardsHtml);
    }

    function formatTime(dt) {
        return new Date(dt).toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    }

    function formatPrice(p) {
        return new Intl.NumberFormat('vi-VN').format(p) + 'đ';
    }

    function calculateDuration(s, e) {
        const diff = Math.max((new Date(e) - new Date(s)) / 60000, 0);
        const h = Math.floor(diff / 60);
        const m = Math.round(diff % 60);
        const parts = [];
        if (h > 0) parts.push(h + ' giờ');
        if (m > 0) parts.push(m + ' phút');
        return parts.join(' ') || '0 phút';
    }

    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('vi-VN', {
            weekday: 'short',
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    // ================== 7. CHỌN CHUYẾN → CHỌN GHẾ ==================
    window.selectTrip = function (id) {
        const trip = tripsData[id];
        if (!trip) {
            alert('Không tìm thấy thông tin chuyến!');
            return;
        }

        const from = encodeURIComponent(trip.departure_location);
        const to = encodeURIComponent(trip.arrival_location);
        const depTime = new Date(trip.departure_time);
        const date = depTime.toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit'
        });
        const time = depTime.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });

        const configEl = document.getElementById('seat-selection-config');
        const seatSelectionUrl = configEl ? configEl.dataset.seatSelectionUrl : '/seat-selection/';

        const url =
            seatSelectionUrl +
            '?from=' + from +
            '&to=' + to +
            '&date=' + date +
            '&time=' + time +
            '&price=' + trip.price +
            '&id=' + id;

        window.location.href = url;
    };
});
