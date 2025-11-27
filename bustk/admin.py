# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser, Trip, Ticket, Notification, Message,
    Feedback, UserEmail, PaymentOrder
)


# ==================== CUSTOM USER ====================
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'phone', 'role', 'is_staff', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active', 'gender']
    search_fields = ['username', 'email', 'phone', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('phone', 'birthday', 'gender', 'address', 'role')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('phone', 'birthday', 'gender', 'address', 'role')
        }),
    )


# ==================== TRIP (CHUYẾN XE) ====================
@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'departure_location',
        'arrival_location',
        'departure_time',
        'vehicle_type',
        'price',
        'total_seats',
        'get_available_seats'
    ]
    list_filter = ['vehicle_type', 'departure_location', 'arrival_location', 'departure_time']
    search_fields = ['departure_location', 'arrival_location']
    ordering = ['-departure_time']
    date_hierarchy = 'departure_time'

    fieldsets = (
        ('Thông tin chuyến đi', {
            'fields': ('departure_location', 'arrival_location', 'departure_time', 'arrival_time')
        }),
        ('Thông tin xe', {
            'fields': ('vehicle_type', 'total_seats', 'price')
        }),
    )

    def get_available_seats(self, obj):
        return obj.available_seats

    get_available_seats.short_description = 'Ghế trống'

    # Thêm màu cho số ghế trống
    def get_available_seats(self, obj):
        available = obj.available_seats
        if available == 0:
            return f'❌ {available}'
        elif available < 10:
            return f'⚠️ {available}'
        else:
            return f'✅ {available}'

    get_available_seats.short_description = 'Ghế trống'


# ==================== TICKET (VÉ) ====================
@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_ticket_code',
        'user',
        'get_trip_info',
        'seat_number',
        'status',
        'booking_date',
        'get_payment_status'
    ]
    list_filter = ['status', 'booking_date', 'trip__departure_location', 'trip__arrival_location']
    search_fields = ['user__username', 'user__email', 'seat_number', 'payment_order__ticket_code']
    ordering = ['-booking_date']
    date_hierarchy = 'booking_date'
    raw_id_fields = ['user', 'trip', 'payment_order']

    fieldsets = (
        ('Thông tin vé', {
            'fields': ('user', 'trip', 'seat_number', 'status')
        }),
        ('Thanh toán', {
            'fields': ('payment_order', 'booking_date')
        }),
    )

    readonly_fields = ['booking_date']

    def get_ticket_code(self, obj):
        if obj.payment_order:
            return obj.payment_order.ticket_code
        return '-'

    get_ticket_code.short_description = 'Mã vé'

    def get_trip_info(self, obj):
        # Nếu có trip thì ưu tiên dùng trip
        if obj.trip:
            return f"{obj.trip.departure_location} → {obj.trip.arrival_location}"

        # Nếu không có trip nhưng có payment_order thì fallback sang từ đơn hàng
        if obj.payment_order and obj.payment_order.from_location:
            to_loc = obj.payment_order.to_location or ""
            return f"{obj.payment_order.from_location} → {to_loc}"

        return "-"

    get_trip_info.short_description = 'Tuyến đường'

    def get_payment_status(self, obj):
        if obj.payment_order:
            if obj.payment_order.status == 'paid':
                return '✅ Đã thanh toán'
            elif obj.payment_order.status == 'pending':
                return '⏳ Chờ thanh toán'
            else:
                return '❌ Hết hạn'
        return '❓ Không có'

    get_payment_status.short_description = 'Thanh toán'

    # Action: Đánh dấu vé đã đi
    actions = ['mark_as_completed', 'mark_as_cancelled']

    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'Đã đánh dấu {updated} vé là "Đã đi"')

    mark_as_completed.short_description = 'Đánh dấu đã đi'

    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'Đã hủy {updated} vé')

    mark_as_cancelled.short_description = 'Hủy vé'


