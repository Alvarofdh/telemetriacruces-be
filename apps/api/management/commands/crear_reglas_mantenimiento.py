"""
Comando para crear reglas de mantenimiento preventivo de ejemplo
"""
from django.core.management.base import BaseCommand
from apps.api.models import MantenimientoPreventivo, Cruce
from datetime import date, timedelta


class Command(BaseCommand):
	help = 'Crear reglas de mantenimiento preventivo de ejemplo'

	def handle(self, *args, **options):
		self.stdout.write('Creando reglas de mantenimiento preventivo...\n')
		
		# ============================================
		# REGLA 1: Cambio de Batería - Batería Baja
		# ============================================
		regla1, created1 = MantenimientoPreventivo.objects.get_or_create(
			nombre='Cambio de Batería - Batería Baja',
			defaults={
				'descripcion': 'Mantenimiento preventivo cuando la batería está por debajo del 30% (11.5V)',
				'tipo_mantenimiento': 'BATERIA',
				'prioridad': 'ALTA',
				'condiciones': {
					'battery_voltage': {
						'operator': 'lt',
						'value': 11.5
					},
					'battery_percentage': {
						'operator': 'lt',
						'value': 30
					}
				},
				'acciones': {
					'dias_anticipacion': 7,  # Programar 7 días antes
					'notificar_responsable': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'LOW_BATTERY',
				'severidad_alerta': 'WARNING',
				'activo': True
			}
		)
		
		if created1:
			self.stdout.write(self.style.SUCCESS('✅ Regla 1 creada: Cambio de Batería - Batería Baja'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  Regla 1 ya existe'))
		
		# ============================================
		# REGLA 2: Cambio de Batería Estacional (Invierno)
		# ============================================
		# Fechas típicas donde falla la batería por falta de luz solar
		# Ejemplo: Junio, Julio, Agosto (invierno en hemisferio sur)
		regla2, created2 = MantenimientoPreventivo.objects.get_or_create(
			nombre='Cambio de Batería Estacional - Invierno',
			defaults={
				'descripcion': 'Mantenimiento preventivo de batería durante meses de invierno (baja luz solar)',
				'tipo_mantenimiento': 'BATERIA',
				'prioridad': 'MEDIA',
				'condiciones': {
					'month': [6, 7, 8],  # Junio, Julio, Agosto
					'hours_low_battery': {
						'operator': 'gt',
						'value': 48  # Más de 48 horas con batería baja
					}
				},
				'acciones': {
					'dias_anticipacion': 14,  # Programar 14 días antes
					'notificar_responsable': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'LOW_BATTERY',
				'severidad_alerta': 'WARNING',
				'fecha_inicio': date(date.today().year, 6, 1),
				'fecha_fin': date(date.today().year, 8, 31),
				'activo': True
			}
		)
		
		if created2:
			self.stdout.write(self.style.SUCCESS('✅ Regla 2 creada: Cambio de Batería Estacional'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  Regla 2 ya existe'))
		
		# ============================================
		# REGLA 3: Revisión de Sensores - Sensor con Valores Anómalos
		# ============================================
		regla3, created3 = MantenimientoPreventivo.objects.get_or_create(
			nombre='Revisión de Sensor - Valores Anómalos',
			defaults={
				'descripcion': 'Mantenimiento cuando un sensor reporta valores fuera de rango normal',
				'tipo_mantenimiento': 'SENSOR',
				'prioridad': 'MEDIA',
				'condiciones': {
					'sensor_1': {
						'operator': 'gt',
						'value': 900  # Sensor muy alto (posible falla)
					}
				},
				'acciones': {
					'dias_anticipacion': 3,
					'notificar_responsable': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'SENSOR_ERROR',
				'severidad_alerta': 'WARNING',
				'activo': True
			}
		)
		
		if created3:
			self.stdout.write(self.style.SUCCESS('✅ Regla 3 creada: Revisión de Sensor'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  Regla 3 ya existe'))
		
		# ============================================
		# REGLA 4: Mantenimiento de Barrera - Voltaje Crítico
		# ============================================
		regla4, created4 = MantenimientoPreventivo.objects.get_or_create(
			nombre='Mantenimiento de Barrera - Voltaje Crítico',
			defaults={
				'descripcion': 'Mantenimiento cuando el voltaje de la barrera está crítico',
				'tipo_mantenimiento': 'BARRERA',
				'prioridad': 'CRITICA',
				'condiciones': {
					'barrier_voltage': {
						'operator': 'lt',
						'value': 20.0
					}
				},
				'acciones': {
					'dias_anticipacion': 1,  # Urgente, programar para mañana
					'notificar_responsable': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'VOLTAGE_CRITICAL',
				'severidad_alerta': 'CRITICAL',
				'activo': True
			}
		)
		
		if created4:
			self.stdout.write(self.style.SUCCESS('✅ Regla 4 creada: Mantenimiento de Barrera'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  Regla 4 ya existe'))
		
		# ============================================
		# REGLA 5: Mantenimiento Programado - Cada 90 días
		# ============================================
		regla5, created5 = MantenimientoPreventivo.objects.get_or_create(
			nombre='Mantenimiento General - Cada 90 Días',
			defaults={
				'descripcion': 'Mantenimiento preventivo general cada 90 días',
				'tipo_mantenimiento': 'GENERAL',
				'prioridad': 'MEDIA',
				'condiciones': {
					'days_since_maintenance': {
						'operator': 'ge',
						'value': 90
					}
				},
				'acciones': {
					'dias_anticipacion': 7,
					'notificar_responsable': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'LOW_BATTERY',  # Usar tipo genérico
				'severidad_alerta': 'INFO',
				'activo': True
			}
		)
		
		if created5:
			self.stdout.write(self.style.SUCCESS('✅ Regla 5 creada: Mantenimiento General 90 días'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  Regla 5 ya existe'))
		
		# ============================================
		# REGLA 6: Revisión Energética - Señal WiFi Débil
		# ============================================
		regla6, created6 = MantenimientoPreventivo.objects.get_or_create(
			nombre='Revisión Energética - Señal WiFi Débil',
			defaults={
				'descripcion': 'Mantenimiento cuando la señal WiFi es muy débil (posible problema de energía)',
				'tipo_mantenimiento': 'ENERGIA',
				'prioridad': 'BAJA',
				'condiciones': {
					'signal_strength': {
						'operator': 'lt',
						'value': -80  # Señal muy débil
					}
				},
				'acciones': {
					'dias_anticipacion': 14,
					'notificar_responsable': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'SENSOR_ERROR',
				'severidad_alerta': 'INFO',
				'activo': True
			}
		)
		
		if created6:
			self.stdout.write(self.style.SUCCESS('✅ Regla 6 creada: Revisión Energética'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  Regla 6 ya existe'))
		
		# ============================================
		# REGLA 7: Limpieza y Revisión - Comunicación Perdida
		# ============================================
		regla7, created7 = MantenimientoPreventivo.objects.get_or_create(
			nombre='Limpieza y Revisión - Comunicación Perdida',
			defaults={
				'descripcion': 'Mantenimiento cuando hay pérdida de comunicación prolongada',
				'tipo_mantenimiento': 'LIMPIEZA',
				'prioridad': 'ALTA',
				'condiciones': {
					'communication_lost_hours': {
						'operator': 'gt',
						'value': 24  # Más de 24 horas sin comunicación
					}
				},
				'acciones': {
					'dias_anticipacion': 0,  # Inmediato
					'notificar_responsable': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'COMMUNICATION_LOST',
				'severidad_alerta': 'CRITICAL',
				'activo': True
			}
		)
		
		if created7:
			self.stdout.write(self.style.SUCCESS('✅ Regla 7 creada: Limpieza y Revisión'))
		else:
			self.stdout.write(self.style.WARNING('⚠️  Regla 7 ya existe'))
		
		self.stdout.write(
			self.style.SUCCESS(
				'\n' + '='*70 + '\n'
				'✅ REGLAS DE MANTENIMIENTO PREVENTIVO CREADAS\n'
				'='*70 + '\n'
				'\n📋 Reglas creadas:\n'
				'1. Cambio de Batería - Batería Baja (< 11.5V)\n'
				'2. Cambio de Batería Estacional - Invierno (Jun-Ago)\n'
				'3. Revisión de Sensor - Valores Anómalos\n'
				'4. Mantenimiento de Barrera - Voltaje Crítico\n'
				'5. Mantenimiento General - Cada 90 Días\n'
				'6. Revisión Energética - Señal WiFi Débil\n'
				'7. Limpieza y Revisión - Comunicación Perdida\n'
				'\n💡 Puedes modificar estas reglas desde el admin o la API\n'
				'='*70
			)
		)

