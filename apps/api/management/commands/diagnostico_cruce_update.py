"""
Comando de diagnóstico para verificar que los eventos Socket.IO
se emiten correctamente cuando se actualiza un cruce.
"""
from django.core.management.base import BaseCommand
from apps.api.models import Cruce
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
	help = 'Diagnóstico de emisión de eventos Socket.IO para actualizaciones de cruce'

	def add_arguments(self, parser):
		parser.add_argument(
			'--cruce-id',
			type=int,
			default=21,
			help='ID del cruce a actualizar (default: 21)'
		)
		parser.add_argument(
			'--nombre',
			type=str,
			help='Nuevo nombre para el cruce (opcional)'
		)
		parser.add_argument(
			'--ubicacion',
			type=str,
			help='Nueva ubicación para el cruce (opcional)'
		)

	def handle(self, *args, **options):
		cruce_id = options['cruce_id']
		
		self.stdout.write(self.style.SUCCESS(f'\n🔍 DIAGNÓSTICO DE ACTUALIZACIÓN DE CRUCE {cruce_id}\n'))
		self.stdout.write('=' * 70)
		
		# 1. Verificar que el cruce existe
		try:
			cruce = Cruce.objects.get(id=cruce_id)
			self.stdout.write(self.style.SUCCESS(f'✅ Cruce encontrado: {cruce.nombre}'))
			self.stdout.write(f'   Ubicación: {cruce.ubicacion}')
			self.stdout.write(f'   Estado: {cruce.estado}')
			self.stdout.write(f'   Última actualización: {cruce.updated_at}')
		except Cruce.DoesNotExist:
			self.stdout.write(self.style.ERROR(f'❌ Error: Cruce con ID {cruce_id} no existe'))
			return
		
		self.stdout.write('')
		self.stdout.write('=' * 70)
		self.stdout.write('📝 PASO 1: Verificando configuración de signals...')
		
		# 2. Verificar que los signals están registrados
		from django.db.models.signals import post_save
		from apps.api.models import Cruce as CruceModel
		
		receivers = post_save._live_receivers(CruceModel)
		self.stdout.write(f'   Receivers registrados para Cruce: {len(receivers)}')
		
		if len(receivers) == 0:
			self.stdout.write(self.style.WARNING('⚠️  ADVERTENCIA: No hay receivers registrados para Cruce'))
			self.stdout.write('   Verifica que apps/api/apps.py importe signals correctamente')
		else:
			self.stdout.write(self.style.SUCCESS(f'✅ Signals registrados correctamente'))
			for i, receiver in enumerate(receivers, 1):
				self.stdout.write(f'   Receiver {i}: {receiver.__name__ if hasattr(receiver, "__name__") else str(receiver)}')
		
		self.stdout.write('')
		self.stdout.write('=' * 70)
		self.stdout.write('📝 PASO 2: Preparando actualización...')
		
		# 3. Preparar datos de actualización
		nombre_original = cruce.nombre
		ubicacion_original = cruce.ubicacion
		
		# Limpiar nombre de actualizaciones previas
		if ' (Actualizado' in nombre_original:
			nombre_original = nombre_original.split(' (Actualizado')[0]
		
		nombre_nuevo = options.get('nombre') or f"{nombre_original} (Actualizado - Test {cruce.updated_at.strftime('%H:%M:%S')})"
		ubicacion_nueva = options.get('ubicacion') or ubicacion_original
		
		# Asegurar que no exceda max_length
		if len(nombre_nuevo) > 100:
			nombre_nuevo = nombre_nuevo[:97] + '...'
		if len(ubicacion_nueva) > 200:
			ubicacion_nueva = ubicacion_nueva[:197] + '...'
		
		self.stdout.write(f'   Nombre original: {nombre_original}')
		self.stdout.write(f'   Nombre nuevo: {nombre_nuevo}')
		self.stdout.write(f'   Ubicación: {ubicacion_nueva}')
		
		self.stdout.write('')
		self.stdout.write('=' * 70)
		self.stdout.write('📝 PASO 3: Actualizando cruce (esto debería disparar el signal)...')
		self.stdout.write('')
		self.stdout.write(self.style.WARNING('⚠️  IMPORTANTE: Observa los logs del servidor Uvicorn'))
		self.stdout.write('   Deberías ver mensajes como:')
		self.stdout.write('   - 📡 Signal post_save recibido: Cruce X actualizado')
		self.stdout.write('   - 🚀 Signal detectado: Cruce X actualizado...')
		self.stdout.write('   - 🔄 Iniciando emisión de actualización...')
		self.stdout.write('   - 📤 Emitiendo evento \'cruce_update\' a sala \'cruce_X\'...')
		self.stdout.write('   - ✅ Cruce actualizado emitido exitosamente')
		self.stdout.write('')
		
		# 4. Actualizar el cruce
		cruce.nombre = nombre_nuevo
		cruce.ubicacion = ubicacion_nueva
		
		self.stdout.write('   Guardando cambios...')
		cruce.save()
		
		self.stdout.write(self.style.SUCCESS('✅ Cruce guardado exitosamente'))
		self.stdout.write('')
		
		# 5. Verificar que se actualizó
		cruce.refresh_from_db()
		self.stdout.write('=' * 70)
		self.stdout.write('📝 PASO 4: Verificación post-actualización...')
		self.stdout.write(f'   Nombre actual: {cruce.nombre}')
		self.stdout.write(f'   Última actualización: {cruce.updated_at}')
		
		self.stdout.write('')
		self.stdout.write('=' * 70)
		self.stdout.write('📝 PASO 5: Instrucciones para verificar en el frontend...')
		self.stdout.write('')
		self.stdout.write('1. Asegúrate de que el frontend esté conectado a Socket.IO')
		self.stdout.write('2. Verifica que el frontend esté escuchando el evento:')
		self.stdout.write('   socket.on("cruce_update", (data) => { ... })')
		self.stdout.write('3. Verifica que el frontend esté unido a la sala:')
		self.stdout.write(f'   socket.emit("join_room", {{ room: "cruce_{cruce_id}" }})')
		self.stdout.write('4. Revisa la consola del navegador para ver el evento')
		self.stdout.write('')
		
		self.stdout.write('=' * 70)
		self.stdout.write(self.style.SUCCESS('✅ DIAGNÓSTICO COMPLETADO'))
		self.stdout.write('')
		self.stdout.write('📋 RESUMEN:')
		self.stdout.write(f'   - Cruce {cruce_id} actualizado')
		self.stdout.write(f'   - Signal debería haberse ejecutado')
		self.stdout.write(f'   - Evento debería haberse emitido a sala "cruce_{cruce_id}"')
		self.stdout.write('')
		self.stdout.write('🔍 Si no ves eventos en el frontend:')
		self.stdout.write('   1. Verifica los logs del servidor (deberías ver los mensajes con 📡, 🚀, etc.)')
		self.stdout.write('   2. Verifica que el frontend esté conectado y autenticado')
		self.stdout.write('   3. Verifica que el frontend esté en la sala correcta')
		self.stdout.write('   4. Verifica que el frontend esté escuchando el evento correcto')
		self.stdout.write('')