# ==================== PAYMENT ORDER (ĐỘN THANH TOÁN) ====================
@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_code',
        'user',
        'get_trip_info',
        'seats',
        'amount',
        'status',
        'created_at',
        'paid_at',
        'get_expired_status'
    ]
    list_filter = ['status', 'created_at', 'paid_at']
    search_fields = ['ticket_code', 'user__username', 'user__email', 'seats']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user', 'trip']

    fieldsets = (
        ('Thông tin đơn hàng', {
            'fields': ('ticket_code', 'user', 'trip', 'seats', 'amount')
        }),
        ('Trạng thái', {
            'fields': ('status', 'created_at', 'paid_at')
        }),
    )

    readonly_fields = ['ticket_code', 'created_at']

    def get_trip_info(self, obj):
        if obj.trip:
            return f"{obj.trip.departure_location} → {obj.trip.arrival_location}"
        return '-'

    get_trip_info.short_description = 'Chuyến đi'

    def get_expired_status(self, obj):
        if obj.status == 'paid':
            return '✅ Đã thanh toán'
        elif obj.is_expired and obj.status == 'pending':
            return '⏰ Hết hạn'
        else:
            return '⏳ Còn hiệu lực'

    get_expired_status.short_description = 'Trạng thái'

    # Action: Đánh dấu đã thanh toán
    actions = ['mark_as_paid', 'mark_as_expired']

    def mark_as_paid(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='paid', paid_at=timezone.now())
        self.message_user(request, f'Đã đánh dấu {updated} đơn là "Đã thanh toán"')

    mark_as_paid.short_description = 'Đánh dấu đã thanh toán'

    def mark_as_expired(self, request, queryset):
        updated = queryset.update(status='expired')
        self.message_user(request, f'Đã đánh dấu {updated} đơn là "Hết hạn"')

    mark_as_expired.short_description = 'Đánh dấu hết hạn'


# ==================== NOTIFICATION (THÔNG BÁO) ====================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']

    fieldsets = (
        ('Thông tin thông báo', {
            'fields': ('user', 'title', 'message')
        }),
        ('Trạng thái', {
            'fields': ('is_read', 'created_at')
        }),
    )

    readonly_fields = ['created_at']

    actions = ['mark_as_read']

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'Đã đánh dấu {updated} thông báo là đã đọc')

    mark_as_read.short_description = 'Đánh dấu đã đọc'


# ==================== MESSAGE (TIN NHẮN) ====================
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'sender_name', 'get_content_preview', 'is_from_user', 'created_at']
    list_filter = ['is_from_user', 'created_at']
    search_fields = ['user__username', 'sender_name', 'content']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user']

    fieldsets = (
        ('Thông tin tin nhắn', {
            'fields': ('user', 'sender_name', 'content', 'is_from_user')
        }),
        ('Thời gian', {
            'fields': ('created_at',)
        }),
    )

    readonly_fields = ['created_at']

    def get_content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content

    get_content_preview.short_description = 'Nội dung'


# ==================== FEEDBACK (ĐÁNH GIÁ) ====================
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'get_trip_info', 'rating', 'title', 'created_at']
    list_filter = ['rating', 'created_at', 'trip__departure_location']
    search_fields = ['user__username', 'title', 'content']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    raw_id_fields = ['user', 'trip']

    fieldsets = (
        ('Thông tin đánh giá', {
            'fields': ('user', 'trip', 'rating', 'title', 'content', 'image')
        }),
        ('Thời gian', {
            'fields': ('created_at',)
        }),
    )

    readonly_fields = ['created_at']

    def get_trip_info(self, obj):
        return f"{obj.trip.departure_location} → {obj.trip.arrival_location}"

    get_trip_info.short_description = 'Chuyến đi'


# ==================== USER EMAIL (EMAIL PHỤ) ====================
@admin.register(UserEmail)
class UserEmailAdmin(admin.ModelAdmin):
    list_display = ['email', 'user', 'is_primary', 'added_at']
    list_filter = ['is_primary', 'added_at']
    search_fields = ['email', 'user__username']
    ordering = ['-is_primary', '-added_at']
    raw_id_fields = ['user']

    fieldsets = (
        ('Thông tin email', {
            'fields': ('user', 'email', 'is_primary')
        }),
        ('Thời gian', {
            'fields': ('added_at',)
        }),
    )

    readonly_fields = ['added_at']

