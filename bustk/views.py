# FILE: views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_http_methods
import json
from .models import Trip, Ticket, PaymentOrder
from django.views.decorators.http import require_POST
import qrcode
from io import BytesIO
from django.http import HttpResponse, Http404
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import qrcode
from io import BytesIO
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
import os

from django.utils import timezone
from datetime import datetime

from .models import Ticket, Trip, PaymentOrder  # nếu chưa import
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from xhtml2pdf import pisa

from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Avg, Count

from .models import Ticket, Trip, Feedback
from .models import Notification

# === THÊM 3 DÒNG NÀY (CHỈ CẦN THÊM, KHÔNG SỬA GÌ KHÁC) ===
import random
from django.core.mail import send_mail
from django.conf import settings
VIETQR_SHEET_URL = "https://script.google.com/macros/s/AKfycbz1aRWfQeQSF8ZqgNVnDF5B6BH-spB-erpX0gfTZBrQ717cLQsn-2Q2By7cH7-tt8bNQQ/exec"
# =========================================================

otp_storage = {}

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({
                'status': 'success',
                'redirect': reverse('index')
            })
        else:
            if User.objects.filter(username=username).exists():
                error = 'Mật khẩu không đúng!'
            else:
                error = 'Tài khoản không tồn tại! Vui lòng <a href="/register/"> đăng ký</a>.'
            return JsonResponse({
                'status': 'error',
                'message': error
            }, status=400)

    return render(request, 'ticket/login.html')

def register_view(request):
    return render(request, 'ticket/register.html')

from django.contrib.auth import get_user_model
User = get_user_model()
@require_http_methods(["POST"])
def send_otp_view(request):
    email = request.POST.get('email')
    username = request.POST.get('username')
    phone = request.POST.get('phone')

    # === 1. KIỂM TRA THIẾU TRƯỜNG ===
    if not email or not username or not phone:
        return JsonResponse({'status': 'error', 'message': 'Thiếu thông tin bắt buộc!'})

    # === 2. KIỂM TRA TRÙNG EMAIL & USERNAME ===
    if User.objects.filter(email=email).exists():
        return JsonResponse({'status': 'error', 'message': 'Email đã được sử dụng!'})
    if User.objects.filter(username=username).exists():
        return JsonResponse({'status': 'error', 'message': 'Tên đăng nhập đã tồn tại!'})

    # === 3. TẠO OTP ===
    otp = str(random.randint(100000, 999999))
    otp_storage[email] = {'otp': otp, 'phone': phone}

    # === 4. GỬI EMAIL ===
    subject = 'Mã OTP Đăng Ký BusTicket'
    message = f'Mã OTP của bạn là: {otp}\nMã có hiệu lực trong 5 phút.'
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # Cần cấu hình trong settings.py
            [email],
            fail_silently=False,
        )
    except Exception as e:
        # Xóa OTP nếu gửi mail lỗi
        otp_storage.pop(email, None)
        return JsonResponse({'status': 'error', 'message': 'Không thể gửi email. Vui lòng thử lại.'})

    # === 5. TRẢ KẾT QUẢ ===
    return JsonResponse({'status': 'ok', 'message': 'OTP đã được gửi!'})


from django.db import transaction
from django.db.utils import OperationalError
import time  # Để sleep retry
import re  # ← THÊM ĐỂ VALIDATE SĐT

@require_http_methods(["POST"])
def verify_otp_view(request):
    data = request.POST
    email = data.get('email')
    otp = data.get('otp')
    fullname = data.get('fullname')
    username = data.get('username')
    password = data.get('password')
    phone = data.get('phone')  # ← THÊM: Lấy phone từ form

    # ===============================

    # === GIỮ NGUYÊN BẢN GỐC ===
    stored = otp_storage.get(email)
    if not stored or stored.get('otp') != otp:
        return JsonResponse({'status': 'error', 'message': 'Mã OTP không đúng!'})
    if User.objects.filter(username=username).exists():
        return JsonResponse({'status': 'error', 'message': 'Tên đăng nhập đã tồn tại!'})

    if User.objects.filter(email=email).exists():
        return JsonResponse({'status': 'error', 'message': 'Email đã được sử dụng!'})

    # Retry 3 lần nếu lock
    for attempt in range(3):
        try:
            with transaction.atomic():
                # === SỬA: DÙNG CustomUser, THÊM phone ===
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=fullname
                )
                user.phone = phone  # ← LƯU SĐT VÀO DB
                user.save()
                # =======================================
            otp_storage.pop(email, None)
            return JsonResponse({'status': 'ok', 'message': 'Đăng ký thành công!'})
        except OperationalError as e:
            if 'locked' in str(e) and attempt < 2:
                time.sleep(0.5)  # Đợi 0.5s
            else:
                return JsonResponse({'status': 'error', 'message': 'Hệ thống bận. Thử lại sau!'}, status=503)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

# views.py (thay hàm search_trips)
import random
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, date
from .models import Trip  # .models → bustk.models nếu cần import tuyệt đối


