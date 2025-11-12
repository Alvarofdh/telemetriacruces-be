"""
Comando para crear datos de prueba completos en la base de datos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import random
from apps.api.models import (
	Cruce, Sensor, Telemetria, BarrierEvent, Alerta,
	UserProfile, MantenimientoPreventivo, HistorialMantenimiento,
	MetricasDesempeno
)


class Command(BaseCommand):
	help = 'Crear datos de prueba completos para todas las funcionalidades del sistema'

	def add_arguments(self, parser):
		parser.add_argument(
			'--limpiar',
			action='store_true',
			help='Limpiar datos existentes antes de crear nuevos',
		)

	def handle(self, *args, **options):
		limpiar = options['limpiar']
		
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('📊 CREANDO DATOS DE PRUEBA'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

		if limpiar:
			self.stdout.write(self.style.WARNING('⚠️  Limpiando datos existentes...'))
			# Limpiar en orden inverso de dependencias
			MetricasDesempeno.objects.all().delete()
			HistorialMantenimiento.objects.all().delete()
			MantenimientoPreventivo.objects.all().delete()
			Alerta.objects.all().delete()
			BarrierEvent.objects.all().delete()
			Telemetria.objects.all().delete()
			Sensor.objects.all().delete()
			Cruce.objects.all().delete()
			# No eliminar usuarios existentes, solo sus perfiles si no tienen datos
			self.stdout.write(self.style.SUCCESS('✅ Datos limpiados\n'))

		# ============================================
		# 1. CREAR CRUCES
		# ============================================
		self.stdout.write(self.style.WARNING('1. Creando Cruces...'))
		
		cruces_data = [
			{
				'nombre': 'Cruce Ferroviario Norte',
				'ubicacion': 'Ruta Nacional 9, Km 45',
				'coordenadas_lat': -34.6037,
				'coordenadas_lng': -58.3816,
				'estado': 'ACTIVO',
			},
			{
				'nombre': 'Cruce Ferroviario Sur',
				'ubicacion': 'Ruta Provincial 2, Km 120',
				'coordenadas_lat': -34.6500,
				'coordenadas_lng': -58.4000,
				'estado': 'ACTIVO',
			},
			{
				'nombre': 'Cruce Ferroviario Este',
				'ubicacion': 'Autopista del Este, Km 30',
				'coordenadas_lat': -34.5500,
				'coordenadas_lng': -58.3500,
				'estado': 'MANTENIMIENTO',
			},
			{
				'nombre': 'Cruce Ferroviario Oeste',
				'ubicacion': 'Ruta Nacional 7, Km 80',
				'coordenadas_lat': -34.7000,
				'coordenadas_lng': -58.4500,
				'estado': 'ACTIVO',
			},
			{
				'nombre': 'Cruce Ferroviario Central',
				'ubicacion': 'Avenida Libertador 1500',
				'coordenadas_lat': -34.6000,
				'coordenadas_lng': -58.3800,
				'estado': 'ACTIVO',
			}
		]

		responsables_data = [
			{
				'nombre': 'Juan Pérez',
				'telefono': '+54 11 1234-5678',
				'email': 'juan.perez@mantenimiento.com',
				'empresa': 'Mantenimiento Ferroviario S.A.',
				'horario': 'Lunes a Viernes 8:00-18:00, Emergencias 24/7'
			},
			{
				'nombre': 'María González',
				'telefono': '+54 11 2345-6789',
				'email': 'maria.gonzalez@mantenimiento.com',
				'empresa': 'Servicios Técnicos Ferroviarios',
				'horario': 'Lunes a Sábado 7:00-19:00'
			},
			{
				'nombre': 'Carlos Rodríguez',
				'telefono': '+54 11 3456-7890',
				'email': 'carlos.rodriguez@mantenimiento.com',
				'empresa': 'Ingeniería y Mantenimiento',
				'horario': 'Lunes a Viernes 9:00-17:00'
			},
			{
				'nombre': 'Ana Martínez',
				'telefono': '+54 11 4567-8901',
				'email': 'ana.martinez@mantenimiento.com',
				'empresa': 'Mantenimiento Integral',
				'horario': '24/7'
			},
			{
				'nombre': 'Roberto Sánchez',
				'telefono': '+54 11 5678-9012',
				'email': 'roberto.sanchez@mantenimiento.com',
				'empresa': 'Técnicos Especializados',
				'horario': 'Lunes a Viernes 8:00-20:00'
			}
		]

		cruces = []
		for i, data in enumerate(cruces_data):
			cruce = Cruce.objects.create(**data)
			# Asignar información de responsable si los campos existen
			responsable = responsables_data[i]
			try:
				cruce.responsable_nombre = responsable['nombre']
				cruce.responsable_telefono = responsable['telefono']
				cruce.responsable_email = responsable['email']
				cruce.responsable_empresa = responsable['empresa']
				cruce.responsable_horario = responsable['horario']
				cruce.save()
			except AttributeError:
				# Los campos de responsable no existen, continuar sin ellos
				pass
			cruces.append(cruce)
			self.stdout.write(f'   ✅ {cruce.nombre} (ID: {cruce.id})')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(cruces)} cruces creados\n'))

		# ============================================
		# 2. CREAR SENSORES
		# ============================================
		self.stdout.write(self.style.WARNING('2. Creando Sensores...'))
		
		tipos_sensores = ['BARRERA', 'ALARMA', 'ENERGIA', 'TEMPERATURA', 'MOVIMIENTO']
		sensores = []
		
		for cruce in cruces:
			for i, tipo in enumerate(tipos_sensores[:3]):  # 3 sensores por cruce
				sensor = Sensor.objects.create(
					cruce=cruce,
					nombre=f'{tipo} {cruce.nombre}',
					tipo=tipo,
					descripcion=f'Sensor de {tipo.lower()} para {cruce.nombre}'
				)
				sensores.append(sensor)
				self.stdout.write(f'   ✅ {sensor.nombre}')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(sensores)} sensores creados\n'))

		# ============================================
		# 3. CREAR TELEMETRÍA (últimos 30 días)
		# ============================================
		self.stdout.write(self.style.WARNING('3. Creando Telemetría (últimos 30 días)...'))
		
		telemetrias = []
		ahora = timezone.now()
		
		for cruce in cruces:
			# Crear telemetría cada 2 horas durante los últimos 30 días
			for dias_atras in range(30, 0, -1):
				for hora in range(0, 24, 2):  # Cada 2 horas
					timestamp = ahora - timedelta(days=dias_atras, hours=24-hora)
					
					# Simular variaciones realistas
					battery_voltage = round(random.uniform(11.5, 13.5), 2)
					barrier_voltage = random.choice([0.0, 0.0, 0.0, 3.3, 24.0])  # Más tiempo UP
					
					telemetria = Telemetria.objects.create(
						cruce=cruce,
						timestamp=timestamp,
						barrier_voltage=barrier_voltage,
						battery_voltage=battery_voltage,
						sensor_1=random.randint(0, 1023),
						sensor_2=random.randint(0, 1023),
						sensor_3=random.randint(0, 1023),
						sensor_4=random.randint(0, 1023),
						signal_strength=random.randint(-80, -40),
						temperature=round(random.uniform(15, 35), 1),
						barrier_status='UP' if barrier_voltage < 2.0 else 'DOWN'
					)
					telemetrias.append(telemetria)
			
			self.stdout.write(f'   ✅ {len([t for t in telemetrias if t.cruce == cruce])} telemetrías para {cruce.nombre}')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(telemetrias)} telemetrías creadas\n'))

		# ============================================
		# 4. CREAR EVENTOS DE BARRERA
		# ============================================
		self.stdout.write(self.style.WARNING('4. Creando Eventos de Barrera...'))
		
		eventos = []
		for cruce in cruces:
			telemetrias_cruce = [t for t in telemetrias if t.cruce == cruce]
			if telemetrias_cruce:
				# Crear eventos basados en cambios de estado
				estado_anterior = None
				for telemetria in sorted(telemetrias_cruce, key=lambda x: x.timestamp):
					estado_actual = 'DOWN' if telemetria.barrier_voltage > 2.0 else 'UP'
					if estado_anterior and estado_actual != estado_anterior:
						evento = BarrierEvent.objects.create(
							cruce=cruce,
							telemetria=telemetria,
							state=estado_actual,
							event_time=telemetria.timestamp,
							voltage_at_event=telemetria.barrier_voltage
						)
						eventos.append(evento)
					estado_anterior = estado_actual
			
			self.stdout.write(f'   ✅ {len([e for e in eventos if e.cruce == cruce])} eventos para {cruce.nombre}')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(eventos)} eventos de barrera creados\n'))

		# ============================================
		# 5. CREAR ALERTAS
		# ============================================
		self.stdout.write(self.style.WARNING('5. Creando Alertas...'))
		
		tipos_alertas = [
			('LOW_BATTERY', 'CRITICAL'),
			('LOW_BATTERY', 'WARNING'),
			('VOLTAGE_CRITICAL', 'CRITICAL'),
			('SENSOR_ERROR', 'WARNING'),
			('BARRIER_STUCK', 'WARNING'),
			('COMMUNICATION_LOST', 'WARNING'),
			('GABINETE_ABIERTO', 'INFO'),
		]
		
		alertas = []
		for cruce in cruces:
			# Crear algunas alertas resueltas y otras no
			for i, (tipo, severidad) in enumerate(tipos_alertas):
				telemetria = random.choice([t for t in telemetrias if t.cruce == cruce]) if telemetrias else None
				
				# 70% resueltas, 30% activas
				resuelta = random.random() > 0.3
				created_at = ahora - timedelta(days=random.randint(1, 25))
				resolved_at = created_at + timedelta(hours=random.randint(1, 48)) if resuelta else None
				
				alerta = Alerta.objects.create(
					cruce=cruce,
					telemetria=telemetria,
					type=tipo,
					severity=severidad,
					description=f'Alerta de {tipo.replace("_", " ").lower()} en {cruce.nombre}',
					resolved=resuelta,
					created_at=created_at,
					resolved_at=resolved_at
				)
				alertas.append(alerta)
			
			self.stdout.write(f'   ✅ {len([a for a in alertas if a.cruce == cruce])} alertas para {cruce.nombre}')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(alertas)} alertas creadas\n'))

		# ============================================
		# 6. CREAR REGLAS DE MANTENIMIENTO PREVENTIVO
		# ============================================
		self.stdout.write(self.style.WARNING('6. Creando Reglas de Mantenimiento Preventivo...'))
		
		reglas_data = [
			{
				'nombre': 'Cambio de Batería - Bajo Voltaje',
				'descripcion': 'Cambiar batería cuando el voltaje sea menor a 11.5V',
				'tipo_mantenimiento': 'BATERIA',
				'prioridad': 'CRITICA',
				'condiciones': [
					{'field': 'battery_voltage', 'operator': '<', 'value': 11.5}
				],
				'acciones': {
					'crear_mantenimiento': True,
					'generar_alerta': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'LOW_BATTERY',
				'severidad_alerta': 'CRITICAL',
				'activo': True
			},
			{
				'nombre': 'Mantenimiento Mensual',
				'descripcion': 'Mantenimiento preventivo mensual de barreras',
				'tipo_mantenimiento': 'PREVENTIVO',
				'prioridad': 'MEDIA',
				'condiciones': [
					{'field': 'days_since_last_maintenance', 'operator': '>=', 'value': 30}
				],
				'acciones': {
					'crear_mantenimiento': True
				},
				'generar_alerta': False,
				'activo': True
			},
			{
				'nombre': 'Revisión de Sensores',
				'descripcion': 'Revisar sensores cuando hay errores',
				'tipo_mantenimiento': 'CORRECTIVO',
				'prioridad': 'ALTA',
				'condiciones': [
					{'field': 'sensor_errors', 'operator': '>', 'value': 0}
				],
				'acciones': {
					'crear_mantenimiento': True,
					'generar_alerta': True
				},
				'generar_alerta': True,
				'tipo_alerta': 'SENSOR_ERROR',
				'severidad_alerta': 'WARNING',
				'activo': True
			}
		]

		reglas = []
		for cruce in cruces[:3]:  # Solo para los primeros 3 cruces
			for regla_data in reglas_data:
				regla = MantenimientoPreventivo.objects.create(
					cruce=cruce,
					**regla_data
				)
				reglas.append(regla)
				self.stdout.write(f'   ✅ {regla.nombre} para {cruce.nombre}')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(reglas)} reglas de mantenimiento creadas\n'))

		# ============================================
		# 7. CREAR HISTORIAL DE MANTENIMIENTO
		# ============================================
		self.stdout.write(self.style.WARNING('7. Creando Historial de Mantenimiento...'))
		
		estados = ['COMPLETADO', 'EN_PROCESO', 'PENDIENTE']
		historial = []
		
		for cruce in cruces:
			for i in range(3):  # 3 mantenimientos por cruce
				reglas_cruce = [r for r in reglas if r.cruce == cruce]
				regla = random.choice(reglas_cruce) if reglas_cruce else None
				estado = random.choice(estados)
				
				fecha_programada = ahora - timedelta(days=random.randint(1, 60))
				fecha_inicio = fecha_programada + timedelta(hours=random.randint(1, 24)) if estado != 'PENDIENTE' else None
				fecha_fin = fecha_inicio + timedelta(hours=random.randint(1, 8)) if estado == 'COMPLETADO' and fecha_inicio else None
				
				mantenimiento = HistorialMantenimiento.objects.create(
					cruce=cruce,
					regla=regla,
					tipo_mantenimiento=random.choice(['BATERIA', 'PREVENTIVO', 'CORRECTIVO']),
					prioridad=random.choice(['CRITICA', 'ALTA', 'MEDIA', 'BAJA']),
					descripcion=f'Mantenimiento {i+1} en {cruce.nombre}',
					estado=estado,
					fecha_programada=fecha_programada,
					fecha_inicio=fecha_inicio,
					fecha_fin=fecha_fin,
					responsable=random.choice(['Juan Pérez', 'María González', 'Carlos Rodríguez']),
					metricas_antes={
						'battery_voltage': round(random.uniform(11.0, 12.5), 2),
						'barrier_voltage': round(random.uniform(0, 24), 2)
					},
					metricas_despues={
						'battery_voltage': round(random.uniform(12.0, 13.5), 2),
						'barrier_voltage': round(random.uniform(0, 24), 2),
						'observaciones': 'Mantenimiento completado exitosamente'
					} if estado == 'COMPLETADO' else {}
				)
				historial.append(mantenimiento)
			
			self.stdout.write(f'   ✅ {len([h for h in historial if h.cruce == cruce])} mantenimientos para {cruce.nombre}')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(historial)} mantenimientos en historial creados\n'))

		# ============================================
		# 8. CREAR MÉTRICAS DE DESEMPEÑO
		# ============================================
		self.stdout.write(self.style.WARNING('8. Creando Métricas de Desempeño...'))
		
		metricas = []
		for cruce in cruces:
			# Crear métricas para los últimos 7 días
			for dias_atras in range(7, 0, -1):
				fecha = (ahora - timedelta(days=dias_atras)).date()
				
				telemetrias_dia = [t for t in telemetrias if t.cruce == cruce and t.timestamp.date() == fecha]
				
				if telemetrias_dia:
					voltajes = [t.battery_voltage for t in telemetrias_dia]
					tiempo_activo = random.randint(20, 24)  # horas
					tiempo_inactivo = 24 - tiempo_activo
					
					metrica = MetricasDesempeno.objects.create(
						cruce=cruce,
						fecha=fecha,
						tiempo_activo=tiempo_activo,
						tiempo_inactivo=tiempo_inactivo,
						disponibilidad_porcentaje=round((tiempo_activo / 24) * 100, 2),
						voltaje_promedio=round(sum(voltajes) / len(voltajes), 2),
						voltaje_minimo=round(min(voltajes), 2),
						voltaje_maximo=round(max(voltajes), 2),
						horas_bateria_baja=random.randint(0, 2),
						total_eventos_barrera=len([e for e in eventos if e.cruce == cruce and e.event_time.date() == fecha]),
						total_alertas=len([a for a in alertas if a.cruce == cruce and a.created_at.date() == fecha]),
						alertas_criticas=len([a for a in alertas if a.cruce == cruce and a.severity == 'CRITICAL' and a.created_at.date() == fecha]),
						alertas_resueltas=len([a for a in alertas if a.cruce == cruce and a.resolved and a.resolved_at and a.resolved_at.date() == fecha]),
						total_telemetrias=len(telemetrias_dia),
						tiempo_sin_comunicacion=random.randint(0, 30),  # minutos
						mantenimientos_realizados=len([h for h in historial if h.cruce == cruce and h.fecha_fin and h.fecha_fin.date() == fecha]),
						mantenimientos_preventivos=len([h for h in historial if h.cruce == cruce and h.tipo_mantenimiento == 'PREVENTIVO' and h.fecha_fin and h.fecha_fin.date() == fecha]),
						mantenimientos_correctivos=len([h for h in historial if h.cruce == cruce and h.tipo_mantenimiento == 'CORRECTIVO' and h.fecha_fin and h.fecha_fin.date() == fecha])
					)
					metricas.append(metrica)
			
			self.stdout.write(f'   ✅ {len([m for m in metricas if m.cruce == cruce])} métricas para {cruce.nombre}')

		self.stdout.write(self.style.SUCCESS(f'✅ {len(metricas)} métricas de desempeño creadas\n'))

		# ============================================
		# RESUMEN FINAL
		# ============================================
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('📊 RESUMEN DE DATOS CREADOS'))
		self.stdout.write(self.style.SUCCESS('='*70))
		self.stdout.write(f'\n✅ Cruces: {len(cruces)}')
		self.stdout.write(f'✅ Sensores: {len(sensores)}')
		self.stdout.write(f'✅ Telemetrías: {len(telemetrias)}')
		self.stdout.write(f'✅ Eventos de Barrera: {len(eventos)}')
		self.stdout.write(f'✅ Alertas: {len(alertas)}')
		self.stdout.write(f'✅ Reglas de Mantenimiento: {len(reglas)}')
		self.stdout.write(f'✅ Historial de Mantenimiento: {len(historial)}')
		self.stdout.write(f'✅ Métricas de Desempeño: {len(metricas)}')
		self.stdout.write(self.style.SUCCESS('\n✅ ¡Datos de prueba creados exitosamente!\n'))
		self.stdout.write(self.style.WARNING('💡 Puedes ver estos datos en el frontend ahora\n'))

