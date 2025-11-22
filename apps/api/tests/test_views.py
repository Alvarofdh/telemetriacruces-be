"""
Tests para las vistas de la API
"""
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from apps.api.models import (
	Cruce, Sensor, Telemetria, Alerta, BarrierEvent,
	UserProfile, MantenimientoPreventivo, HistorialMantenimiento, MetricasDesempeno
)
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch


def obtener_usuario_existente(email, rol_esperado):
	try:
		usuario = User.objects.get(email=email)
	except User.DoesNotExist:
		raise AssertionError(f"Debe existir un usuario con email {email} antes de ejecutar estos tests")
	
	try:
		perfil = usuario.profile
	except UserProfile.DoesNotExist:
		raise AssertionError(f"El usuario {email} requiere un UserProfile con rol {rol_esperado}")
	
	if perfil.role != rol_esperado:
		raise AssertionError(f"El usuario {email} debe tener rol {rol_esperado} (actual: {perfil.role})")
	
	return usuario


class TelemetriaAPITestCase(TestCase):
	"""Tests para endpoints de telemetría"""
	
	@classmethod
	def setUpTestData(cls):
		cls.admin_user = obtener_usuario_existente('admin@test.com', 'ADMIN')
		cls.maintenance_user = obtener_usuario_existente('mantenimiento@test.com', 'MAINTENANCE')
		cls.observer_user = obtener_usuario_existente('observador@test.com', 'OBSERVER')
		
		cls.cruce = Cruce.objects.create(
			nombre='Cruce Test',
			ubicacion='Ubicación Test',
			estado='ACTIVO'
		)
	
	def setUp(self):
		self.client = APIClient()
		self.user = self.__class__.observer_user
		self.cruce = self.__class__.cruce
	
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
	
	def test_telemetria_con_sensores_detecta_gabinete(self):
		"""Verifica que los valores de sensores se guarden y disparen alertas"""
		self.client.force_authenticate(user=self.user)
		
		data = {
			'cruce': self.cruce.id,
			'barrier_voltage': 3.3,
			'battery_voltage': 12.2,
			'sensor_1': 800,  # > 500 debe generar alerta de gabinete abierto
			'sensor_2': 300,
			'sensor_3': 123,
			'sensor_4': 0
		}
		
		response = self.client.post('/api/telemetria/', data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		
		telemetria = Telemetria.objects.get(cruce=self.cruce)
		self.assertEqual(telemetria.sensor_1, 800)
		self.assertEqual(telemetria.sensor_2, 300)
		self.assertEqual(telemetria.sensor_3, 123)
		self.assertEqual(telemetria.sensor_4, 0)
		
		alerta = Alerta.objects.filter(cruce=self.cruce, type='GABINETE_ABIERTO').first()
		self.assertIsNotNone(alerta)
		self.assertEqual(alerta.severity, 'WARNING')


class CruceAPITestCase(TestCase):
	"""Tests para endpoints de cruces"""
	
	@classmethod
	def setUpTestData(cls):
		cls.user = obtener_usuario_existente('admin@test.com', 'ADMIN')
	
	def setUp(self):
		self.client = APIClient()
		self.client.force_authenticate(user=self.__class__.user)
	
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
			'estado': 'ACTIVO',
			'responsable_nombre': 'Juan Pérez',
			'responsable_telefono': '+56 9 1234 5678',
			'responsable_email': 'juan@example.com',
			'responsable_empresa': 'Ferrovial',
			'responsable_horario': 'Lunes a Viernes 8:00-18:00'
		}
		
		response = self.client.post('/api/cruces/', data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		cruce = Cruce.objects.get(nombre='Nuevo Cruce')
		self.assertEqual(cruce.responsable_nombre, 'Juan Pérez')
		self.assertEqual(cruce.responsable_empresa, 'Ferrovial')
	
	def test_eliminar_cruce_con_dependencias(self):
		"""Verifica que eliminar un cruce borra dependencias y responde 200"""
		cruce = Cruce.objects.create(nombre='Cruce para eliminar', ubicacion='Ubicación Test', estado='ACTIVO')
		
		# Crear dependencias
		sensor = Sensor.objects.create(nombre='Sensor Test', tipo='BARRERA', cruce=cruce)
		telemetria = Telemetria.objects.create(cruce=cruce, barrier_voltage=3.3, battery_voltage=12.1)
		BarrierEvent.objects.create(cruce=cruce, telemetria=telemetria, state='DOWN', event_time=timezone.now(), voltage_at_event=3.3)
		Alerta.objects.create(
			type='LOW_BATTERY',
			severity='CRITICAL',
			description='Alerta test',
			cruce=cruce,
			telemetria=telemetria
		)
		MantenimientoPreventivo.objects.create(
			nombre='Regla Test',
			descripcion='',
			tipo_mantenimiento='BATERIA',
			prioridad='MEDIA',
			condiciones={'dummy': True},
			acciones={'dummy': True},
			cruce=cruce
		)
		HistorialMantenimiento.objects.create(
			cruce=cruce,
			regla=None,
			tipo_mantenimiento='BATERIA',
			prioridad='MEDIA',
			descripcion='Historial test',
			estado='PENDIENTE',
			fecha_programada=timezone.now(),
		)
		MetricasDesempeno.objects.create(
			cruce=cruce,
			fecha=timezone.now().date(),
			tiempo_activo=1,
			tiempo_inactivo=0
		)
		
		response = self.client.delete(f'/api/cruces/{cruce.id}/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertFalse(Cruce.objects.filter(id=cruce.id).exists())
		self.assertEqual(Sensor.objects.filter(id=sensor.id).count(), 0)


class MantenimientoPreventivoTestCase(TestCase):
	"""Tests para mantenimiento preventivo"""
	
	@classmethod
	def setUpTestData(cls):
		cls.user = obtener_usuario_existente('admin@test.com', 'ADMIN')
		cls.cruce = Cruce.objects.create(
			nombre='Cruce Test',
			ubicacion='Ubicación Test',
			estado='ACTIVO'
		)
	
	def setUp(self):
		self.client = APIClient()
		self.client.force_authenticate(user=self.__class__.user)
		self.cruce = self.__class__.cruce
	
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
	
	@classmethod
	def setUpTestData(cls):
		cls.observer_user = obtener_usuario_existente('observador@test.com', 'OBSERVER')
		cls.admin_user = obtener_usuario_existente('admin@test.com', 'ADMIN')
		cls.cruce = Cruce.objects.create(
			nombre='Cruce Test',
			ubicacion='Ubicación Test',
			estado='ACTIVO'
		)
	
	def setUp(self):
		self.client = APIClient()
		self.client.force_authenticate(user=self.__class__.observer_user)
		self.cruce = self.__class__.cruce
	
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
		self.client.force_authenticate(user=self.__class__.admin_user)
		
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


class CruceN8NWebhookTestCase(TestCase):
	"""Tests para la integración n8n vía webhook"""
	
	def setUp(self):
		self.cruce = Cruce.objects.create(
			nombre='Cruce Signal n8n',
			ubicacion='Ubicación n8n',
			estado='ACTIVO'
		)
	
	@override_settings(N8N_WEBHOOK_URL='https://n8n.example/webhook')
	@patch('apps.api.n8n_service.requests.post')
	def test_envia_webhook_al_pasara_inactivo(self, mock_post):
		"""Debe llamar al webhook n8n cuando el cruce pasa de ACTIVO a INACTIVO"""
		mock_response = mock_post.return_value
		mock_response.raise_for_status.return_value = None
		
		self.cruce.estado = 'INACTIVO'
		self.cruce.save()
		
		self.assertTrue(mock_post.called)
		args, kwargs = mock_post.call_args
		self.assertIn('json', kwargs)
		payload = kwargs['json']
		self.assertEqual(payload['estado_anterior'], 'ACTIVO')
		self.assertEqual(payload['nuevo_estado'], 'INACTIVO')
		self.assertEqual(payload['cruce_id'], self.cruce.id)
	
	@override_settings(N8N_WEBHOOK_URL='https://n8n.example/webhook')
	@patch('apps.api.n8n_service.requests.post')
	def test_no_envia_webhook_para_otras_transiciones(self, mock_post):
		"""No debe llamar al webhook cuando no es una transición ACTIVO->INACTIVO"""
		mock_response = mock_post.return_value
		mock_response.raise_for_status.return_value = None
		
		self.cruce.estado = 'MANTENIMIENTO'
		self.cruce.save()
		
		mock_post.assert_not_called()

