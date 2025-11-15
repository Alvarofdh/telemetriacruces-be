"""
Comando para hacer backup de la base de datos PostgreSQL
Ejecutar diariamente vía cron job
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import os
import subprocess
import shutil


class Command(BaseCommand):
	help = 'Hacer backup de la base de datos PostgreSQL'

	def add_arguments(self, parser):
		parser.add_argument(
			'--output-dir',
			type=str,
			default='backups',
			help='Directorio donde guardar los backups (por defecto: backups/)',
		)
		parser.add_argument(
			'--retention-days',
			type=int,
			default=30,
			help='Días de retención de backups (por defecto: 30)',
		)
		parser.add_argument(
			'--compress',
			action='store_true',
			help='Comprimir el backup con gzip',
		)

	def handle(self, *args, **options):
		output_dir = options['output_dir']
		retention_days = options['retention_days']
		compress = options['compress']
		
		# Crear directorio de backups si no existe
		os.makedirs(output_dir, exist_ok=True)
		
		# Obtener configuración de base de datos
		db_config = settings.DATABASES['default']
		db_name = db_config['NAME']
		db_user = db_config['USER']
		db_host = db_config.get('HOST', 'localhost')
		db_port = db_config.get('PORT', '5432')
		
		# Generar nombre de archivo con timestamp
		timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
		backup_filename = f'{db_name}_backup_{timestamp}.dump'
		backup_path = os.path.join(output_dir, backup_filename)
		
		# Comando pg_dump
		pg_dump_cmd = [
			'pg_dump',
			'-h', db_host,
			'-p', str(db_port),
			'-U', db_user,
			'-F', 'c',  # Formato custom (comprimido por defecto)
			'-f', backup_path,
			db_name
		]
		
		# Establecer variable de entorno para password
		env = os.environ.copy()
		if 'DB_PASSWORD' in env:
			env['PGPASSWORD'] = env['DB_PASSWORD']
		elif hasattr(settings, 'DATABASES') and 'PASSWORD' in db_config:
			env['PGPASSWORD'] = db_config['PASSWORD']
		
		try:
			self.stdout.write(f'Iniciando backup de base de datos: {db_name}...')
			
			# Ejecutar pg_dump
			result = subprocess.run(
				pg_dump_cmd,
				env=env,
				capture_output=True,
				text=True
			)
			
			if result.returncode != 0:
				self.stdout.write(
					self.style.ERROR(f'❌ Error al hacer backup: {result.stderr}')
				)
				return
			
			# Comprimir si se solicita
			if compress:
				self.stdout.write('Comprimiendo backup...')
				compressed_path = f'{backup_path}.gz'
				with open(backup_path, 'rb') as f_in:
					import gzip
					with gzip.open(compressed_path, 'wb') as f_out:
						shutil.copyfileobj(f_in, f_out)
				os.remove(backup_path)
				backup_path = compressed_path
				backup_filename = f'{backup_filename}.gz'
			
			# Obtener tamaño del archivo
			file_size = os.path.getsize(backup_path)
			file_size_mb = file_size / (1024 * 1024)
			
			self.stdout.write(
				self.style.SUCCESS(
					f'✅ Backup creado exitosamente:\n'
					f'   Archivo: {backup_filename}\n'
					f'   Tamaño: {file_size_mb:.2f} MB\n'
					f'   Ubicación: {backup_path}'
				)
			)
			
			# Limpiar backups antiguos
			self._limpiar_backups_antiguos(output_dir, retention_days)
			
		except FileNotFoundError:
			self.stdout.write(
				self.style.ERROR(
					'❌ Error: pg_dump no encontrado. '
					'Asegúrate de tener PostgreSQL client tools instalado.'
				)
			)
		except Exception as e:
			self.stdout.write(
				self.style.ERROR(f'❌ Error inesperado: {str(e)}')
			)

	def _limpiar_backups_antiguos(self, backup_dir, retention_days):
		"""Eliminar backups más antiguos que retention_days"""
		try:
			cutoff_date = timezone.now() - timedelta(days=retention_days)
			deleted_count = 0
			
			for filename in os.listdir(backup_dir):
				file_path = os.path.join(backup_dir, filename)
				
				# Solo procesar archivos de backup
				if not (filename.endswith('.dump') or filename.endswith('.dump.gz')):
					continue
				
				# Obtener fecha de modificación
				file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
				file_mtime = timezone.make_aware(file_mtime)
				
				# Eliminar si es más antiguo que retention_days
				if file_mtime < cutoff_date:
					os.remove(file_path)
					deleted_count += 1
					self.stdout.write(f'🗑️  Eliminado backup antiguo: {filename}')
			
			if deleted_count > 0:
				self.stdout.write(
					self.style.SUCCESS(f'✅ {deleted_count} backup(s) antiguo(s) eliminado(s)')
				)
		except Exception as e:
			self.stdout.write(
				self.style.WARNING(f'⚠️  Error al limpiar backups antiguos: {str(e)}')
			)

