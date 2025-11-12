"""
Comando para realizar un test completo de todas las funcionalidades del proyecto
"""
from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.api.models import (
	Cruce, Sensor, Telemetria, Alerta, BarrierEvent,
	UserProfile, MantenimientoPreventivo, HistorialMantenimiento,
	MetricasDesempeno
)
from django.utils import timezone
from datetime import timedelta
import json


class Command(BaseCommand):
	help = 'Realizar test completo de todas las funcionalidades del proyecto'

	def add_arguments(self, parser):
		parser.add_argument(
			'--verbose',
			action='store_true',
			help='Mostrar información detallada',
		)

	def handle(self, *args, **options):
		verbose = options['verbose']
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🧪 TEST COMPLETO DEL SISTEMA'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

		errores = []
		exitosos = []

		# ============================================
		# 1. VERIFICACIÓN DE MODELOS
		# ============================================
		self.stdout.write(self.style.WARNING('\n📦 1. VERIFICACIÓN DE MODELOS'))
		try:
			# Verificar que todos los modelos se pueden instanciar
			cruce = Cruce(nombre='Test Cruce', ubicacion='Test Ubicación', estado='ACTIVO')
			cruce.save()
			exitosos.append('Modelo Cruce')
			
			# Verificar relaciones
			telemetria = Telemetria(
				cruce=cruce,
				barrier_voltage=3.3,
				battery_voltage=12.5
			)
			telemetria.save()
			exitosos.append('Modelo Telemetria')
			
			alerta = Alerta(
				cruce=cruce,
				type='LOW_BATTERY',
				severity='CRITICAL',
				description='Test alerta',
				resolved=False
			)
			alerta.save()
			exitosos.append('Modelo Alerta')
			
			# Limpiar datos de prueba
			telemetria.delete()
			alerta.delete()
			cruce.delete()
			
			self.stdout.write(self.style.SUCCESS('  ✅ Todos los modelos funcionan correctamente'))
		except Exception as e:
			errores.append(f'Modelos: {str(e)}')
			self.stdout.write(self.style.ERROR(f'  ❌ Error en modelos: {str(e)}'))

		# ============================================
		# 2. VERIFICACIÓN DE API ENDPOINTS
		# ============================================
		self.stdout.write(self.style.WARNING('\n🌐 2. VERIFICACIÓN DE API ENDPOINTS'))
		
		# Crear usuario de prueba
		try:
			test_user, created = User.objects.get_or_create(
				username='test_api',
				defaults={
					'email': 'test@test.com',
					'password': 'pbkdf2_sha256$600000$test$test',
					'is_active': True
				}
			)
			if created:
				test_user.set_password('TestPassword123456!')
				test_user.save()
				UserProfile.objects.get_or_create(
					user=test_user,
					defaults={'role': 'ADMIN'}
				)
			
			client = APIClient()
			
			# Test login
			try:
				response = client.post('/api/login', {
					'email': 'test@test.com',
					'password': 'TestPassword123456!'
				}, format='json')
				if response.status_code == 200:
					token = response.data.get('access')
					client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
					exitosos.append('Login API')
					self.stdout.write(self.style.SUCCESS('  ✅ Login funciona'))
				else:
					errores.append(f'Login: Status {response.status_code}')
			except Exception as e:
				errores.append(f'Login: {str(e)}')
			
			# Test health check
			try:
				response = client.get('/api/health')
				if response.status_code == 200:
					exitosos.append('Health Check')
					self.stdout.write(self.style.SUCCESS('  ✅ Health check funciona'))
				else:
					errores.append(f'Health Check: Status {response.status_code}')
			except Exception as e:
				errores.append(f'Health Check: {str(e)}')
			
			# Test listar cruces
			try:
				response = client.get('/api/cruces/')
				if response.status_code == 200:
					exitosos.append('Listar Cruces')
					self.stdout.write(self.style.SUCCESS('  ✅ Listar cruces funciona'))
				else:
					errores.append(f'Listar Cruces: Status {response.status_code}')
			except Exception as e:
				errores.append(f'Listar Cruces: {str(e)}')
			
			# Test listar alertas
			try:
				response = client.get('/api/alertas/')
				if response.status_code == 200:
					exitosos.append('Listar Alertas')
					self.stdout.write(self.style.SUCCESS('  ✅ Listar alertas funciona'))
				else:
					errores.append(f'Listar Alertas: Status {response.status_code}')
			except Exception as e:
				errores.append(f'Listar Alertas: {str(e)}')
			
			# Limpiar usuario de prueba
			if created:
				test_user.delete()
				
		except Exception as e:
			errores.append(f'API Tests: {str(e)}')
			self.stdout.write(self.style.ERROR(f'  ❌ Error en tests de API: {str(e)}'))

		# ============================================
		# 3. VERIFICACIÓN DE MANTENIMIENTO PREVENTIVO
		# ============================================
		self.stdout.write(self.style.WARNING('\n🔧 3. VERIFICACIÓN DE MANTENIMIENTO PREVENTIVO'))
		try:
			from apps.api.mantenimiento_engine import motor_mantenimiento
			
			# Crear cruce de prueba
			cruce_test = Cruce.objects.create(
				nombre='Cruce Test Mantenimiento',
				ubicacion='Test',
				estado='ACTIVO'
			)
			
			# Crear regla de mantenimiento
			regla = MantenimientoPreventivo.objects.create(
				nombre='Test Regla',
				tipo_mantenimiento='BATERIA',
				prioridad='ALTA',
				condiciones=[
					{'field': 'battery_voltage', 'operator': '<', 'value': 11.5}
				],
				acciones={},
				activo=True,
				cruce=cruce_test
			)
			exitosos.append('Crear Regla Mantenimiento')
			
			# Crear telemetría que cumple condiciones
			telemetria_test = Telemetria.objects.create(
				cruce=cruce_test,
				barrier_voltage=3.3,
				battery_voltage=11.0  # < 11.5
			)
			
			# Evaluar regla
			mantenimientos = motor_mantenimiento.evaluar_telemetria(telemetria_test)
			if len(mantenimientos) > 0:
				exitosos.append('Motor Mantenimiento')
				self.stdout.write(self.style.SUCCESS('  ✅ Motor de mantenimiento funciona'))
			else:
				errores.append('Motor Mantenimiento: No generó mantenimiento')
			
			# Limpiar
			telemetria_test.delete()
			regla.delete()
			cruce_test.delete()
			
		except Exception as e:
			errores.append(f'Mantenimiento: {str(e)}')
			self.stdout.write(self.style.ERROR(f'  ❌ Error en mantenimiento: {str(e)}'))

		# ============================================
		# 4. VERIFICACIÓN DE SOCKET.IO
		# ============================================
		self.stdout.write(self.style.WARNING('\n🔌 4. VERIFICACIÓN DE SOCKET.IO'))
		try:
			from apps.api.socketio_app import sio, socketio_app
			from apps.api.socketio_utils import (
				emit_telemetria, emit_alerta, emit_barrier_event
			)
			
			# Verificar que las funciones se pueden llamar
			exitosos.append('Socket.IO Import')
			self.stdout.write(self.style.SUCCESS('  ✅ Socket.IO se importa correctamente'))
			
		except Exception as e:
			errores.append(f'Socket.IO: {str(e)}')
			self.stdout.write(self.style.ERROR(f'  ❌ Error en Socket.IO: {str(e)}'))

		# ============================================
		# 5. VERIFICACIÓN DE PERMISOS Y ROLES
		# ============================================
		self.stdout.write(self.style.WARNING('\n🔐 5. VERIFICACIÓN DE PERMISOS Y ROLES'))
		try:
			# Verificar roles disponibles
			roles = [choice[0] for choice in UserProfile.ROLE_CHOICES]
			if len(roles) == 3 and 'ADMIN' in roles and 'MAINTENANCE' in roles and 'OBSERVER' in roles:
				exitosos.append('Roles Disponibles')
				self.stdout.write(self.style.SUCCESS('  ✅ Roles configurados correctamente'))
			else:
				errores.append('Roles: No están todos los roles')
			
			# Verificar métodos de perfil
			user_test = User.objects.create_user('test_perm', 'test@perm.com', 'pass123456')
			profile = UserProfile.objects.create(user=user_test, role='ADMIN')
			
			if profile.is_admin():
				exitosos.append('Métodos de Perfil')
				self.stdout.write(self.style.SUCCESS('  ✅ Métodos de perfil funcionan'))
			else:
				errores.append('Métodos Perfil: is_admin() no funciona')
			
			user_test.delete()
			
		except Exception as e:
			errores.append(f'Permisos: {str(e)}')
			self.stdout.write(self.style.ERROR(f'  ❌ Error en permisos: {str(e)}'))

		# ============================================
		# 6. VERIFICACIÓN DE BASE DE DATOS
		# ============================================
		self.stdout.write(self.style.WARNING('\n💾 6. VERIFICACIÓN DE BASE DE DATOS'))
		try:
			from django.db import connection
			cursor = connection.cursor()
			
			# Verificar tablas principales
			tablas_requeridas = [
				'api_cruce', 'api_telemetria', 'api_alerta',
				'api_mantenimientopreventivo', 'api_historialmantenimiento',
				'api_metricasdesempeno'
			]
			
			tablas_ok = 0
			for tabla in tablas_requeridas:
				cursor.execute("""
					SELECT EXISTS (
						SELECT FROM information_schema.tables 
						WHERE table_name = %s
					)
				""", [tabla])
				if cursor.fetchone()[0]:
					tablas_ok += 1
			
			if tablas_ok == len(tablas_requeridas):
				exitosos.append('Tablas BD')
				self.stdout.write(self.style.SUCCESS(f'  ✅ Todas las tablas existen ({tablas_ok}/{len(tablas_requeridas)})'))
			else:
				errores.append(f'Tablas BD: Faltan {len(tablas_requeridas) - tablas_ok} tablas')
			
		except Exception as e:
			errores.append(f'Base de Datos: {str(e)}')
			self.stdout.write(self.style.ERROR(f'  ❌ Error en BD: {str(e)}'))

		# ============================================
		# 7. VERIFICACIÓN DE CONFIGURACIÓN
		# ============================================
		self.stdout.write(self.style.WARNING('\n⚙️  7. VERIFICACIÓN DE CONFIGURACIÓN'))
		try:
			from django.conf import settings
			
			checks = []
			
			# Verificar SECRET_KEY
			if settings.SECRET_KEY and not settings.SECRET_KEY.startswith('django-insecure'):
				checks.append('SECRET_KEY')
			
			# Verificar DEBUG
			if not settings.DEBUG:
				checks.append('DEBUG=False')
			
			# Verificar CORS
			if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
				checks.append('CORS')
			
			# Verificar JWT
			if hasattr(settings, 'SIMPLE_JWT'):
				checks.append('JWT')
			
			if len(checks) >= 3:
				exitosos.append('Configuración')
				self.stdout.write(self.style.SUCCESS(f'  ✅ Configuración correcta ({len(checks)} checks)'))
			else:
				errores.append('Configuración: Faltan configuraciones')
			
		except Exception as e:
			errores.append(f'Configuración: {str(e)}')
			self.stdout.write(self.style.ERROR(f'  ❌ Error en configuración: {str(e)}'))

		# ============================================
		# RESUMEN FINAL
		# ============================================
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE TESTS'))
		self.stdout.write(self.style.SUCCESS('='*70))
		
		self.stdout.write(f'\n✅ Tests Exitosos: {len(exitosos)}')
		if verbose:
			for test in exitosos:
				self.stdout.write(f'   ✓ {test}')
		
		if errores:
			self.stdout.write(f'\n❌ Tests con Errores: {len(errores)}')
			for error in errores:
				self.stdout.write(self.style.ERROR(f'   ✗ {error}'))
		else:
			self.stdout.write(self.style.SUCCESS('\n✅ ¡Todos los tests pasaron exitosamente!'))
		
		self.stdout.write('\n' + '='*70 + '\n')
		
		return 0 if not errores else 1