@login_required(login_url='login')
def search_trips(request):
    # 1. Lấy tham số
    from_loc = request.GET.get('from_location', '').strip()
    to_loc = request.GET.get('to_location', '').strip()
    dep_date = request.GET.get('departure_date')  # YYYY-MM-DD
    passengers = int(request.GET.get('passengers', 1))

    # 2. Query ban đầu
    qs = Trip.objects.all()

    # 3. Áp dụng filter (giữ nguyên)
    if from_loc:
        qs = qs.filter(departure_location__icontains=from_loc)
    if to_loc:
        qs = qs.filter(arrival_location__icontains=to_loc)
    if dep_date:
        try:
            d = datetime.strptime(dep_date, '%Y-%m-%d').date()
            qs = qs.filter(departure_time__date=d)
        except ValueError:
            pass  # Ngày sai → bỏ qua

    qs = qs.order_by('departure_time')

    # 4. FALLBACK LOGIC: Nếu < 3 kết quả → mở rộng query
    trip_list = list(qs)
    if len(trip_list) < 3:  # Ngưỡng: ít hơn 3 → fallback
        print("Fallback: Mở rộng tìm kiếm...")  # Debug log
        # Mở rộng: Bỏ filter ngày, chỉ giữ địa điểm lỏng lẻo
        qs_fallback = Trip.objects.all()
        if from_loc or to_loc:  # Chỉ nếu có địa điểm
            if from_loc:
                qs_fallback = qs_fallback.filter(
                    Q(departure_location__icontains=from_loc) | Q(arrival_location__icontains=from_loc))
            if to_loc:
                qs_fallback = qs_fallback.filter(
                    Q(departure_location__icontains=to_loc) | Q(arrival_location__icontains=to_loc))
        else:
            # Không có địa điểm → top phổ biến theo ngày gần nhất
            today = date.today()
            qs_fallback = Trip.objects.filter(departure_time__date__gte=today).order_by('-id')[:20]

        qs_fallback = qs_fallback.order_by('departure_time')
        trip_list_fallback = list(qs_fallback)
        if len(trip_list_fallback) > 10:
            trip_list_fallback = random.sample(trip_list_fallback, 10)
        trip_list = trip_list + trip_list_fallback[:5]  # Kết hợp, giới hạn 5 fallback
        trip_list = list(set(trip_list))  # Loại trùng
        random.shuffle(trip_list)  # Random để đa dạng

    # 5. Giới hạn ≤10
    if len(trip_list) > 10:
        trip_list = random.sample(trip_list, 10)

    # 6. AJAX → JSON (sửa available_seats)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = [{
            'id': t.id,
            'departure_location': t.departure_location,
            'arrival_location': t.arrival_location,
            'departure_time': t.departure_time.isoformat(),
            'arrival_time': t.arrival_time.isoformat(),
            'vehicle_type': t.vehicle_type.capitalize(),
            'price': float(t.price),
            'available_seats': t.available_seats,  # SỬA: DÙNG PROPERTY
        } for t in trip_list]
        return JsonResponse({'trips': data, 'total_found': len(trip_list)})  # Thêm total_found cho UX

    # 7. Trang HTML
    context = {
        'trips': trip_list,
        'no_results': len(trip_list) == 0,  # Luôn False sau fallback
        'search_params': {
            'from_location': from_loc,
            'to_location': to_loc,
            'departure_date': dep_date,
            'passengers': passengers,
        }
    }
    return render(request, 'bustk/search_results.html', context)  # Thay 'ticket' → 'bustk' nếu cần



def logout_view(request):
    logout(request)
    return redirect('login')

# @login_required(login_url='login')
# def index(request):
#     return render(request, 'ticket/index.html')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse, HttpResponseBadRequest

from .models import Trip, Ticket


# ===================== INDEX / TRANG CHỦ =====================

