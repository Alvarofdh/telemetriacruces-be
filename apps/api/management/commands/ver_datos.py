"""
Comando para visualizar todos los datos en la base de datos
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.api.models import UserProfile, Cruce, Telemetria, BarrierEvent, Alerta
from django.db.models import Count, Q


class Command(BaseCommand):
    help = 'Ver todos los datos en la base de datos'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("📊 RESUMEN DE DATOS EN LA BASE DE DATOS"))
        self.stdout.write("="*70 + "\n")
        
        # ============ USUARIOS ============
        self.stdout.write(self.style.WARNING("👥 USUARIOS:"))
        usuarios = User.objects.all()
        for user in usuarios:
            try:
                profile = user.profile
                self.stdout.write(
                    f"  ✅ {user.username} ({user.email})"
                )
                self.stdout.write(
                    f"     Rol: {self.style.SUCCESS(profile.get_role_display())} ({profile.role})"
                )
                self.stdout.write(
                    f"     Nombre: {user.first_name} {user.last_name}"
                )
            except:
                self.stdout.write(
                    f"  ⚠️  {user.username} ({user.email}) - {self.style.WARNING('Sin perfil')}"
                )
        self.stdout.write(f"\n  📊 Total: {self.style.SUCCESS(str(usuarios.count()))} usuarios\n")
        
        # ============ CRUCES ============
        self.stdout.write(self.style.WARNING("🚂 CRUCES:"))
        cruces = Cruce.objects.all()
        if cruces.exists():
            for cruce in cruces:
                self.stdout.write(f"  ✅ ID {cruce.id}: {self.style.SUCCESS(cruce.nombre)}")
                self.stdout.write(f"     Ubicación: {cruce.ubicacion}")
                self.stdout.write(f"     Estado: {self.style.SUCCESS(cruce.estado)}")
                if cruce.coordenadas_lat and cruce.coordenadas_lng:
                    self.stdout.write(f"     GPS: ({cruce.coordenadas_lat}, {cruce.coordenadas_lng})")
                
                # Contar telemetrías de este cruce
                tele_count = Telemetria.objects.filter(cruce=cruce).count()
                self.stdout.write(f"     Telemetrías: {tele_count}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠️  No hay cruces creados"))
        self.stdout.write(f"\n  📊 Total: {self.style.SUCCESS(str(cruces.count()))} cruces\n")
        
        # ============ TELEMETRÍA ============
        self.stdout.write(self.style.WARNING("📡 TELEMETRÍA:"))
        telemetrias = Telemetria.objects.all()
        self.stdout.write(f"  📊 Total: {self.style.SUCCESS(str(telemetrias.count()))} registros")
        if telemetrias.exists():
            ultima = telemetrias.first()
            self.stdout.write(f"  ⏰ Última: {ultima.cruce.nombre} - {ultima.timestamp}")
            self.stdout.write(
                f"     Voltajes: Barrera={ultima.barrier_voltage}V, "
                f"Batería={ultima.battery_voltage}V"
            )
            self.stdout.write(f"     Estado: {ultima.barrier_status or 'N/A'}")
        self.stdout.write()
        
        # ============ EVENTOS ============
        self.stdout.write(self.style.WARNING("🚧 EVENTOS DE BARRERA:"))
        eventos = BarrierEvent.objects.all()
        self.stdout.write(f"  📊 Total: {self.style.SUCCESS(str(eventos.count()))} eventos")
        if eventos.exists():
            ultimo = eventos.first()
            self.stdout.write(
                f"  ⏰ Último: {ultimo.cruce.nombre} - "
                f"{self.style.SUCCESS(ultimo.get_state_display())} - {ultimo.event_time}"
            )
            
            # Contar por estado
            eventos_up = eventos.filter(state='UP').count()
            eventos_down = eventos.filter(state='DOWN').count()
            self.stdout.write(f"     UP: {eventos_up}, DOWN: {eventos_down}")
        self.stdout.write()
        
        # ============ ALERTAS ============
        self.stdout.write(self.style.WARNING("🚨 ALERTAS:"))
        alertas_activas = Alerta.objects.filter(resolved=False)
        alertas_total = Alerta.objects.all()
        self.stdout.write(
            f"  🔴 Activas: {self.style.ERROR(str(alertas_activas.count()))}"
        )
        self.stdout.write(
            f"  📊 Total: {self.style.SUCCESS(str(alertas_total.count()))}"
        )
        
        if alertas_activas.exists():
            self.stdout.write("\n  ⚠️  Alertas activas:")
            for alerta in alertas_activas[:5]:
                severidad_style = {
                    'CRITICAL': self.style.ERROR,
                    'WARNING': self.style.WARNING,
                    'INFO': self.style.SUCCESS
                }.get(alerta.severity, self.style.SUCCESS)
                
                self.stdout.write(
                    f"    - {alerta.cruce.nombre}: "
                    f"{severidad_style(alerta.get_type_display())} "
                    f"({severidad_style(alerta.get_severity_display())})"
                )
                self.stdout.write(f"      {alerta.description[:60]}...")
        
        # Contar por severidad
        if alertas_activas.exists():
            critical = alertas_activas.filter(severity='CRITICAL').count()
            warning = alertas_activas.filter(severity='WARNING').count()
            info = alertas_activas.filter(severity='INFO').count()
            self.stdout.write(f"\n  Por severidad: Críticas={critical}, Advertencias={warning}, Info={info}")
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(
            self.style.SUCCESS(
                "\n💡 TIP: Usa 'python manage.py shell' para consultas más detalladas"
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "💡 TIP: Accede a http://localhost:8000/admin/ para interfaz visual\n"
            )
        )

