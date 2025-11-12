"""
Comando para probar que Socket.IO emite eventos correctamente
y que el frontend puede recibirlos
"""
from django.core.management.base import BaseCommand
from apps.api.models import Cruce, Telemetria, Alerta, Sensor
from django.utils import timezone
from decimal import Decimal
import time


class Command(BaseCommand):
	help = 'Generar eventos de prueba para verificar que Socket.IO funciona con el frontend'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			help='ID del cruce para generar eventos (por defecto: primer cruce disponible)',
		)
		parser.add_argument(
			'--telemetrias',
			type=int,
			default=5,
			help='Número de telemetrías a crear (default: 5)',
		)
		parser.add_argument(
			'--alertas',
			type=int,
			default=2,
			help='Número de alertas a crear (default: 2)',
		)
		parser.add_argument(
			'--intervalo',
			type=float,
			default=2.0,
			help='Intervalo entre eventos en segundos (default: 2.0)',
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']
		num_telemetrias = options['telemetrias']
		num_alertas = options['alertas']
		intervalo = options['intervalo']

		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('🧪 TEST DE EVENTOS SOCKET.IO'))
		self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

		# Obtener cruce
		if cruce_id:
			try:
				cruce = Cruce.objects.get(id=cruce_id)
			except Cruce.DoesNotExist:
				self.stdout.write(self.style.ERROR(f'❌ Cruce con ID {cruce_id} no existe'))
				return
		else:
			cruce = Cruce.objects.first()
			if not cruce:
				self.stdout.write(self.style.ERROR('❌ No hay cruces en la base de datos'))
				self.stdout.write(self.style.WARNING('   Ejecuta: python manage.py crear_datos_prueba'))
				return

		self.stdout.write(self.style.SUCCESS(f'✅ Usando cruce: {cruce.nombre} (ID: {cruce.id})'))
		self.stdout.write('')

		# Verificar que el servidor esté corriendo
		self.stdout.write(self.style.WARNING('⚠️  IMPORTANTE:'))
		self.stdout.write(self.style.WARNING('   1. Asegúrate de que el servidor esté corriendo con Uvicorn'))
		self.stdout.write(self.style.WARNING('   2. Abre el frontend o test_socketio_frontend.html'))
		self.stdout.write(self.style.WARNING('   3. Conecta con un token JWT válido'))
		self.stdout.write(self.style.WARNING('   4. Suscríbete a eventos y únete a la sala del cruce'))
		self.stdout.write('')

		input('Presiona Enter cuando el frontend esté conectado y listo...')

		# Crear telemetrías
		self.stdout.write(self.style.SUCCESS(f'\n📊 Creando {num_telemetrias} telemetrías...'))
		for i in range(num_telemetrias):
			telemetria = Telemetria.objects.create(
				cruce=cruce,
				barrier_voltage=Decimal(f'{3.0 + (i * 0.1):.2f}'),
				battery_voltage=Decimal(f'{12.0 + (i * 0.1):.2f}'),
				sensor_1=500 + (i * 10),
				sensor_2=600 + (i * 10),
				sensor_3=700 + (i * 10),
				sensor_4=800 + (i * 10),
				signal_strength=-70 + i,
				temperature=25 + i,
				timestamp=timezone.now()
			)
			self.stdout.write(
				self.style.SUCCESS(
					f'   ✅ Telemetría {i+1}/{num_telemetrias} creada (ID: {telemetria.id})'
				)
			)
			self.stdout.write(
				self.style.WARNING(
					f'      → Deberías ver evento "new_telemetria" en el frontend'
				)
			)
			if i < num_telemetrias - 1:
				time.sleep(intervalo)

		# Crear alertas
		self.stdout.write(self.style.SUCCESS(f'\n🚨 Creando {num_alertas} alertas...'))
		alertas_tipos = ['LOW_BATTERY', 'SENSOR_ERROR', 'BARRIER_STUCK']
		severidades = ['CRITICAL', 'WARNING', 'INFO']

		for i in range(num_alertas):
			alerta = Alerta.objects.create(
				cruce=cruce,
				type=alertas_tipos[i % len(alertas_tipos)],
				severity=severidades[i % len(severidades)],
				description=f'Alerta de prueba {i+1}: {alertas_tipos[i % len(alertas_tipos)]}',
				resolved=False
			)
			self.stdout.write(
				self.style.SUCCESS(
					f'   ✅ Alerta {i+1}/{num_alertas} creada (ID: {alerta.id}, Tipo: {alerta.type})'
				)
			)
			self.stdout.write(
				self.style.WARNING(
					f'      → Deberías ver evento "new_alerta" en el frontend'
				)
			)
			if i < num_alertas - 1:
				time.sleep(intervalo)

		# Resumen
		self.stdout.write(self.style.SUCCESS('\n' + '='*70))
		self.stdout.write(self.style.SUCCESS('📊 RESUMEN'))
		self.stdout.write(self.style.SUCCESS('='*70))
		self.stdout.write(f'\n✅ Telemetrías creadas: {num_telemetrias}')
		self.stdout.write(f'✅ Alertas creadas: {num_alertas}')
		self.stdout.write(f'✅ Cruce: {cruce.nombre} (ID: {cruce.id})')
		self.stdout.write('')

		self.stdout.write(self.style.WARNING('\n💡 Verifica en el frontend:'))
		self.stdout.write(self.style.WARNING('   - Eventos "new_telemetria" recibidos'))
		self.stdout.write(self.style.WARNING('   - Eventos "new_alerta" recibidos'))
		self.stdout.write(self.style.WARNING('   - Datos actualizados en tiempo real'))
		self.stdout.write('')

		self.stdout.write(self.style.SUCCESS('✅ Test de eventos completado\n'))

