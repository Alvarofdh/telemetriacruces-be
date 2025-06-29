from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.api.models import Cruce, Sensor, Telemetria, Alerta
from datetime import timedelta
import random

class Command(BaseCommand):
    help = 'Crear datos de prueba para el sistema de cruces ferroviarios'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos de prueba...')
        
        # Crear cruces
        cruces = []
        for i in range(1, 9):  # 8 cruces
            cruce = Cruce.objects.create(
                nombre=f'Cruce {i}',
                ubicacion=f'Ubicación {i}',
                coordenadas_lat=-33.4489 + (i * 0.01),
                coordenadas_lng=-70.6693 + (i * 0.01),
                estado='ACTIVO'
            )
            cruces.append(cruce)
            self.stdout.write(f'Cruce creado: {cruce.nombre}')
        
        # Crear sensores para cada cruce
        for cruce in cruces:
            # Sensor de barrera
            Sensor.objects.create(
                nombre=f'Sensor Barrera {cruce.nombre}',
                tipo='BARRERA',
                cruce=cruce,
                descripcion='Sensor principal de barrera',
                activo=True
            )
            
            # Sensor de gabinete
            Sensor.objects.create(
                nombre=f'Sensor Gabinete {cruce.nombre}',
                tipo='GABINETE',
                cruce=cruce,
                descripcion='Sensor de apertura de gabinete',
                activo=True
            )
            
            # Sensor de batería
            Sensor.objects.create(
                nombre=f'Sensor Batería {cruce.nombre}',
                tipo='BATERIA',
                cruce=cruce,
                descripcion='Sensor de nivel de batería',
                activo=True
            )
            
            # Sensor de temperatura
            Sensor.objects.create(
                nombre=f'Sensor Temperatura {cruce.nombre}',
                tipo='TEMPERATURA',
                cruce=cruce,
                descripcion='Sensor de temperatura',
                activo=True
            )
            
            self.stdout.write(f'Sensores creados para: {cruce.nombre}')
        
        # Crear telemetría para cada cruce
        for cruce in cruces:
            # Crear 10 lecturas de telemetría en las últimas 24 horas
            for i in range(10):
                timestamp = timezone.now() - timedelta(hours=i*2)
                
                # Simular datos realistas
                barrier_voltage = random.uniform(20, 24)  # 20-24V
                battery_voltage = random.uniform(11, 14)  # 11-14V
                
                telemetria = Telemetria.objects.create(
                    cruce=cruce,
                    timestamp=timestamp,
                    barrier_voltage=barrier_voltage,
                    battery_voltage=battery_voltage,
                    sensor_1=random.randint(0, 1023),  # Gabinete
                    sensor_2=random.randint(0, 1023),  # Otro sensor
                    sensor_3=random.randint(0, 1023),  # Otro sensor
                    sensor_4=random.randint(0, 1023),  # Otro sensor
                    signal_strength=random.randint(-80, -40),
                    temperature=random.uniform(15, 35)
                )
                
                # Determinar estado de barrera basado en voltaje
                if barrier_voltage > 2.0:
                    telemetria.barrier_status = 'DOWN'
                else:
                    telemetria.barrier_status = 'UP'
                telemetria.save()
            
            self.stdout.write(f'Telemetría creada para: {cruce.nombre}')
        
        # Crear algunas alertas
        alertas_tipos = ['LOW_BATTERY', 'VOLTAGE_CRITICAL', 'GABINETE_ABIERTO']
        
        for cruce in cruces[:3]:  # Solo para los primeros 3 cruces
            tipo_alerta = random.choice(alertas_tipos)
            
            if tipo_alerta == 'LOW_BATTERY':
                descripcion = f'Batería baja en {cruce.nombre}. Voltaje actual: 10.5V'
            elif tipo_alerta == 'VOLTAGE_CRITICAL':
                descripcion = f'Voltaje crítico del PLC en {cruce.nombre}. Voltaje actual: 18.5V'
            else:
                descripcion = f'Gabinete abierto en {cruce.nombre}'
            
            Alerta.objects.create(
                type=tipo_alerta,
                description=descripcion,
                cruce=cruce,
                telemetria=Telemetria.objects.filter(cruce=cruce).first(),
                resolved=False
            )
            
            self.stdout.write(f'Alerta creada para: {cruce.nombre}')
        
        self.stdout.write(
            self.style.SUCCESS('¡Datos de prueba creados exitosamente!')
        )
        self.stdout.write(f'- {len(cruces)} cruces creados')
        self.stdout.write(f'- {len(cruces) * 4} sensores creados')
        self.stdout.write(f'- {len(cruces) * 10} lecturas de telemetría creadas')
        self.stdout.write(f'- 3 alertas creadas') 