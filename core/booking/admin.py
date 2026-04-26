from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Booking, Service

User = get_user_model()


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'role', 'created_at',)
    search_fields = ('email', 'last_name', 'phone_number')
    list_filter = ('role',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_description', 'price', 'estimated_time', 'created_at',)
    search_fields = ('name', 'price', 'estimated_time', 'created_at')
    list_filter = ('name', 'price',)

    def short_description(self, obj):
        return obj.description[:20]


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'specialist_name', 'status', 'service', 'start_time', 'created_at')
    search_fields = (
        'client__first_name',
        'client__last_name',
        'specialist__user__first_name',
        'specialist__user__last_name',
        'service__name',
    )
    list_filter = ('status', 'service', 'start_time')

    def client_name(self, obj):
        return f"{obj.client.first_name} {obj.client.last_name}"

    def specialist_name(self, obj):
        return f"{obj.specialist.user.first_name} {obj.specialist.user.last_name}"
