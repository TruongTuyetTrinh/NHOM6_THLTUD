from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('send-otp/', views.send_otp_view, name='send_otp'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),

    # Main Pages
    path('', views.index, name='index'),
    path('trip-list/', views.trip_list, name='trip_list'),

    # KHÔNG có trip_id ở đây – lấy trip_id qua query (?id=123)
    path('seat-selection/', views.seat_selection, name='seat_selection'),

# Vé của tôi
    path("my-tickets/", views.my_tickets, name="my_tickets"),
    path('ticket/<int:ticket_id>/download/', views.download_ticket, name='download_ticket'),
    path('ticket/<int:ticket_id>/cancel/', views.cancel_ticket, name='cancel_ticket'),
path("ticket/<int:pk>/rebook/", views.rebook_ticket, name="rebook_ticket"),
path("ticket/<int:ticket_id>/review/", views.submit_review, name="submit_review"),
    path("route-reviews/<int:trip_id>/", views.route_reviews, name="route_reviews"),
    path("reviews/", views.my_reviews_entry, name="my_reviews_entry"),

    path('schedules/', views.schedules, name='schedules'),

    # Thanh toán
    path('payment/', views.payment, name='payment'),
    path('payment/status/<str:ticket_code>/', views.payment_status, name='payment_status'),
    path('casso-webhook/', views.casso_webhook, name='casso_webhook'),

    # User Features
    path('notifications/', views.notifications_list, name='notifications'),
    path("messages/", views.message_list, name="message_list"),

    # Gửi tin nhắn qua AJAX
    path("messages/send/", views.send_message, name="send_message"),

    # Lấy tin nhắn qua AJAX (polling)
    path("messages/get/", views.get_messages, name="get_messages"),

    # Xóa tin nhắn
    path("messages/delete/<int:message_id>/", views.delete_message, name="delete_message"),


    path('logout/', views.logout_view, name='logout'),

    path('search/', views.search_trips, name='search_trips'),

    path('notification-settings/', views.notification_settings, name='notification_settings'),
    path('profile-settings/', views.profile_settings, name='profile_settings'),

    # API lấy ghế đã đặt – trip_id NẰM Ở ĐÂY
    path("api/trip/<int:trip_id>/seats/", views.get_booked_seats, name="api_trip_seats"),
]
