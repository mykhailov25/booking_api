from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Booking
from .serializers import BookingSerializer


# Create your views here.

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.client == request.user


class IsSpecialistOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.specialist.user == request.user


class IsOwnerOrSpecialistOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (
                obj.client == request.user or
                obj.specialist.user == request.user
        )


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['client__name', 'specialist__name', 'service__name', 'status']
    search_fields = (
        'client__first_name',
        'client__last_name',
        'specialist__user__first_name',
        'specialist__user__last_name',
        'service__name',
        'status',
    )
    ordering_fields = ('status', 'created_at')

    def get_queryset(self):
        user = self.request.user
        queryset = Booking.objects.filter().select_related(
            'client',
            'specialist__user',
            'service'
        )
        if user.role == "CL":  # клиент видит только свои записи
            return queryset.filter(client=user)

        elif user.role == "SP":  # мастер видит только свои записи
            return queryset.filter(specialist__user=user)

        return queryset.none()  # для эйдж-кейс случая

    def perform_create(self, serializer):  # чтобы клиент записывался
        serializer.save(client=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrSpecialistOnly], url_path='booking-cancel')
    def cancel(self, request, pk=None):  # отмена своей брони клиентом или специалистом
        booking = self.get_object()
        if booking.status == "DO":
            return Response({'detail': 'Нельзя отменить завершенную бронь'}, status=status.HTTP_409_CONFLICT)
        if booking.status == "CA":
            return Response({'detail': 'Бронирование уже было отменено'}, status=status.HTTP_409_CONFLICT)
        booking.status = "CA"
        booking.save()
        return Response({'detail': 'Бронирование отменено'}, status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsSpecialistOrReadOnly], url_path='booking-confirm')
    def confirm(self, request, pk=None):  # подтверждение брони только специалистом
        booking = self.get_object()
        if booking.status == "DO":
            return Response({'detail': 'Нельзя подтвердить завершенную бронь'}, status=status.HTTP_409_CONFLICT)
        if booking.status == "CA":
            return Response({'detail': 'Бронирование уже было отменено'}, status=status.HTTP_409_CONFLICT)
        if booking.status == "CO":
            return Response({'detail': 'Бронирование уже было подтверждено'}, status=status.HTTP_409_CONFLICT)
        booking.status = "CO"
        booking.save()
        return Response({'detail': 'Бронирование подтверждено'}, status.HTTP_200_OK)

    # в будущем сделать завершение брони в зависимости од длительности услуги
    @action(detail=True, methods=['post'], permission_classes=[IsSpecialistOrReadOnly], url_path='booking-done')
    def done(self, request, pk=None):  # завершение брони только специалистом
        booking = self.get_object()
        if booking.status == "CA":
            return Response({'detail': 'Бронирование уже отменено'}, status=status.HTTP_409_CONFLICT)
        if booking.status == "CO":
            booking.status = "DO"
            booking.save()
        return Response({'detail': 'Бронирование завершено'}, status.HTTP_200_OK)
