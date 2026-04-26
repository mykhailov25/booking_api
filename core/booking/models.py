from datetime import timedelta

from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models

class UserManager(BaseUserManager):#кастомный юзер менеджер
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    first_name = models.CharField(max_length=30, blank=False, null=False)
    last_name = models.CharField(max_length=30, blank=False, null=False)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=13, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    username = None
    USERNAME_FIELD = 'email'  # Вместо юзернейма используем эмейл
    REQUIRED_FIELDS = []
    objects = UserManager()

    ROLE_CHOICES = (  # Создаем роль для юзера: или Специалист или Клиент
        ('SP', 'Specialist'),
        ('CL', 'Client'),
    )

    role = models.CharField(  # Выбираем роль
        max_length=2,
        choices=ROLE_CHOICES,
        default='CL'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} - {self.phone_number}'


class Service(models.Model):  # Модель для услуг от Специалистов
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(decimal_places=2, max_digits=10)
    estimated_time = models.DurationField(default=timedelta(minutes=60))  # занимаемое время услуги, по дефолту 60 минут
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} - {self.description[:30]}'


class SpecialistProfile(
    models.Model):  # модель в которой мы добавляем описание для мастера и какие услуги могут быть от него
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='specialist_profiles')
    description = models.TextField(blank=True, null=True, )
    services = models.ManyToManyField(Service, related_name='specialists', blank=True)

    def __str__(self):
        return f'Мастер: {self.user.first_name}'


class WorkingHours(models.Model):  # модель чтобы определять когда Специалист работет
    specialist = models.ForeignKey(SpecialistProfile, on_delete=models.CASCADE)
    WORKDAYS_CHOICES = (
        (1, "Понедельник",),
        (2, "Вторник",),
        (3, "Среда",),
        (4, "Четверг",),
        (5, "Пятница",),
        (6, "Суббота",),
        (7, "Воскресенье",),
    )
    workdays = models.PositiveIntegerField(choices=WORKDAYS_CHOICES, )  # выбираем рабочие дни
    from_hour = models.TimeField()  # со скольки работаем
    to_hour = models.TimeField()  # до скольки работаем

    class Meta:
        unique_together = ('specialist', 'workdays', 'from_hour')
        ordering = ['workdays', 'from_hour']

    def __str__(self):
        return f'{self.specialist.user.first_name} - {self.workdays} ({self.from_hour}-{self.to_hour})'


class Booking(models.Model):  # связуящая модель для бронирования по времени между специалистом(его услугой) и клиентом
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_booking',
        limit_choices_to={'role': 'CL'}
    )
    specialist = models.ForeignKey(
        SpecialistProfile,
        on_delete=models.CASCADE,
        related_name='specialist_booking',
    )
    STATUS_CHOICES = (  # Статусы бронирования
        ('PE', 'Ожидает подтверджения'),
        ('CO', "Подтверждён"),
        ('DO', "Завершён"),
        ('CA', "Отменён")
    )

    status = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        default='PE'
    )

    service = models.ForeignKey(Service, on_delete=models.CASCADE, )  # какая именно услуга
    start_time = models.DateTimeField()  # на сколько бронируем
    created_at = models.DateTimeField(auto_now_add=True)

    @property  # вычисляем и не храним когда закончится услуга
    def end_time(self):
        return self.start_time + self.service.estimated_time

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"

    def __str__(self):
        return (f'{self.client.first_name}'
                f'к {self.specialist.user.first_name} {self.specialist.user.last_name} '
                f'на {self.service.name} ({self.start_time.strftime("%d.%m %H:%M")})')


