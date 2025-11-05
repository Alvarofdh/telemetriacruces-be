"""
Comando para crear un cruce de prueba fácilmente
"""
from django.core.management.base import BaseCommand
from apps.api.models import Cruce


class Command(BaseCommand):
    help = 'Crear un cruce de prueba para testing con ESP32'

    def add_arguments(self, parser):
        parser.add_argument(
            '--nombre',
            type=str,
            default='Cruce de Prueba',
            help='Nombre del cruce'
        )
        parser.add_argument(
            '--ubicacion',
            type=str,
            default='Av. Principal 123',
            help='Ubicación del cruce'
        )
        parser.add_argument(
            '--lat',
            type=float,
            default=-33.4489,
            help='Latitud (coordenada GPS)'
        )
        parser.add_argument(
            '--lng',
            type=float,
            default=-70.6693,
            help='Longitud (coordenada GPS)'
        )

    def handle(self, *args, **options):
        nombre = options['nombre']
        ubicacion = options['ubicacion']
        lat = options['lat']
        lng = options['lng']
        
        cruce, created = Cruce.objects.get_or_create(
            nombre=nombre,
            defaults={
                'ubicacion': ubicacion,
                'coordenadas_lat': lat,
                'coordenadas_lng': lng,
                'estado': 'ACTIVO'
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Cruce creado exitosamente!\n'
                    f'   ID: {cruce.id}\n'
                    f'   Nombre: {cruce.nombre}\n'
                    f'   Ubicación: {cruce.ubicacion}\n'
                    f'   Estado: {cruce.estado}\n'
                    f'\n'
                    f'   Usa este ID en tu ESP32: cruce_id = {cruce.id}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  El cruce "{nombre}" ya existe.\n'
                    f'   ID: {cruce.id}\n'
                    f'   Estado: {cruce.estado}'
                )
            )

