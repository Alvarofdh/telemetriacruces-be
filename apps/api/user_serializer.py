"""
Serializer adicional para gestión completa de usuarios (solo admins)
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile


class UserManagementSerializer(serializers.ModelSerializer):
	"""Serializer para gestión completa de usuarios (solo admins)"""
	profile = serializers.SerializerMethodField()
	role = serializers.CharField(write_only=True, required=False)
	role_display = serializers.CharField(source='profile.get_role_display', read_only=True)
	full_name = serializers.SerializerMethodField()
	
	class Meta:
		model = User
		fields = (
			'id', 'username', 'email', 'first_name', 'last_name', 
			'full_name', 'is_active', 'date_joined', 'last_login',
			'profile', 'role', 'role_display'
		)
		read_only_fields = ('id', 'date_joined', 'last_login', 'username')
	
	def get_profile(self, obj):
		"""Obtener datos del perfil"""
		try:
			profile = obj.profile
			return {
				'role': profile.role,
				'role_display': profile.get_role_display(),
				'created_at': profile.created_at,
				'updated_at': profile.updated_at,
			}
		except:
			return None
	
	def get_full_name(self, obj):
		"""Obtener nombre completo del usuario"""
		if obj.first_name or obj.last_name:
			return f"{obj.first_name} {obj.last_name}".strip()
		return obj.username
	
	def update(self, instance, validated_data):
		"""Actualizar usuario y perfil"""
		role = validated_data.pop('role', None)
		
		# Actualizar campos del usuario
		instance.email = validated_data.get('email', instance.email)
		instance.first_name = validated_data.get('first_name', instance.first_name)
		instance.last_name = validated_data.get('last_name', instance.last_name)
		instance.is_active = validated_data.get('is_active', instance.is_active)
		instance.save()
		
		# Actualizar rol si se proporciona
		if role:
			try:
				profile = instance.profile
				profile.role = role
				profile.save()
			except UserProfile.DoesNotExist:
				# Si no tiene perfil, crearlo
				UserProfile.objects.create(user=instance, role=role)
		
		return instance


class UserUpdateSerializer(serializers.ModelSerializer):
	"""Serializer para actualizar usuario (campos específicos)"""
	role = serializers.CharField(write_only=True, required=False)
	
	class Meta:
		model = User
		fields = ('email', 'first_name', 'last_name', 'is_active', 'role')
	
	def update(self, instance, validated_data):
		"""Actualizar usuario"""
		role = validated_data.pop('role', None)
		
		# Actualizar campos del usuario
		for attr, value in validated_data.items():
			setattr(instance, attr, value)
		instance.save()
		
		# Actualizar rol si se proporciona
		if role:
			try:
				profile = instance.profile
				profile.role = role
				profile.save()
			except UserProfile.DoesNotExist:
				UserProfile.objects.create(user=instance, role=role)
		
		return instance

