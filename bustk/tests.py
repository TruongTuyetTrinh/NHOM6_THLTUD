from random import random

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction


from busticket.bustk.views import otp_storage


class AuthTest(TestCase):
    def test_verify_otp_success(self):
        otp_storage['test@example.com'] = '123456'
        with transaction.atomic():
            User.objects.create_user(
                username='testuser',
                email='test@example.com',
                password='strongpass123',
                first_name='Test'
            )
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_concurrent_create(self):
        # Test concurrent (giả lập)
        from concurrent.futures import ThreadPoolExecutor
        def create_user():
            with transaction.atomic():
                User.objects.create_user(username=f'user_{random.randint(1,100)}', email='concurrent@test.com', password='pass123')
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(create_user, range(5))
        self.assertEqual(User.objects.count(), 5)  # Không lỗi lock