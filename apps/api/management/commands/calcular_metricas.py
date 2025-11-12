"""
Comando para calcular métricas de desempeño diarias
Ejecutar diariamente vía cron job
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Avg, Min, Max, Count, Q
from apps.api.models import (
	Cruce, Telemetria, Alerta, BarrierEvent, HistorialMantenimiento, MetricasDesempeno
)


class Command(BaseCommand):
	help = 'Calcular métricas de desempeño diarias para todos los cruces'

	def add_arguments(self, parser):
		parser.add_argument(
			'--fecha',
			type=str,
			help='Fecha a calcular (YYYY-MM-DD). Por defecto: ayer',
		)
		parser.add_argument(
			'--cruce',
			type=int,
			help='ID del cruce específico (opcional)',
		)

	def handle(self, *args, **options):
		# Determinar fecha a calcular
		if options['fecha']:
			try:
				fecha_calcular = date.fromisoformat(options['fecha'])
			except ValueError:
				self.stdout.write(self.style.ERROR('Formato de fecha inválido. Use YYYY-MM-DD'))
				return
		else:
			# Por defecto, calcular métricas de ayer
			fecha_calcular = (timezone.now() - timedelta(days=1)).date()
		
		self.stdout.write(f'Calculando métricas para {fecha_calcular}...')
		
		# Obtener cruces
		if options['cruce']:
			cruces = Cruce.objects.filter(id=options['cruce'])
		else:
			cruces = Cruce.objects.all()
		
		total_calculadas = 0
		
		for cruce in cruces:
			try:
				metricas = self._calcular_metricas_cruce(cruce, fecha_calcular)
				if metricas:
					total_calculadas += 1
					self.stdout.write(
						self.style.SUCCESS(
							f'✅ Métricas calculadas para {cruce.nombre}: '
							f'Disponibilidad: {metricas.disponibilidad_porcentaje:.1f}%'
						)
					)
			except Exception as e:
				self.stdout.write(
					self.style.ERROR(f'❌ Error al calcular métricas para {cruce.nombre}: {str(e)}')
				)
		
		self.stdout.write(
			self.style.SUCCESS(
				f'\n✅ Proceso completado. Métricas calculadas: {total_calculadas}/{cruces.count()}'
			)
		)

	def _calcular_metricas_cruce(self, cruce, fecha):
		"""Calcular métricas para un cruce en una fecha específica"""
		# Rango de tiempo del día
		inicio_dia = timezone.make_aware(timezone.datetime.combine(fecha, timezone.datetime.min.time()))
		fin_dia = timezone.make_aware(timezone.datetime.combine(fecha, timezone.datetime.max.time()))
		
		# Obtener o crear métricas del día
		metricas, created = MetricasDesempeno.objects.get_or_create(
			cruce=cruce,
			fecha=fecha,
			defaults={}
		)
		
		# ============================================
		# MÉTRICAS DE TELEMETRÍA
		# ============================================
		telemetrias = Telemetria.objects.filter(
			cruce=cruce,
			timestamp__gte=inicio_dia,
			timestamp__lte=fin_dia
		)
		
		total_telemetrias = telemetrias.count()
		metricas.total_telemetrias = total_telemetrias
		
		if total_telemetrias > 0:
			# Voltajes
			voltajes_bateria = telemetrias.values_list('battery_voltage', flat=True)
			voltajes_barrera = telemetrias.values_list('barrier_voltage', flat=True)
			
			metricas.voltaje_promedio = sum(voltajes_bateria) / total_telemetrias if voltajes_bateria else None
			metricas.voltaje_minimo = min(voltajes_bateria) if voltajes_bateria else None
			metricas.voltaje_maximo = max(voltajes_bateria) if voltajes_bateria else None
			
			# Horas con batería baja (< 11.5V)
			telemetrias_bateria_baja = telemetrias.filter(battery_voltage__lt=11.5)
			# Asumiendo telemetría cada 5 minutos
			intervalo_horas = 5 / 60  # 0.083 horas
			metricas.horas_bateria_baja = telemetrias_bateria_baja.count() * intervalo_horas
		else:
			# Sin telemetría = tiempo sin comunicación
			metricas.tiempo_sin_comunicacion = 24.0  # Todo el día sin comunicación
		
		# ============================================
		# MÉTRICAS DE EVENTOS
		# ============================================
		eventos = BarrierEvent.objects.filter(
			cruce=cruce,
			event_time__gte=inicio_dia,
			event_time__lte=fin_dia
		)
		metricas.total_eventos_barrera = eventos.count()
		
		# ============================================
		# MÉTRICAS DE ALERTAS
		# ============================================
		alertas = Alerta.objects.filter(
			cruce=cruce,
			created_at__gte=inicio_dia,
			created_at__lte=fin_dia
		)
		metricas.total_alertas = alertas.count()
		metricas.alertas_criticas = alertas.filter(severity='CRITICAL').count()
		metricas.alertas_resueltas = alertas.filter(resolved=True).count()
		
		# ============================================
		# MÉTRICAS DE MANTENIMIENTO
		# ============================================
		mantenimientos = HistorialMantenimiento.objects.filter(
			cruce=cruce,
			fecha_programada__gte=inicio_dia,
			fecha_programada__lte=fin_dia
		)
		metricas.mantenimientos_realizados = mantenimientos.filter(estado='COMPLETADO').count()
		metricas.mantenimientos_preventivos = mantenimientos.filter(
			regla__isnull=False,
			estado='COMPLETADO'
		).count()
		metricas.mantenimientos_correctivos = mantenimientos.filter(
			regla__isnull=True,
			estado='COMPLETADO'
		).count()
		
		# ============================================
		# MÉTRICAS DE DISPONIBILIDAD
		# ============================================
		# Calcular tiempo activo vs inactivo
		# Si hay telemetría, el cruce está activo
		# Si no hay telemetría por más de 1 hora, está inactivo
		
		if total_telemetrias > 0:
			# Calcular intervalos de actividad
			telemetrias_ordenadas = telemetrias.order_by('timestamp')
			
			tiempo_activo = 0
			tiempo_inactivo = 0
			ultima_telemetria = None
			
			for telemetria in telemetrias_ordenadas:
				if ultima_telemetria:
					intervalo = (telemetria.timestamp - ultima_telemetria.timestamp).total_seconds() / 3600
					
					if intervalo <= 1.0:  # Menos de 1 hora entre telemetrías = activo
						tiempo_activo += intervalo
					else:  # Más de 1 hora = inactivo
						tiempo_inactivo += intervalo - 1.0
						tiempo_activo += 1.0
				else:
					# Primera telemetría del día
					tiempo_desde_inicio = (telemetria.timestamp - inicio_dia).total_seconds() / 3600
					if tiempo_desde_inicio <= 1.0:
						tiempo_activo += tiempo_desde_inicio
					else:
						tiempo_inactivo += tiempo_desde_inicio - 1.0
						tiempo_activo += 1.0
				
				ultima_telemetria = telemetria
			
			# Tiempo desde última telemetría hasta fin del día
			if ultima_telemetria:
				tiempo_hasta_fin = (fin_dia - ultima_telemetria.timestamp).total_seconds() / 3600
				if tiempo_hasta_fin <= 1.0:
					tiempo_activo += tiempo_hasta_fin
				else:
					tiempo_inactivo += tiempo_hasta_fin - 1.0
					tiempo_activo += 1.0
			
			metricas.tiempo_activo = tiempo_activo
			metricas.tiempo_inactivo = tiempo_inactivo
		else:
			# Sin telemetría = todo el día inactivo
			metricas.tiempo_activo = 0
			metricas.tiempo_inactivo = 24.0
		
		# Calcular porcentaje de disponibilidad
		total_horas = metricas.tiempo_activo + metricas.tiempo_inactivo
		if total_horas > 0:
			metricas.disponibilidad_porcentaje = (metricas.tiempo_activo / total_horas) * 100
		else:
			metricas.disponibilidad_porcentaje = 0
		
		# Guardar métricas
		metricas.save()
		
		return metricas