def index(request):
    """
    Trang chủ:
    - Nếu có ?from=&to= -> hiển thị các chuyến xe tương ứng
    - Luôn hiển thị các tuyến phổ biến (dựa trên PaymentOrder đã thanh toán)
    """
    # === 1. ĐỌC PARAM TÌM KIẾM ===
    from_q = (request.GET.get("from") or "").strip()
    to_q   = (request.GET.get("to") or "").strip()

    # Chỉ lấy các chuyến còn sắp tới
    trips = Trip.objects.filter(
        departure_time__gte=timezone.now()
    ).order_by("departure_time")

    if from_q:
        trips = trips.filter(departure_location__icontains=from_q)
    if to_q:
        trips = trips.filter(arrival_location__icontains=to_q)

    has_search = bool(from_q or to_q)

    # === 2. TÍNH CÁC TUYẾN PHỔ BIẾN ===
    FROM_CITIES = ["Hà Nội", "Đà Nẵng", "TP Hồ Chí Minh"]
    popular_groups = []

    for city in FROM_CITIES:
        # Dựa trên PaymentOrder đã thanh toán
        orders_qs = (
            PaymentOrder.objects
            .filter(
                status="paid",
                from_location__icontains=city,
            )
            .values("to_location")
            .annotate(total=Count("id"))
            .order_by("-total")
        )

        top_destinations = orders_qs[:3]

        destinations = []
        for row in top_destinations:
            to_loc = row["to_location"]

            # Lấy 1 trip mẫu để show thời gian + giá, nếu có
            sample_trip = (
                Trip.objects
                .filter(
                    departure_location__icontains=city,
                    arrival_location__icontains=to_loc,
                )
                .order_by("departure_time")
                .first()
            )

            duration_str = None
            date_str = None
            price = None

            if sample_trip:
                delta = sample_trip.arrival_time - sample_trip.departure_time
                mins = int(delta.total_seconds() // 60)
                hours = mins // 60
                rest = mins % 60
                if hours and rest:
                    duration_str = f"{hours} giờ {rest} phút"
                elif hours:
                    duration_str = f"{hours} giờ"
                else:
                    duration_str = f"{rest} phút"

                date_str = sample_trip.departure_time.strftime("%d/%m/%Y")
                price = sample_trip.price

            destinations.append({
                "to_location": to_loc,
                "duration_str": duration_str,
                "date_str": date_str,
                "price": price,
                "total": row["total"],   # nếu muốn show "đã đặt X lần"
            })

        popular_groups.append({
            "from_location": city,
            "destinations": destinations,
        })

    context = {
        "popular_groups": popular_groups,

        # cho phần search/list chuyến
        "trips": trips,
        "from_value": from_q,
        "to_value": to_q,
        "has_search": has_search,
    }
    return render(request, "ticket/index.html", context)

# ===================== DANH SÁCH CHUYẾN XE (ĐƠN GIẢN) =====================

# views.py
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render
from .models import Trip

def trip_list(request):
    # Lấy filter từ query string
    from_q = request.GET.get('from', '').strip()
    to_q = request.GET.get('to', '').strip()
    vehicle_q = request.GET.get('vehicle_type', '').strip()

    # Chỉ lấy chuyến còn khởi hành cách hiện tại >= 40 phút
    now = timezone.now()
    trips = Trip.objects.filter(
        departure_time__gte=now + timedelta(minutes=40)
    ).order_by('departure_location', 'arrival_location', 'departure_time')

    if from_q:
        trips = trips.filter(departure_location__icontains=from_q)
    if to_q:
        trips = trips.filter(arrival_location__icontains=to_q)
    if vehicle_q:
        trips = trips.filter(vehicle_type=vehicle_q)

    context = {
        'trips': trips,
        'from_q': from_q,
        'to_q': to_q,
        'vehicle_q': vehicle_q,
    }
    return render(request, 'ticket/trip_list.html', context)


# ===================== CHỌN GHẾ =====================

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Trip, Ticket

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Trip, Ticket

@login_required(login_url='login')
def seat_selection(request):
    # Lấy trip_id từ query (?trip_id=... hoặc ?id=...)
    trip_id = request.GET.get("trip_id") or request.GET.get("id")
    trip = None
    price = request.GET.get("price")

    if trip_id:
        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            trip = None

    # Nếu không có price trên URL thì fallback sang trip.price
    if not price and trip:
        price = trip.price

    context = {
        "trip_id": trip_id or "",
        "price": price or "",

        "user_fullname": request.user.get_full_name() or request.user.username,
        "user_phone": request.user.customuser.phone if hasattr(request.user, "customuser") else "",
    }
    return render(request, "ticket/seat_selection.html", context)

# ===================== API LẤY GHẾ ĐÃ ĐẶT =====================

def get_booked_seats(request, trip_id):
    """
    Trả về danh sách ghế đã đặt (upcoming + completed) cho 1 trip.
    JS sẽ hiển thị dạng 'sold'.
    """
    booked = Ticket.objects.filter(
        trip_id=trip_id,
        status__in=["upcoming", "completed"]
    ).values_list("seat_number", flat=True)

    return JsonResponse({"booked_seats": list(booked)})

# ===================== THANH TOÁN (ĐƠN GIẢN) =====================

from types import SimpleNamespace
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponseBadRequest
from .models import Trip  # đã có sẵn

@login_required(login_url='login')
def payment(request):
    seats_str = request.GET.get("seats", "")
    price_str = request.GET.get("price", "0")

    if not seats_str or not price_str:
        return HttpResponseBadRequest("Thiếu thông tin seats hoặc price")

    try:
        price = int(float(price_str))
    except ValueError:
        return HttpResponseBadRequest("Giá vé không hợp lệ")

    from_loc = request.GET.get("from", "")
    to_loc   = request.GET.get("to", "")
    date_str = request.GET.get("date", "")   # dạng 27-11
    time_str = request.GET.get("time", "")   # dạng 06:32
    trip_id  = request.GET.get("trip_id")

    seats_list   = [s.strip() for s in seats_str.split(",") if s.strip()]
    total_amount = price * len(seats_list)

    # Lấy trip nếu có id hợp lệ
    trip = None
    if trip_id:
        trip = Trip.objects.filter(id=trip_id).first()

    # Tạo ticket_code
    import uuid
    ticket_code = uuid.uuid4().hex[:10].upper()

    # Tạo PaymentOrder trong DB
    order = PaymentOrder.objects.create(
        user=request.user,
        trip=trip,
        seats=seats_str,
        amount=total_amount,
        ticket_code=ticket_code,
        status="pending",
        from_location=from_loc,
        to_location=to_loc,
        depart_date=date_str,
        depart_time=time_str,
    )

    # Thời gian hết hạn
    expires_at = timezone.now() + timedelta(minutes=5)

    # QR động
    qr_url = (
        "https://img.vietqr.io/image/MB-12080812228800-qr_only.png"
        f"?amount={total_amount}&addInfo={ticket_code}"
    )

    # ✅ LUÔN luôn gán biến này
    if trip and trip.departure_time:
        departure_display = trip.departure_time.strftime("%d/%m/%Y %H:%M")
    else:
        # fallback nếu không có trip (hoặc trip thiếu giờ)
        departure_display = f"{date_str} {time_str}"

    context = {
        "order": order,
        "trip": trip,
        "from_location": from_loc,
        "to_location": to_loc,
        "departure_display": departure_display,
        "total_amount": total_amount,
        "qr_url": qr_url,
        "expires_at": expires_at.isoformat(),
    }
    return render(request, "ticket/payment.html", context)

import requests

GGSHEET_URL = "https://script.google.com/macros/s/AKfycbz1aRWfQeQSF8ZqgNVnDF5B6BH-spB-erpX0gfTZBrQ717cLQsn-2Q2By7cH7-tt8bNQQ/exec"

@login_required(login_url='login')
def payment_status(request, ticket_code):

    try:
        order = PaymentOrder.objects.get(ticket_code=ticket_code, user=request.user)
    except PaymentOrder.DoesNotExist:
        return JsonResponse({"status": "not_found"})

    # Nếu đã paid
    if order.status == "paid":
        return JsonResponse({"status": "paid"})

    # Hết hạn
    if order.is_expired:
        order.status = "expired"
        order.save()
        return JsonResponse({"status": "expired"})

    # Gọi Google Sheet
    try:
        res = requests.get(GGSHEET_URL, timeout=5)
        data = res.json().get("data", [])
    except:
        return JsonResponse({"status": "pending"})

    # Dò từng dòng
    for row in data:
        description = str(row.get("Mô tả", "")).upper()
        amount = int(row.get("Giá trị", 0))

        # Điều kiện: nội dung chứa ticket_code + đúng số tiền
        if ticket_code in description and amount == order.amount:
            # Đánh dấu PAID
            order.status = "paid"
            order.paid_at = timezone.now()
            order.save()

            # Tạo ticket sau khi thanh toán
            create_tickets_from_order(order)



            return JsonResponse({"status": "paid"})

    return JsonResponse({"status": "pending"})

import json
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def casso_webhook(request):
    """
    Webhook Casso gọi vào khi có giao dịch mới.
    Bạn cần cấu hình URL này bên Casso.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Casso gửi list transactions
    transactions = data.get("data", [])

    for tx in transactions:
        description = (tx.get("description") or "").upper()
        amount = tx.get("amount")

        if not description or not amount:
            continue

        # Tìm tất cả PaymentOrder có ticket_code xuất hiện trong description
        pending_orders = PaymentOrder.objects.filter(
            status="pending"
        ).exclude(ticket_code__isnull=True)

        for order in pending_orders:
            # Kiểm tra ticket_code có trong description không
            if order.ticket_code in description and int(amount) == int(order.amount):
                # Kiểm tra chưa hết hạn
                if not order.is_expired:
                    order.status = "paid"
                    order.paid_at = timezone.now()
                    order.save()

                    # ✅ TẠO TICKET SAU KHI THANH TOÁN THÀNH CÔNG
                    create_tickets_from_order(order)

                break  # Đã xử lý order này, chuyển transaction tiếp theo

    return JsonResponse({"ok": True})


# @login_required(login_url='login')
# def my_tickets(request):
#     return render(request, 'ticket/my_tickets.html')
def create_tickets_from_order(order):
    """Tạo tickets từ PaymentOrder (CHỈ tạo nếu chưa có),
    tránh lỗi duplicate khi payment_status được gọi nhiều lần."""

    seats = [s.strip() for s in order.seats.split(",") if s.strip()]

    for seat in seats:
        exists = Ticket.objects.filter(
            payment_order=order,
            seat_number=seat
        ).exists()

        if not exists:
            Ticket.objects.create(
                user=order.user,
                trip=order.trip,    # có thể None → OK vì bạn đã cho null=True
                seat_number=seat,
                status="upcoming",
                payment_order=order,
            )
        if order.trip:
            Notification.objects.create(
                user=order.user,
                ticket=ticket,
                trip=order.trip,
                type=Notification.Type.BOOKING_SUCCESS,
                title="Đặt vé thành công",
                body=(
                    f"Bạn đã đặt vé thành công cho chuyến "
                    f"{order.trip.departure_location} → {order.trip.arrival_location} "
                    f"lúc {order.trip.departure_time:%H:%M %d/%m/%Y}. "
                    f"Số ghế: {seat}."
                )
            )
        else:
            # Trường hợp không có trip (đặt vé theo kiểu custom)
            Notification.objects.create(
                user=order.user,
                ticket=ticket,
                type=Notification.Type.BOOKING_SUCCESS,
                title="Đặt vé thành công",
                body=f"Bạn đã đặt vé thành công. Mã đặt chỗ: {order.ticket_code}."
            )

@login_required(login_url='login')
def schedules(request):
    return render(request, 'ticket/schedules.html')
# views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Notification, Trip, Ticket
from django.db.models import Q

@login_required(login_url='login')
def notifications_list(request):
    # Lấy tất cả thông báo của user
    noti_qs = Notification.objects.filter(user=request.user).order_by('-created_at')

    # Nhóm "Lịch trình của tôi"
    schedule_types = [
        Notification.Type.BOOKING_SUCCESS,
        Notification.Type.CANCEL_SUCCESS,
        Notification.Type.TRIP_REMINDER,
        Notification.Type.TRIP_START,
        Notification.Type.TRIP_COMPLETED,
    ]

    schedule_notifications = noti_qs.filter(type__in=schedule_types)
    other_notifications    = noti_qs.exclude(type__in=schedule_types)

    # Tuỳ bạn: vào trang là mark read hết:
    noti_qs.filter(is_read=False).update(is_read=True)

    context = {
        "schedule_notifications": schedule_notifications,
        "other_notifications": other_notifications,
        "unread_count": noti_qs.filter(is_read=False).count(),  # sau update sẽ = 0
    }
    return render(request, "ticket/notifications.html", context)

# @login_required(login_url='login')
# def messages(request):
#     return render(request, 'ticket/messages.html')

@login_required(login_url='login')
def notification_settings(request):
    return render(request, 'ticket/notification_settings.html')

import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import UserEmail, CustomUser  # Import CustomUser nếu dùng profile = user.customuser

@login_required
@require_http_methods(["GET", "POST"])
def profile_settings(request):
    if request.method == 'POST':
        try:
            if request.headers.get('Content-Type') == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            action = data.get('action')

            # === CẬP NHẬT PROFILE ===
            if action == 'update_profile':
                user = request.user  # Đây là CustomUser

                # Cập nhật username
                new_username = data.get('fullname', '').strip()
                if new_username and new_username != user.username:
                    if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                        return JsonResponse({'status': 'error', 'message': 'Tên đăng nhập đã tồn tại!'}, status=400)
                    user.username = new_username

                # Các field trong CustomUser
                user.phone = data.get('phone') or None
                user.birthday = data.get('birthday') or None
                user.gender = data.get('gender') or None
                user.address = data.get('address') or None

                password = data.get('password')
                if password:
                    user.set_password(password)

                user.save()
                return JsonResponse({'status': 'success'})

            # === THÊM EMAIL ===
            elif action == 'add_email':
                email = data.get('email')
                if not email:
                    return JsonResponse({'status': 'error', 'message': 'Email không được để trống'}, status=400)

                if User.objects.filter(email=email).exists() or UserEmail.objects.filter(email=email).exists():
                    return JsonResponse({'status': 'error', 'message': 'Email đã được sử dụng!'}, status=400)

                UserEmail.objects.create(user=request.user, email=email)
                return JsonResponse({'status': 'success'})

            # === XÓA EMAIL ===
            elif action == 'delete_email':
                email_id = data.get('email_id')
                try:
                    email_obj = UserEmail.objects.get(id=email_id, user=request.user)
                    email_obj.delete()
                    return JsonResponse({'status': 'success'})
                except UserEmail.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Email không tồn tại'}, status=400)

            return JsonResponse({'status': 'error', 'message': 'Yêu cầu không hợp lệ'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'ticket/profile_settings.html')

from django.utils import timezone
from datetime import datetime
from django.db.models import Q

@login_required(login_url="login")
def my_tickets(request):
    """
    Hiển thị danh sách vé theo 3 tab:
    - upcoming: sắp đi
    - completed: đã đi
    - cancelled: đã hủy

    + Tự động chuyển vé từ 'upcoming' -> 'completed' khi đã qua giờ khởi hành.
    """
    now = timezone.now()

    # ==== 1. AUTO CHUYỂN VÉ CÓ TRIP ====
    # Vé có trip, nếu departure_time <= now thì coi như ĐÃ ĐI
    Ticket.objects.filter(
        status="upcoming",
        trip__isnull=False,
        trip__departure_time__lte=now,
    ).update(status="completed")

    # ==== 2. AUTO CHUYỂN VÉ CHỈ GẮN PAYMENT_ORDER (không có trip) ====
    # Những vé này không có datetime chuẩn, phải tự parse từ depart_date / depart_time dạng chuỗi
    upcoming_no_trip = (
        Ticket.objects
        .filter(
            status="upcoming",
            trip__isnull=True,
            payment_order__isnull=False,
            user=request.user,
        )
        .select_related("payment_order")
    )

    cur_tz = timezone.get_current_timezone()
    cur_year = now.year

    for t in upcoming_no_trip:
        od = t.payment_order

        if not od.depart_date or not od.depart_time:
            continue

        # depart_date dạng "27-11", depart_time dạng "06:30"
        try:
            dt_naive = datetime.strptime(
                f"{od.depart_date} {od.depart_time} {cur_year}",
                "%d-%m %H:%M %Y",
            )
            depart_dt = timezone.make_aware(dt_naive, cur_tz)
        except Exception:
            continue

        if depart_dt <= now:
            t.status = "completed"
            t.save(update_fields=["status"])

    # ==== 3. LỌC THEO TAB NHƯ CŨ ====
    tab = request.GET.get("tab", "upcoming")

    base_qs = (
        Ticket.objects
        .filter(user=request.user)
        .select_related("trip", "payment_order")
        .order_by("-trip__departure_time", "-booking_date")
    )

    upcoming_qs  = base_qs.filter(status="upcoming")
    completed_qs = base_qs.filter(status="completed")
    cancelled_qs = base_qs.filter(status="cancelled")

    if tab == "completed":
        tickets = completed_qs
    elif tab == "cancelled":
        tickets = cancelled_qs
    else:
        tab = "upcoming"
        tickets = upcoming_qs

    context = {
        "tickets": tickets,
        "has_tickets": base_qs.exists(),
        "current_tab": tab,
        "upcoming_count": upcoming_qs.count(),
        "completed_count": completed_qs.count(),
        "cancelled_count": cancelled_qs.count(),
    }
    return render(request, "ticket/my_tickets.html", context)

from io import BytesIO
import os
import qrcode

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

from .models import Ticket


@login_required(login_url='login')
def download_ticket(request, ticket_id):
    """
    Tải vé dạng PDF (một vé = một ghế).
    PDF dùng font DejaVu để hiển thị tiếng Việt đẹp.
    """
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)
    trip   = ticket.trip
    order  = getattr(ticket, "payment_order", None)

    # ---- FONT UNICODE (DejaVu) ----
    font_path = os.path.join(settings.BASE_DIR, "static", "fonts", "DejaVuSans.ttf")
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("DejaVu", font_path))
            font_name = "DejaVu"
        except Exception:
            font_name = "Helvetica"
    else:
        font_name = "Helvetica"

    # ---- TẠO PDF ----
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 25 * mm
    margin_y = 25 * mm
    content_width = width - 2 * margin_x

    y = height - margin_y

    # ==== MÀU THƯƠNG HIỆU ====
    primary = HexColor("#2563EB")  # xanh DaNaGO
    primary_dark = HexColor("#1D4ED8")
    gray_border = HexColor("#E5E7EB")
    gray_text = HexColor("#4B5563")
    bg_light = HexColor("#F9FAFB")

    # ===== HEADER THANH MÀU + LOGO =====
    header_h = 28 * mm
    p.setFillColor(primary)
    p.setStrokeColor(primary)
    p.rect(0, height - header_h, width, header_h, stroke=0, fill=1)

    # Logo (nếu có file logo)
    logo_y = height - header_h + 6 * mm
    try:
        logo_path = os.path.join(settings.BASE_DIR, "static", "img", "logo.png")
        if os.path.exists(logo_path):
            p.drawImage(
                logo_path,
                margin_x,
                logo_y,
                width=24 * mm,
                height=16 * mm,
                preserveAspectRatio=True,
                mask="auto",
            )
            title_x = margin_x + 26 * mm
        else:
            title_x = margin_x
    except Exception:
        title_x = margin_x

    # ==== KHUNG CARD CHÍNH ====
    card_top = y
    card_bottom = margin_y + 20
    card_height = card_top - card_bottom

    p.setFillColor(bg_light)
    p.setStrokeColor(gray_border)
    p.setLineWidth(0.8)
    p.roundRect(
        margin_x,
        card_bottom,
        content_width,
        card_height,
        6 * mm,
        stroke=1,
        fill=1,
    )

    # Nội dung bên trong card
    inner_x = margin_x + 8 * mm
    inner_y = card_top - 8 * mm
    inner_width = content_width - 16 * mm

    # ===== THÔNG TIN VÉ (trên cùng, bên trái) =====
    p.setFillColor(primary_dark)
    p.setFont(font_name, 12)
    p.drawString(inner_x, inner_y, "Thông tin vé")
    inner_y -= 10 * mm

    p.setFont(font_name, 11)
    p.setFillColor(gray_text)
    p.drawString(inner_x, inner_y, f"Mã vé: {ticket.id}")
    inner_y -= 5 * mm

    if order and order.ticket_code:
        p.drawString(inner_x, inner_y, f"Mã thanh toán: {order.ticket_code}")
        inner_y -= 5 * mm

    full_name = request.user.get_full_name() or request.user.username
    p.drawString(inner_x, inner_y, f"Hành khách: {full_name}")
    inner_y -= 8 * mm

    # đường kẻ mảnh
    p.setStrokeColor(gray_border)
    p.setLineWidth(0.5)
    p.line(inner_x, inner_y, inner_x + inner_width, inner_y)
    inner_y -= 6 * mm

    # ===== THÔNG TIN CHUYẾN ĐI =====
    p.setFont(font_name, 12)
    p.setFillColor(primary_dark)
    p.drawString(inner_x, inner_y, "Thông tin chuyến đi")
    inner_y -= 8 * mm

    p.setFont(font_name, 11)
    p.setFillColor(gray_text)

    # Tuyến
    if trip and trip.departure_location and trip.arrival_location:
        route_str = f"{trip.departure_location} → {trip.arrival_location}"
    elif order and getattr(order, "from_location", None):
        to_loc = getattr(order, "to_location", "") or ""
        route_str = f"{order.from_location} → {to_loc}"
    else:
        route_str = "(Không xác định)"
    p.drawString(inner_x, inner_y, f"Tuyến: {route_str}")
    inner_y -= 5 * mm

    # Ngày đi
    if trip and getattr(trip, "departure_time", None):
        date_str = trip.departure_time.strftime("%d/%m/%Y")
    elif order and getattr(order, "depart_date", None):
        date_str = str(order.depart_date)
    else:
        date_str = "-"
    p.drawString(inner_x, inner_y, f"Ngày đi: {date_str}")
    inner_y -= 5 * mm

    # Giờ khởi hành
    if trip and getattr(trip, "departure_time", None):
        time_str = trip.departure_time.strftime("%H:%M")
    elif order and getattr(order, "depart_time", None):
        time_str = str(order.depart_time)
    else:
        time_str = "-"
    p.drawString(inner_x, inner_y, f"Giờ khởi hành: {time_str}")
    inner_y -= 5 * mm

    # Giờ đến dự kiến
    if trip and getattr(trip, "arrival_time", None):
        arr_str = trip.arrival_time.strftime("%H:%M")
        p.drawString(inner_x, inner_y, f"Giờ đến dự kiến: {arr_str}")
        inner_y -= 5 * mm

    # Số ghế
    p.drawString(inner_x, inner_y, f"Số ghế: {ticket.seat_number}")
    inner_y -= 8 * mm

    # ===== THÔNG TIN THANH TOÁN =====
    p.setStrokeColor(gray_border)
    p.setLineWidth(0.5)
    p.line(inner_x, inner_y, inner_x + inner_width, inner_y)
    inner_y -= 6 * mm

    p.setFont(font_name, 12)
    p.setFillColor(primary_dark)
    p.drawString(inner_x, inner_y, "Thông tin thanh toán")
    inner_y -= 8 * mm

    p.setFont(font_name, 11)
    p.setFillColor(gray_text)

    price_value = None
    if trip and trip.price is not None:
        price_value = int(trip.price)
    elif order:
        try:
            seat_count = max(len([s for s in order.seats.split(",") if s.strip()]), 1)
            price_value = int(order.amount / seat_count)
        except Exception:
            price_value = int(order.amount)

    if price_value is not None:
        price_str = f"{price_value:,} đ".replace(",", ".")
        p.drawString(inner_x, inner_y, f"Giá vé: {price_str}")
        inner_y -= 5 * mm

    status_map = {
        "upcoming": "Sắp đi",
        "completed": "Đã đi",
        "cancelled": "Đã hủy",
    }
    p.drawString(
        inner_x,
        inner_y,
        f"Trạng thái vé: {status_map.get(ticket.status, ticket.status)}",
    )
    inner_y -= 10 * mm

    # ===== Ô QR CHECK-IN BÊN PHẢI =====
    qr_size = 40 * mm
    qr_box_w = qr_size + 12 * mm
    qr_box_h = qr_size + 18 * mm
    qr_box_x = margin_x + content_width - qr_box_w - 8 * mm
    qr_box_y = card_bottom + 20 * mm

    p.setStrokeColor(gray_border)
    p.setFillColor(colors.white)
    p.setLineWidth(0.8)
    p.roundRect(qr_box_x, qr_box_y, qr_box_w, qr_box_h, 4 * mm, stroke=1, fill=1)

    p.setFont(font_name, 11)
    p.setFillColor(gray_text)
    p.drawString(qr_box_x + 6 * mm, qr_box_y + qr_box_h - 7 * mm, "Mã QR Check-in")

    if order and order.ticket_code:
        qr_img = qrcode.make(order.ticket_code)
        img_buffer = BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        qr_reader = ImageReader(img_buffer)

        p.drawImage(
            qr_reader,
            qr_box_x + 6 * mm,
            qr_box_y + 6 * mm,
            qr_size,
            qr_size,
            preserveAspectRatio=True,
            mask="auto",
        )
    else:
        p.setFont(font_name, 9)
        p.setFillColor(colors.red)
        p.drawString(qr_box_x + 6 * mm, qr_box_y + 10 * mm, "Không tìm thấy mã QR")

    # ===== FOOTER NHỎ =====
    p.setFont(font_name, 9)
    p.setFillColor(gray_text)
    footer_text = (
        "Vui lòng mang theo vé (hoặc mã QR / mã vé) khi lên xe để đối chiếu. "
        "Cảm ơn bạn đã sử dụng dịch vụ của DaNaGO!"
    )
    p.drawString(margin_x, card_bottom - 10, footer_text)

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    filename = f"ve_{ticket.id}.pdf"
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename=\"{filename}\"'
    return response

from decimal import Decimal
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
# nhớ đã import Ticket, Trip, PaymentOrder ở trên
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Ticket
@login_required(login_url='login')
def cancel_ticket(request, ticket_id):
    """
    GET: Hiển thị trang xác nhận hủy vé
    POST: Xử lý hủy vé

    Chính sách:
      - Hủy trước >= 24h: hoàn 100%
      - 12h <= Hủy < 24h: hoàn 50%
      - Hủy < 12h: vẫn cho hủy nhưng KHÔNG hoàn tiền
    """
    ticket = get_object_or_404(Ticket, id=ticket_id, user=request.user)

    # Chỉ cho hủy vé 'sắp đi'
    if ticket.status != "upcoming":
        messages.error(request, "Chỉ có thể hủy những vé ở mục 'Sắp đi'.")
        return redirect("my_tickets")

    order = ticket.payment_order
    trip = ticket.trip

    # ================= XÁC ĐỊNH GIỜ KHỞI HÀNH =================
    departure_dt = None

    # 1) Ticket có trip & departure_time
    if trip and getattr(trip, "departure_time", None):
        departure_dt = trip.departure_time

    # 2) Ticket không có trip nhưng PaymentOrder có trip
    elif order and order.trip and getattr(order.trip, "departure_time", None):
        trip = order.trip
        departure_dt = order.trip.departure_time

    # 3) Không có trip nhưng PaymentOrder có depart_date + depart_time (vd "27-11", "06:32")
    elif order and order.depart_date and order.depart_time:
        try:
            raw = f"{order.depart_date} {order.depart_time}"  # "27-11 06:32"
            year = order.created_at.year
            naive = datetime.strptime(raw, "%d-%m %H:%M")
            naive = naive.replace(year=year)
            tz = timezone.get_current_timezone()
            departure_dt = tz.localize(naive)
        except Exception:
            departure_dt = None

    # ================= TÍNH GIÁ VÉ GỐC =================
    seat_price = 0

    if trip and getattr(trip, "price", None) is not None:
        seat_price = int(trip.price)
    elif order:
        if getattr(order, "price_each", None):
            seat_price = int(order.price_each)
        else:
            # fallback: chia đều tổng tiền cho số ghế
            try:
                seats = [s.strip() for s in order.seats.split(",") if s.strip()]
                seat_count = max(len(seats), 1)
                seat_price = int(order.amount / seat_count)
            except Exception:
                seat_price = int(order.amount)

    # ================= TÍNH THỜI GIAN & HOÀN TIỀN =================
    diff_hours = None
    refund_percent = 0

    if departure_dt:
        now = timezone.now()
        diff = departure_dt - now
        diff_hours = diff.total_seconds() / 3600

        # Chính sách hoàn:
        if diff_hours >= 24:
            refund_percent = 100
        elif diff_hours >= 12:
            refund_percent = 50
        else:
            refund_percent = 0   # < 12h: vẫn hủy được nhưng không hoàn tiền

    # Phí hủy & số tiền hoàn lại
    fee_percent = 100 - refund_percent
    refund_fee = round(seat_price * fee_percent / 100) if seat_price else 0
    refund_amount = max(seat_price - refund_fee, 0)

    # ================= POST: XỬ LÝ HỦY VÉ =================
    if request.method == "POST":
        confirm = request.POST.get("confirm")

        if not confirm:
            messages.error(request, "Vui lòng xác nhận hủy vé.")
            return redirect("cancel_ticket", ticket_id=ticket_id)

        # PHƯƠNG ÁN B: luôn cho hủy, kể cả < 12h (refund_amount lúc đó = 0)
        with transaction.atomic():
            ticket.status = "cancelled"
            ticket.save(update_fields=["status"])
            # Nếu muốn, bạn xử lý log hoàn tiền / ví / v.v. ở đây
            if trip:  # phòng khi trip = None
                Notification.objects.create(
                    user=request.user,
                    ticket=ticket,
                    trip=trip,
                    type=Notification.Type.CANCEL_SUCCESS,
                    title="Hủy vé thành công",
                    body=(
                        f"Bạn đã hủy vé chuyến {trip.departure_location} → {trip.arrival_location} "
                        f"lúc {trip.departure_time:%H:%M %d/%m/%Y}."
                    ),
                )
        messages.success(
            request,
            (
                f"✅ Hủy vé thành công! Số tiền hoàn lại: {int(refund_amount):,}đ "
                f"(Phí hủy: {int(refund_fee):,}đ)"
            ).replace(",", "."),
        )
        return redirect("my_tickets")

    # ================= GET: HIỂN THỊ TRANG XÁC NHẬN =================
    context = {
        "ticket": ticket,
        "trip": trip,
        "order": order,
        "seat_price": int(seat_price),
        "diff_hours": round(diff_hours, 1) if diff_hours is not None else None,
        "refund_percent": refund_percent,
        "fee_percent": fee_percent,
        "refund_amount": int(refund_amount),
        "refund_fee": int(refund_fee),
        "can_cancel": True,   # phương án B: luôn cho hủy
    }
    return render(request, "ticket/cancel_ticket.html", context)



from urllib.parse import urlencode
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from .models import Ticket


from urllib.parse import urlencode
from django.urls import reverse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import date

from .models import Ticket


@login_required(login_url="login")
def rebook_ticket(request, pk):
    ticket = get_object_or_404(
        Ticket.objects.select_related("trip", "payment_order"),
        pk=pk,
        user=request.user,
    )

    trip = ticket.trip
    order = ticket.payment_order

    from_loc = ""
    to_loc = ""
    dep_date_str = None  # YYYY-MM-DD

    if trip:
        from_loc = trip.departure_location
        to_loc = trip.arrival_location
        if trip.departure_time:
            dep_date_str = trip.departure_time.date().isoformat()  # yyyy-mm-dd
    elif order:
        from_loc = order.from_location or ""
        to_loc = order.to_location or ""
        # order.depart_date đang kiểu "27-11" (dd-MM), ta convert sang yyyy-MM-dd
        if order.depart_date:
            try:
                day, month = order.depart_date.split("-")
                year = timezone.now().year
                d = date(year=int(year), month=int(month), day=int(day))
                dep_date_str = d.isoformat()
            except Exception:
                dep_date_str = None

    if not from_loc or not to_loc:
        messages.error(request, "Không tìm được tuyến đường để đặt lại.")
        return redirect("my_tickets")

    # Nếu ngày trong quá khứ thì đẩy về hôm nay cho chắc,
    # vì JS của bạn không cho chọn ngày < hôm nay
    today = timezone.now().date()
    if dep_date_str:
        try:
            y, m, d = dep_date_str.split("-")
            dep_d = date(int(y), int(m), int(d))
            if dep_d < today:
                dep_date_str = today.isoformat()
        except Exception:
            dep_date_str = today.isoformat()

    params = {
        "from_location": from_loc,
        "to_location": to_loc,
    }
    if dep_date_str:
        params["departure_date"] = dep_date_str

    url = f"{reverse('index')}?{urlencode(params)}"
    return redirect(url)
@login_required(login_url="login")
@require_POST
def submit_review(request, ticket_id):
    """
    Nhận đánh giá từ modal, tạo Feedback và trả về URL trang review của tuyến.
    """
    ticket = get_object_or_404(
        Ticket.objects.select_related("trip", "payment_order"),
        id=ticket_id,
        user=request.user,
    )

    trip = ticket.trip

    # 🔹 Nếu ticket không có trip, thử dò theo payment_order.from/to
    if not trip and ticket.payment_order and ticket.payment_order.from_location and ticket.payment_order.to_location:
        po = ticket.payment_order
        trip = (
            Trip.objects
            .filter(
                departure_location=po.from_location,
                arrival_location=po.to_location,
            )
            .order_by("-departure_time")
            .first()
        )

    # Nếu vẫn không có trip thì chịu
    if not trip:
        return JsonResponse(
            {"status": "error", "message": "Không tìm thấy chuyến đi để đánh giá."},
            status=400,
        )

    # -------- LẤY DỮ LIỆU FORM --------
    try:
        rating = int(request.POST.get("rating", 5))
    except ValueError:
        rating = 5
    rating = max(1, min(5, rating))

    title = (request.POST.get("title") or "").strip()
    content = (request.POST.get("content") or "").strip()
    image_file = request.FILES.get("image")

    Feedback.objects.create(
        user=request.user,
        trip=trip,
        rating=rating,
        title=title or "Không có tiêu đề",
        content=content,
        image=image_file,
    )

    redirect_url = reverse("route_reviews", args=[trip.id])
    return JsonResponse({"status": "success", "redirect_url": redirect_url})

@login_required(login_url="login")
def route_reviews(request, trip_id):
    """
    Trang hiển thị tất cả đánh giá của mọi khách cho CÙNG TUYẾN:
    cùng departure_location & arrival_location (không giới hạn ngày).
    """
    base_trip = get_object_or_404(Trip, id=trip_id)

    feedback_qs = (
        Feedback.objects
        .filter(
            trip__departure_location=base_trip.departure_location,
            trip__arrival_location=base_trip.arrival_location,
        )
        .select_related("user", "trip")
        .order_by("-created_at")
    )

    agg = feedback_qs.aggregate(
        avg_rating=Avg("rating"),
        total=Count("id"),
    )

    context = {
        "base_trip": base_trip,
        "feedbacks": feedback_qs,
        "avg_rating": agg["avg_rating"] or 0,
        "total_reviews": agg["total"] or 0,
    }
    return render(request, "ticket/route_reviews.html", context)
@login_required(login_url="login")
def my_reviews_entry(request):
    """
    Khi bấm menu 'Đánh giá' trên header:
    - Nếu user đã từng đánh giá: nhảy tới tuyến của feedback mới nhất
    - Nếu chưa có feedback nhưng có vé 'đã đi': nhảy tới tuyến của vé đã đi gần nhất
    - Nếu chưa đi/chưa đánh giá: quay về 'Vé của tôi'
    """
    # 1) Ưu tiên feedback mới nhất
    fb = (
        Feedback.objects
        .filter(user=request.user)
        .select_related("trip")
        .order_by("-created_at")
        .first()
    )
    if fb and fb.trip:
        return redirect("route_reviews", trip_id=fb.trip.id)

    # 2) Nếu chưa có feedback, lấy vé đã đi gần nhất
    ticket = (
        Ticket.objects
        .filter(user=request.user, status="completed")
        .select_related("trip")
        .order_by("-trip__departure_time")
        .first()
    )
    if ticket and ticket.trip:
        return redirect("route_reviews", trip_id=ticket.trip.id)

    # 3) Không có gì để review → quay lại Vé của tôi
    return redirect(f"{reverse('my_tickets')}?tab=upcoming")
# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.http import JsonResponse
from .models import Message
from .forms import MessageForm

@login_required
def message_list(request):
    user_messages = Message.objects.filter(user=request.user).order_by('created_at')

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.user = request.user
            msg.sender_name = request.user.username
            msg.is_from_user = True
            msg.save()
            return redirect('message_list')
    else:
        form = MessageForm()

    return render(request, 'ticket/messages.html', {
        'messages': user_messages,
        'form': form,
    })

@login_required
def message_list(request):
    """Hiển thị danh sách tin nhắn của user"""
    user_messages = Message.objects.filter(user=request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.user = request.user
            message.sender_name = request.user.username
            message.is_from_user = True
            message.save()
            django_messages.success(request, 'Tin nhắn đã được gửi!')
            return redirect('message_list')
    else:
        form = MessageForm()

    context = {
        'messages': user_messages,
        'form': form
    }
    return render(request, 'ticket/messages.html', context)


@login_required
def send_message(request):
    """API endpoint để gửi tin nhắn (AJAX)"""
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image')

        if content or image:
            message = Message.objects.create(
                user=request.user,
                sender_name=request.user.username,
                content=content if content else '',
                image=image,
                is_from_user=True
            )

            return JsonResponse({
                'success': True,
                'message': {
                    'id': message.id,
                    'sender_name': message.sender_name,
                    'content': message.content,
                    'image_url': message.image.url if message.image else None,
                    'is_from_user': message.is_from_user,
                    'created_at': message.created_at.strftime('%d/%m/%Y %H:%M')
                }
            })

        return JsonResponse({
            'success': False,
            'error': 'Vui lòng nhập nội dung hoặc chọn ảnh'
        })

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def get_messages(request):
    """API endpoint để lấy danh sách tin nhắn (AJAX)"""
    messages_list = Message.objects.filter(user=request.user)

    messages_data = [{
        'id': msg.id,
        'sender_name': msg.sender_name,
        'content': msg.content,
        'image_url': msg.image.url if msg.image else None,
        'is_from_user': msg.is_from_user,
        'created_at': msg.created_at.strftime('%d/%m/%Y %H:%M')
    } for msg in messages_list]

    return JsonResponse({
        'success': True,
        'messages': messages_data
    })


@login_required
def delete_message(request, message_id):
    """Xóa tin nhắn"""
    if request.method == 'POST':
        try:
            message = Message.objects.get(id=message_id, user=request.user)

            # Xóa file ảnh nếu có
            if message.image:
                message.image.delete()

            message.delete()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True})

            django_messages.success(request, 'Tin nhắn đã được xóa!')
        except Message.DoesNotExist:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Tin nhắn không tồn tại'})

            django_messages.error(request, 'Tin nhắn không tồn tại!')

    return redirect('message_list')

