from django.db.models import F, ExpressionWrapper, DateTimeField
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

from .models import User, Service, Booking, WorkingHours


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'phone_number', 'created_at', 'role')
        read_only_fields = ('id', 'created_at', 'role')


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'name', 'price', 'estimated_time', 'created_at',)
        read_only_fields = ('id', 'created_at', 'price',)


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('id', 'specialist', 'client', 'service', 'start_time', 'status', 'created_at',)
        read_only_fields = ('id', 'client', 'status', 'created_at',)

    def validate_start_time(self, value):
        if value < timezone.now():
            raise serializers.ValidationError('Нельзя забронировать в прошлом.')
        return value

    def validate_specialist(self, value):
        if value.user.role != 'SP':
            raise serializers.ValidationError('Это не специалист!')
        return value

    def validate(self, data):
        specialist = data.get('specialist')
        service = data.get('service')
        start_time = data.get('start_time')

        # если это ПАТЧ и эти поля не меняются
        if self.instance:
            specialist = self.instance.specialist or specialist
            service = self.instance.service or service
            start_time = self.instance.start_time or start_time
        # если чего то не хватает то ДРФ выкинет ошибку по отдельным полям,
        # защита от edge case-ов например start_time = None
        if not all([specialist, service, start_time]):
            return data


        end_time = start_time + service.estimated_time
        #считаем end_time прямо в запросе
        overlaping_bookings = (Booking.objects.annotate(
            end_time=ExpressionWrapper(
                F('start_time') + F('service__estimated_time'),
                output_field=DateTimeField()
            )
        ).filter(        # Проверка пересечений бронирования
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time),  # сама формула пересечения
            specialist=specialist,  # текущий специалист
            status__in=['PE', 'CO'],  # ищем только среди активных броней
        ).exclude(id=self.instance.id if self.instance else None))  # исключаем текущую бронь при обновлении
        if overlaping_bookings.exists():
            raise serializers.ValidationError("На это время у специалиста есть другая бронь")

        # проверка имеет ли этот специалист данную услугу
        if not specialist.services.filter(id=service.id).exists():
            raise serializers.ValidationError(
                f"Специалист {specialist.user.first_name} не оказывает услугу {service.name}."
            )

        # проверка - работает ли специалист в этот день + учитываем его график
        weekday = start_time.weekday() + 1  # день недели из модели +1 (В пайтоне 0-6, в нашей модели 1-7)
        booking_start_time = start_time.time()
        booking_end_time = end_time.time()

        # ищем рабочие часы
        work_hours = WorkingHours.objects.filter(
            specialist=specialist,
            workdays=weekday,
        ).first()

        # если записи нет - выходной
        if not work_hours:
            raise serializers.ValidationError("Специалист не работает в выбранный день")

        # проверяем диапозон времени
        if not (booking_start_time >= work_hours.from_hour and
                booking_end_time <= work_hours.to_hour):
            raise serializers.ValidationError(
                f'Время записи выходит за рамки рабочего графика мастера '
            )

        return data
