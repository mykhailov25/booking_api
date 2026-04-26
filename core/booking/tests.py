from django.contrib.auth import get_user_model

User = get_user_model()
from datetime import timedelta, time

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from freezegun import freeze_time

from .models import Service, WorkingHours, Booking, SpecialistProfile

User = get_user_model()


# Create your tests here.
class RegistrationTest(APITestCase):
    def test_registration_success(self):
        url = reverse('register')
        data = {
            'email': 'test@example.com',
            'password': '12345678'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.filter(email='test@example.com').exists()
        self.assertTrue(user)

    def test_registration_duplicate_email(self):
        url = reverse('register')
        data = {
            'email': 'test@example.com',
            'password': '12345678'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        user = User.objects.get(email='test@example.com')
        self.assertEqual(User.objects.count(), 1)


class LoginJWTTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='12345678',
        )
        self.url = reverse('login')

    def test_login_success(self):
        data = {
            'email': 'test@example.com',
            'password': '12345678'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        data = {
            'email': 'test@example.com',
            'password': 'wrong_password'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BookingTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='client@mail.com',
            password='12345678',
        )

        self.user_specialist = User.objects.create_user(
            email='specialist@mail.com',
            password='12345678',
            role='SP',
        )

        self.specialist_profile = SpecialistProfile.objects.create(
            user=self.user_specialist
        )

        self.service = Service.objects.create(
            name='Test Service',
            description='Test Service Description',
            price=100,
            estimated_time=timedelta(minutes=60),
        )

        self.specialist_profile.services.add(self.service)

        self.working_hours = WorkingHours.objects.create(
            specialist=self.specialist_profile,
            workdays=1,
            from_hour=time(9, 0),
            to_hour=time(18, 0),
        )

    @freeze_time("2026-04-20 12:00:00")
    def test_booking_success(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('booking-list')

        data = {
            "specialist": self.specialist_profile.id,
            "service": self.service.id,
            "start_time": "2026-04-20T14:00:00Z",
        }

        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Booking.objects.count(), 1)

        booking = Booking.objects.first()
        self.assertEqual(booking.client, self.user)
        self.assertEqual(booking.specialist, self.specialist_profile)

    @freeze_time("2026-04-20 12:00:00")
    def test_booking_in_past(self):
        self.client.force_authenticate(user=self.user)

        url = reverse('booking-list')

        data = {
            "specialist": self.specialist_profile.id,
            "service": self.service.id,
            "start_time": "2026-03-20T14:00:00Z", #старт тайм в прошлом
        }

        response = self.client.post(url, data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(Booking.objects.count(), 0)

