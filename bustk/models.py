from django.db import models
from django.conf import settings

# FILE: models.py (app bustk)

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Quản trị viên'),
        ('user', 'Người dùng'),
    ]
    phone = models.CharField(max_length=15, blank=True, null=True)
    birthday = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', 'Nam'), ('female', 'Nữ'), ('other', 'Khác')], blank=True)
    address = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    # THÊM 2 DÒNG NÀY ĐỂ TRÁNH XUNG ĐỘT
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',  # ← THAY ĐỔI TÊN
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',  # ← CÙNG TÊN VỚI TRÊN
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == 'admin'


# models.py
from datetime import timedelta

class Trip(models.Model):
    VEHICLE_TYPES = [
        ('limousine', 'Limousine'),
        ('giuong', 'Giường'),
    ]

    departure_location = models.CharField(max_length=100)
    arrival_location = models.CharField(max_length=100)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES)
    total_seats = models.IntegerField(default=40)
    price = models.DecimalField(max_digits=10, decimal_places=0)

    @property
    def available_seats(self):
        from .models import Ticket  # nếu Ticket ở cùng file thì bỏ dòng này
        booked = Ticket.objects.filter(
            trip=self,
            status__in=['upcoming', 'completed']
        ).count()
        return max(self.total_seats - booked, 0)

    @property
    def duration_display(self):
        """Trả về chuỗi kiểu '6 giờ 30 phút' từ departure_time -> arrival_time"""
        delta = self.arrival_time - self.departure_time
        mins = int(delta.total_seconds() // 60)
        hours = mins // 60
        minutes = mins % 60
        if hours and minutes:
            return f"{hours} giờ {minutes} phút"
        elif hours:
            return f"{hours} giờ"
        else:
            return f"{minutes} phút"

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Sắp đi'),
        ('completed', 'Đã đi'),
        ('cancelled', 'Đã hủy'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tickets",
    )
    trip = models.ForeignKey(
        Trip,
        on_delete=models.CASCADE,
        null=True, blank=True,  # 👈 thêm 2 flag này
    )
    seat_number = models.CharField(max_length=5)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_order = models.ForeignKey(
        'PaymentOrder',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='tickets'
    )
    reminder_30m_sent = models.BooleanField(default=False)
    started_notified = models.BooleanField(default=False)
    completed_notified = models.BooleanField(default=False)

    def __str__(self):
        return f"Ticket {self.id} - {self.user.username}"

class Notification(models.Model):
    class Type(models.TextChoices):
        BOOKING_SUCCESS = 'booking_success', 'Đặt vé thành công'
        CANCEL_SUCCESS  = 'cancel_success',  'Hủy vé thành công'
        TRIP_REMINDER   = 'trip_reminder',   'Chuyến xe sắp khởi hành'
        TRIP_START      = 'trip_start',      'Chuyến xe đang khởi hành'
        TRIP_COMPLETED  = 'trip_completed',  'Chuyến xe đã hoàn thành'
        OTHER           = 'other',           'Thông báo khác'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)

    type = models.CharField(
        max_length=50,
        choices=Type.choices,
        default=Type.OTHER
    )

    ticket = models.ForeignKey(
        'Ticket', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notifications'
    )

    trip = models.ForeignKey(
        'Trip', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='notifications'
    )

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    sender_name = models.CharField(max_length=100, default='BusTicket Support')
    content = models.TextField()
    image = models.ImageField(upload_to='messages/', blank=True, null=True)
    is_from_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender_name} to {self.user.username}"


class Feedback(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='feedbacks/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback from {self.user.username} - {self.rating} stars"


class UserEmail(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='extra_emails'
    )

    email = models.EmailField(unique=True)
    added_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)  # Chỉ 1 email chính

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-is_primary', '-added_at']



from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

from .models import Trip  # nếu models.py chung thì bỏ dòng import này

from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from .models import Trip  # nếu Trip ở cùng file thì bỏ dòng này

class PaymentOrder(models.Model):
    STATUS_CHOICES = [
        ("pending", "Đang chờ thanh toán"),
        ("paid", "Đã thanh toán"),
        ("expired", "Hết hạn"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_orders",
    )
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True)

    seats = models.CharField(max_length=200)          # VD: "A01,A02,B03"
    amount = models.IntegerField()                    # tổng tiền (đ)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    ticket_code = models.CharField(max_length=20, unique=True)  # dùng để nhét vào nội dung chuyển khoản / addInfo
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    from_location = models.CharField(max_length=100, blank=True)
    to_location = models.CharField(max_length=100, blank=True)
    depart_date = models.CharField(max_length=20, blank=True)  # vd: 27-11
    depart_time = models.CharField(max_length=10, blank=True)
    # ví dụ: "27-11 06:32"
    price_each = models.IntegerField(default=0)
    def __str__(self):
        return f"{self.ticket_code} - {self.user.username} - {self.status}"

    @property
    def is_expired(self):
        # hết hạn sau 5 phút
        return self.created_at + timedelta(minutes=5) < timezone.now()
