from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ObjectDoesNotExist
from rest_framework_simplejwt.tokens import RefreshToken

class UserSerializer(serializers.ModelSerializer):
    """Serializer para el modelo User de Django"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'date_joined')

class LoginSerializer(serializers.Serializer):
    """Serializer para el login con email"""
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Buscar usuario por email
            try:
                user = User.objects.get(email=email)
                # Autenticar con username (Django usa username para authenticate)
                user = authenticate(username=user.username, password=password)
                if not user:
                    raise serializers.ValidationError('Credenciales inválidas')
                if not user.is_active:
                    raise serializers.ValidationError('Usuario inactivo')
            except ObjectDoesNotExist:
                raise serializers.ValidationError('Email no encontrado')
        else:
            raise serializers.ValidationError('Debe proporcionar email y password')

        attrs['user'] = user
        return attrs

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuarios con email"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        
        # Verificar que el email no esté en uso
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        
        # Generar username desde el email
        email = validated_data['email']
        username = email.split('@')[0]  # Tomar la parte antes del @
        
        # Si el username ya existe, agregar números
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Crear usuario con username generado
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        return user

class TokenSerializer(serializers.Serializer):
    """Serializer para tokens JWT"""
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer() 