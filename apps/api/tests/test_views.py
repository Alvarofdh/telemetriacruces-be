"""
Tests para las vistas de la API
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.api.models import (
	Cruce, Sensor, Telemetria, Alerta, BarrierEvent,
	UserProfile, MantenimientoPreventivo, HistorialMantenimiento
)
from django.utils import timezone
from datetime import timedelta


class TelemetriaAPITestCase(TestCase):
	"""Tests para endpoints de telemetría"""
	
	def setUp(self):
		"""Configurar datos de prueba"""
		self.client = APIClient()
		
		# Crear usuario de prueba
		self.user = User.objects.create_user(
			username='testuser',
			email='test@test.com',
			password='testpass123456'
		)
		UserProfile.objects.create(user=self.user, role='OBSERVER')
		
		# Crear cruce de prueba
		self.cruce = Cruce.objects.create(
			nombre='Cruce Test',
			ubicacion='Ubicación Test',
			estado='ACTIVO'
		)
	
	def test_crear_telemetria(self):
		"""Test crear telemetría"""
		self.client.force_authenticate(user=self.user)
		
		data = {
			'cruce': self.cruce.id,
			'barrier_voltage': 3.3,
			'battery_voltage': 12.5,
			'sensor_1': 500,
			'signal_strength': -45,
			'temperature': 25.0
		}
		
		response = self.client.post('/api/telemetria/', data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Telemetria.objects.count(), 1)
	
	def test_telemetria_crea_evento_barrera(self):
		"""Test que la telemetría crea eventos de barrera automáticamente"""
		self.client.force_authenticate(user=self.user)
		
		# Crear telemetría con barrera abajo
		data = {
			'cruce': self.cruce.id,
			'barrier_voltage': 3.3,  # > 2.0V = DOWN
			'battery_voltage': 12.5
		}
		
		response = self.client.post('/api/telemetria/', data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		# Verificar que se creó un evento
		eventos = BarrierEvent.objects.filter(cruce=self.cruce)
		self.assertGreater(eventos.count(), 0)
		self.assertEqual(eventos.first().state, 'DOWN')
	
	def test_telemetria_crea_alerta_bateria_baja(self):
		"""Test que la telemetría crea alertas de batería baja"""
		self.client.force_authenticate(user=self.user)
		
		# Crear telemetría con batería baja
		data = {
			'cruce': self.cruce.id,
			'barrier_voltage': 3.3,
			'battery_voltage': 10.5  # < 11.0V = batería baja
		}
		
		response = self.client.post('/api/telemetria/', data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		# Verificar que se creó una alerta
		alertas = Alerta.objects.filter(cruce=self.cruce, type='LOW_BATTERY')
		self.assertGreater(alertas.count(), 0)
		self.assertEqual(alertas.first().severity, 'CRITICAL')


class CruceAPITestCase(TestCase):
	"""Tests para endpoints de cruces"""
	
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='admin',
			email='admin@test.com',
			password='adminpass123456'
		)
		UserProfile.objects.create(user=self.user, role='ADMIN')
		self.client.force_authenticate(user=self.user)
	
	def test_listar_cruces(self):
		"""Test listar cruces"""
		Cruce.objects.create(nombre='Cruce 1', ubicacion='Ubicación 1', estado='ACTIVO')
		Cruce.objects.create(nombre='Cruce 2', ubicacion='Ubicación 2', estado='ACTIVO')
		
		response = self.client.get('/api/cruces/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(len(response.data.get('results', [])), 2)
	
	def test_crear_cruce(self):
		"""Test crear cruce (solo admin)"""
		data = {
			'nombre': 'Nuevo Cruce',
			'ubicacion': 'Nueva Ubicación',
			'estado': 'ACTIVO'
		}
		
		response = self.client.post('/api/cruces/', data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Cruce.objects.filter(nombre='Nuevo Cruce').count(), 1)


class MantenimientoPreventivoTestCase(TestCase):
	"""Tests para mantenimiento preventivo"""
	
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='admin',
			email='admin@test.com',
			password='adminpass123456'
		)
		UserProfile.objects.create(user=self.user, role='ADMIN')
		self.client.force_authenticate(user=self.user)
		
		self.cruce = Cruce.objects.create(
			nombre='Cruce Test',
			ubicacion='Ubicación Test',
			estado='ACTIVO'
		)
	
	def test_crear_regla_mantenimiento(self):
		"""Test crear regla de mantenimiento"""
		data = {
			'nombre': 'Test Regla',
			'tipo_mantenimiento': 'BATERIA',
			'prioridad': 'ALTA',
			'condiciones': {
				'battery_voltage': {
					'operator': 'lt',
					'value': 11.5
				}
			},
			'acciones': {
				'dias_anticipacion': 7
			},
			'activo': True
		}
		
		response = self.client.post('/api/mantenimiento-preventivo/', data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(MantenimientoPreventivo.objects.filter(nombre='Test Regla').count(), 1)
	
	def test_mantenimiento_se_genera_automaticamente(self):
		"""Test que se genera mantenimiento cuando se cumplen condiciones"""
		# Crear regla
		regla = MantenimientoPreventivo.objects.create(
			nombre='Test Regla',
			tipo_mantenimiento='BATERIA',
			prioridad='ALTA',
			condiciones={
				'battery_voltage': {
					'operator': 'lt',
					'value': 11.5
				}
			},
			acciones={'dias_anticipacion': 7},
			activo=True
		)
		
		# Crear telemetría que cumple condiciones
		telemetria = Telemetria.objects.create(
			cruce=self.cruce,
			barrier_voltage=3.3,
			battery_voltage=11.0  # < 11.5
		)
		
		# Importar y ejecutar motor de mantenimiento
		from apps.api.mantenimiento_engine import motor_mantenimiento
		mantenimientos = motor_mantenimiento.evaluar_telemetria(telemetria)
		
		# Verificar que se creó un mantenimiento
		self.assertGreater(len(mantenimientos), 0)
		mantenimiento = mantenimientos[0]
		self.assertEqual(mantenimiento.cruce, self.cruce)
		self.assertEqual(mantenimiento.estado, 'PENDIENTE')


class AlertaAPITestCase(TestCase):
	"""Tests para endpoints de alertas"""
	
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='testuser',
			email='test@test.com',
			password='testpass123456'
		)
		UserProfile.objects.create(user=self.user, role='OBSERVER')
		self.client.force_authenticate(user=self.user)
		
		self.cruce = Cruce.objects.create(
			nombre='Cruce Test',
			ubicacion='Ubicación Test',
			estado='ACTIVO'
		)
	
	def test_listar_alertas(self):
		"""Test listar alertas"""
		Alerta.objects.create(
			type='LOW_BATTERY',
			severity='CRITICAL',
			description='Batería baja',
			cruce=self.cruce,
			resolved=False
		)
		
		response = self.client.get('/api/alertas/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(len(response.data.get('results', [])), 1)
	
	def test_marcar_alerta_resuelta(self):
		"""Test marcar alerta como resuelta (solo admin)"""
		# Cambiar a admin
		self.user.profile.role = 'ADMIN'
		self.user.profile.save()
		
		alerta = Alerta.objects.create(
			type='LOW_BATTERY',
			severity='CRITICAL',
			description='Batería baja',
			cruce=self.cruce,
			resolved=False
		)
		
		response = self.client.patch(
			f'/api/alertas/{alerta.id}/',
			{'resolved': True},
			format='json'
		)
		
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		alerta.refresh_from_db()
		self.assertTrue(alerta.resolved)

