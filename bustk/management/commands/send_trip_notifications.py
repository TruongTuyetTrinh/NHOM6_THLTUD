from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from bustk.models import Ticket, Notification  # đổi bustk thành tên app của bạn


class Command(BaseCommand):
    help = "Gửi thông báo chuyến đi (30 phút trước, đang khởi hành, đã hoàn thành)"

    def handle(self, *args, **options):
        now = timezone.now()

        # 1) Nhắc trước 30 phút
        reminder_start = now + timedelta(minutes=29)
        reminder_end   = now + timedelta(minutes=31)

        tickets_reminder = Ticket.objects.filter(
            status='upcoming',
            trip__departure_time__range=(reminder_start, reminder_end),
            reminder_30m_sent=False
        )

        for t in tickets_reminder:
            Notification.objects.create(
                user=t.user,
                ticket=t,
                trip=t.trip,
                type=Notification.Type.TRIP_REMINDER,
                title='Chuyến xe sắp khởi hành',
                body=f'Chuyến {t.trip.departure_location} → {t.trip.arrival_location} '
                     f'sẽ khởi hành lúc {t.trip.departure_time:%H:%M}.'
            )
            t.reminder_30m_sent = True
            t.save(update_fields=['reminder_30m_sent'])

        # 2) Đang khởi hành
        start_start = now - timedelta(minutes=1)
        start_end   = now + timedelta(minutes=1)

        tickets_start = Ticket.objects.filter(
            status='upcoming',
            trip__departure_time__range=(start_start, start_end),
            started_notified=False
        )

        for t in tickets_start:
            Notification.objects.create(
                user=t.user,
                ticket=t,
                trip=t.trip,
                type=Notification.Type.TRIP_START,
                title='Chuyến xe đang khởi hành',
                body=f'Chuyến {t.trip.departure_location} → {t.trip.arrival_location} '
                     f'đã bắt đầu khởi hành.'
            )
            t.started_notified = True
            t.save(update_fields=['started_notified'])

        # 3) Đã hoàn thành
        tickets_completed = Ticket.objects.filter(
            status='completed',
            completed_notified=False,
            trip__departure_time__lte=now
        )

        for t in tickets_completed:
            Notification.objects.create(
                user=t.user,
                ticket=t,
                trip=t.trip,
                type=Notification.Type.TRIP_COMPLETED,
                title='Chuyến xe đã hoàn thành',
                body=f'Chuyến {t.trip.departure_location} → {t.trip.arrival_location} '
                     f'đã hoàn thành. Cảm ơn bạn đã đồng hành cùng DaNaGo!'
            )
            t.completed_notified = True
            t.save(update_fields=['completed_notified'])

        self.stdout.write(self.style.SUCCESS("Đã xử lý thông báo tự động"))
