"""
Motor de Decisión para Mantenimiento Preventivo
Sistema configurable y fácil de modificar para reglas de mantenimiento
"""
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Avg, Min, Max, Count
from .models import (
	MantenimientoPreventivo, HistorialMantenimiento, Alerta, 
	Telemetria, Cruce, MetricasDesempeno
)
import logging

logger = logging.getLogger(__name__)


class MotorMantenimiento:
	"""
	Motor de decisión para mantenimiento preventivo.
	Evalúa condiciones y genera alertas/mantenimientos programados.
	"""
	
	def __init__(self):
		self.reglas_activas = None
		self._cargar_reglas()
	
	def _cargar_reglas(self):
		"""Cargar reglas activas de mantenimiento"""
		self.reglas_activas = MantenimientoPreventivo.objects.filter(activo=True)
		logger.info(f"Cargadas {self.reglas_activas.count()} reglas de mantenimiento activas")
	
	def evaluar_telemetria(self, telemetria_instance):
		"""
		Evaluar telemetría y aplicar reglas de mantenimiento preventivo
		
		Args:
			telemetria_instance: Instancia de Telemetria
		"""
		if not self.reglas_activas.exists():
			return []
		
		mantenimientos_generados = []
		
		# Filtrar reglas aplicables a este cruce
		reglas_aplicables = self.reglas_activas.filter(
			Q(cruce=telemetria_instance.cruce) | Q(cruce__isnull=True)
		)
		
		for regla in reglas_aplicables:
			try:
				if self._evaluar_condiciones(regla, telemetria_instance):
					mantenimiento = self._aplicar_regla(regla, telemetria_instance)
					if mantenimiento:
						mantenimientos_generados.append(mantenimiento)
			except Exception as e:
				logger.error(f"Error al evaluar regla {regla.nombre}: {str(e)}")
		
		return mantenimientos_generados
	
	def _evaluar_condiciones(self, regla, telemetria_instance):
		"""
		Evaluar si las condiciones de una regla se cumplen
		
		Args:
			regla: Instancia de MantenimientoPreventivo
			telemetria_instance: Instancia de Telemetria
		
		Returns:
			bool: True si las condiciones se cumplen
		"""
		condiciones = regla.condiciones
		if not condiciones:
			return False
		
		# Verificar condiciones de fecha
		if not self._verificar_fechas(regla):
			return False
		
		# Evaluar condiciones de telemetría
		resultado = True
		
		# Condición: batería baja
		if 'battery_voltage' in condiciones:
			cond = condiciones['battery_voltage']
			valor = telemetria_instance.battery_voltage
			if not self._evaluar_operador(valor, cond):
				resultado = False
		
		# Condición: voltaje de barrera
		if 'barrier_voltage' in condiciones:
			cond = condiciones['barrier_voltage']
			valor = telemetria_instance.barrier_voltage
			if not self._evaluar_operador(valor, cond):
				resultado = False
		
		# Condición: porcentaje de batería (calculado)
		if 'battery_percentage' in condiciones:
			# Calcular porcentaje basado en voltaje (12V = 100%, 10V = 0%)
			porcentaje = ((telemetria_instance.battery_voltage - 10.0) / 2.0) * 100
			porcentaje = max(0, min(100, porcentaje))  # Limitar entre 0 y 100
			cond = condiciones['battery_percentage']
			if not self._evaluar_operador(porcentaje, cond):
				resultado = False
		
		# Condición: sensor específico
		for sensor_num in [1, 2, 3, 4]:
			sensor_key = f'sensor_{sensor_num}'
			if sensor_key in condiciones:
				valor = getattr(telemetria_instance, sensor_key)
				if valor is not None:
					cond = condiciones[sensor_key]
					if not self._evaluar_operador(valor, cond):
						resultado = False
		
		# Condición: señal WiFi
		if 'signal_strength' in condiciones:
			valor = telemetria_instance.signal_strength
			if valor is not None:
				cond = condiciones['signal_strength']
				if not self._evaluar_operador(valor, cond):
					resultado = False
		
		# Condición: temperatura
		if 'temperature' in condiciones:
			valor = telemetria_instance.temperature
			if valor is not None:
				cond = condiciones['temperature']
				if not self._evaluar_operador(valor, cond):
					resultado = False
		
		# Condición: tiempo sin comunicación (basado en última telemetría)
		if 'communication_lost_hours' in condiciones:
			ultima_telemetria = Telemetria.objects.filter(
				cruce=telemetria_instance.cruce
			).order_by('-timestamp').first()
			
			if ultima_telemetria:
				tiempo_sin_comunicacion = (timezone.now() - ultima_telemetria.timestamp).total_seconds() / 3600
				cond = condiciones['communication_lost_hours']
				if not self._evaluar_operador(tiempo_sin_comunicacion, cond):
					resultado = False
		
		# Condición: horas acumuladas con batería baja
		if 'hours_low_battery' in condiciones:
			horas_baja = self._calcular_horas_bateria_baja(telemetria_instance.cruce)
			cond = condiciones['hours_low_battery']
			if not self._evaluar_operador(horas_baja, cond):
				resultado = False
		
		# Condición: días desde último mantenimiento
		if 'days_since_maintenance' in condiciones:
			ultimo_mantenimiento = HistorialMantenimiento.objects.filter(
				cruce=telemetria_instance.cruce,
				estado='COMPLETADO'
			).order_by('-fecha_fin').first()
			
			if ultimo_mantenimiento and ultimo_mantenimiento.fecha_fin:
				dias = (timezone.now() - ultimo_mantenimiento.fecha_fin).days
			else:
				dias = 999  # Nunca se ha hecho mantenimiento
			
			cond = condiciones['days_since_maintenance']
			if not self._evaluar_operador(dias, cond):
				resultado = False
		
		# Condición: mes del año (para mantenimiento estacional)
		if 'month' in condiciones:
			mes_actual = timezone.now().month
			meses = condiciones['month']
			if isinstance(meses, list):
				if mes_actual not in meses:
					resultado = False
			elif mes_actual != meses:
				resultado = False
		
		return resultado
	
	def _evaluar_operador(self, valor, condicion):
		"""
		Evaluar operador de comparación
		
		Args:
			valor: Valor a comparar
			condicion: Dict con operador y valor, ej: {'operator': 'lt', 'value': 11.0}
		
		Returns:
			bool: Resultado de la comparación
		"""
		if not isinstance(condicion, dict):
			# Si es un número simple, asumir menor que
			return valor < condicion
		
		operador = condicion.get('operator', 'lt')
		valor_condicion = condicion.get('value')
		
		if valor_condicion is None:
			return False
		
		operadores = {
			'lt': lambda v, c: v < c,   # Less than
			'le': lambda v, c: v <= c,  # Less or equal
			'gt': lambda v, c: v > c,   # Greater than
			'ge': lambda v, c: v >= c,  # Greater or equal
			'eq': lambda v, c: v == c,  # Equal
			'ne': lambda v, c: v != c,  # Not equal
			'between': lambda v, c: c[0] <= v <= c[1] if isinstance(c, list) and len(c) == 2 else False,
		}
		
		func = operadores.get(operador)
		if func:
			return func(valor, valor_condicion)
		
		return False
	
	def _verificar_fechas(self, regla):
		"""Verificar si la regla está dentro del rango de fechas válido"""
		ahora = timezone.now().date()
		
		# Verificar rango de fechas
		if regla.fecha_inicio and ahora < regla.fecha_inicio:
			return False
		if regla.fecha_fin and ahora > regla.fecha_fin:
			return False
		
		# Verificar días de la semana
		if regla.dias_semana:
			dia_semana = timezone.now().weekday()  # 0=Lunes, 6=Domingo
			# Ajustar para que 0=Domingo (como en el modelo)
			dia_semana_ajustado = (dia_semana + 1) % 7
			if dia_semana_ajustado not in regla.dias_semana:
				return False
		
		return True
	
	def _aplicar_regla(self, regla, telemetria_instance):
		"""
		Aplicar una regla de mantenimiento cuando se cumplen las condiciones
		
		Args:
			regla: Instancia de MantenimientoPreventivo
			telemetria_instance: Instancia de Telemetria
		
		Returns:
			HistorialMantenimiento: Mantenimiento creado o None
		"""
		# Verificar si ya existe un mantenimiento pendiente para esta regla
		mantenimiento_existente = HistorialMantenimiento.objects.filter(
			cruce=telemetria_instance.cruce,
			regla=regla,
			estado__in=['PENDIENTE', 'EN_PROCESO']
		).first()
		
		if mantenimiento_existente:
			# Ya existe un mantenimiento pendiente, no crear otro
			return None
		
		# Obtener acciones de la regla
		acciones = regla.acciones or {}
		
		# Calcular fecha programada
		fecha_programada = timezone.now()
		if 'dias_anticipacion' in acciones:
			fecha_programada += timedelta(days=acciones['dias_anticipacion'])
		
		# Crear descripción
		descripcion = regla.descripcion or f"Mantenimiento preventivo: {regla.get_tipo_mantenimiento_display()}"
		if telemetria_instance:
			descripcion += f"\n\nDatos actuales:\n"
			descripcion += f"- Voltaje batería: {telemetria_instance.battery_voltage}V\n"
			descripcion += f"- Voltaje barrera: {telemetria_instance.barrier_voltage}V\n"
			if telemetria_instance.signal_strength:
				descripcion += f"- Señal WiFi: {telemetria_instance.signal_strength} dBm\n"
		
		# Obtener métricas actuales
		metricas_antes = self._obtener_metricas_actuales(telemetria_instance.cruce)
		
		# Crear mantenimiento
		mantenimiento = HistorialMantenimiento.objects.create(
			cruce=telemetria_instance.cruce,
			regla=regla,
			tipo_mantenimiento=regla.tipo_mantenimiento,
			prioridad=regla.prioridad,
			descripcion=descripcion,
			fecha_programada=fecha_programada,
			metricas_antes=metricas_antes,
			estado='PENDIENTE'
		)
		
		# Generar alerta si está configurado
		if regla.generar_alerta:
			alerta = Alerta.objects.create(
				type=regla.tipo_alerta,
				severity=regla.severidad_alerta,
				description=f"Mantenimiento preventivo programado: {regla.nombre}\n{descripcion}",
				cruce=telemetria_instance.cruce,
				telemetria=telemetria_instance,
				resolved=False
			)
			
			# Enviar email de mantenimiento programado
			try:
				from .email_service import enviar_email_mantenimiento
				enviar_email_mantenimiento(mantenimiento)
			except Exception as e:
				logger.warning(f"Error al enviar email de mantenimiento: {str(e)}")
		
		logger.info(f"Mantenimiento preventivo creado: {mantenimiento.id} para cruce {telemetria_instance.cruce.nombre}")
		
		return mantenimiento
	
	def _obtener_metricas_actuales(self, cruce):
		"""Obtener métricas actuales del cruce"""
		ultima_telemetria = Telemetria.objects.filter(
			cruce=cruce
		).order_by('-timestamp').first()
		
		if not ultima_telemetria:
			return {}
		
		return {
			'battery_voltage': ultima_telemetria.battery_voltage,
			'barrier_voltage': ultima_telemetria.barrier_voltage,
			'barrier_status': ultima_telemetria.barrier_status,
			'signal_strength': ultima_telemetria.signal_strength,
			'temperature': ultima_telemetria.temperature,
			'timestamp': ultima_telemetria.timestamp.isoformat(),
		}
	
	def _calcular_horas_bateria_baja(self, cruce, horas_retroceso=24):
		"""
		Calcular horas acumuladas con batería baja en las últimas X horas
		
		Args:
			cruce: Instancia de Cruce
			horas_retroceso: Horas hacia atrás para calcular
		
		Returns:
			float: Horas con batería baja
		"""
		fecha_desde = timezone.now() - timedelta(hours=horas_retroceso)
		
		telemetrias = Telemetria.objects.filter(
			cruce=cruce,
			timestamp__gte=fecha_desde,
			battery_voltage__lt=11.5
		).order_by('timestamp')
		
		if not telemetrias.exists():
			return 0.0
		
		# Calcular tiempo total con batería baja
		# Asumiendo que cada telemetría representa un intervalo
		# Si hay telemetría cada 5 minutos, cada registro = 5/60 horas
		intervalo_horas = 5 / 60  # 5 minutos = 0.083 horas
		horas_baja = telemetrias.count() * intervalo_horas
		
		return horas_baja
	
	def evaluar_mantenimientos_programados(self):
		"""
		Evaluar y actualizar mantenimientos programados basados en fechas
		Útil para mantenimientos estacionales o por fecha específica
		"""
		mantenimientos_generados = []
		
		# Obtener reglas con fechas específicas
		reglas_fecha = self.reglas_activas.filter(
			fecha_inicio__isnull=False
		)
		
		for regla in reglas_fecha:
			if not self._verificar_fechas(regla):
				continue
			
			# Obtener cruces aplicables
			if regla.cruce:
				cruces = [regla.cruce]
			else:
				cruces = Cruce.objects.filter(estado='ACTIVO')
			
			for cruce in cruces:
				# Verificar si ya existe mantenimiento para esta regla
				mantenimiento_existente = HistorialMantenimiento.objects.filter(
					cruce=cruce,
					regla=regla,
					fecha_programada__date=timezone.now().date()
				).first()
				
				if mantenimiento_existente:
					continue
				
				# Obtener última telemetría
				ultima_telemetria = Telemetria.objects.filter(
					cruce=cruce
				).order_by('-timestamp').first()
				
				if not ultima_telemetria:
					continue
				
				# Evaluar condiciones
				if self._evaluar_condiciones(regla, ultima_telemetria):
					mantenimiento = self._aplicar_regla(regla, ultima_telemetria)
					if mantenimiento:
						mantenimientos_generados.append(mantenimiento)
		
		return mantenimientos_generados


# Instancia global del motor
motor_mantenimiento = MotorMantenimiento()

