from django.urls import path, include
from rest_framework.routers import DefaultRouter


from .views import BookingViewSet
from users import views

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/register/", views.UserRegisterView.as_view(), name="register"),
    path("api/auth/login/", views.MyTokenObtainPairView.as_view(), name="login"),
    path("api/auth/refresh/", views.TokenRefreshView.as_view(), name="refresh"),
    path("api-auth/", include("rest_framework.urls", )),
]
