from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer

User = get_user_model()


class UserRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'password')

    def validate_email(self, value):
        lower_email = value.lower()
        if User.objects.filter(email__iexact=lower_email).exists():
            raise serializers.ValidationError("Юзер с такой почтой уже зарегистрирован.")
        return value
    #ручное создание + сет_пассворд
    def create(self, validated_data):
        email = validated_data['email'].lower()
        password = validated_data['password']

        user = User.objects.create_user(
            email=email,
            password=password,
        )
        user.set_password(password)
        user.save()

        return user
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    pass


class MyTokenRefreshSerializer(TokenRefreshSerializer):
    pass
