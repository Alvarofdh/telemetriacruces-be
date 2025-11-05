"""
Comando para crear usuarios de prueba con diferentes roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.api.models import UserProfile


class Command(BaseCommand):
    help = 'Crear usuarios de prueba con roles ADMIN, MAINTENANCE y OBSERVER'

    def handle(self, *args, **options):
        # Crear ADMINISTRADOR
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@test.com',
                'first_name': 'Administrador',
                'last_name': 'Sistema'
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.is_staff = True  # ← IMPORTANTE: Para acceder a Django Admin
            admin_user.is_superuser = True  # ← IMPORTANTE: Para permisos de admin
            admin_user.save()
            # La señal automática creará el perfil, pero asegurémonos
            profile, profile_created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={'role': 'ADMIN'}
            )
            if not profile_created:
                profile.role = 'ADMIN'
                profile.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ ADMINISTRADOR creado:\n'
                    f'   Username: admin\n'
                    f'   Email: admin@test.com\n'
                    f'   Password: admin123\n'
                    f'   Rol: ADMIN\n'
                    f'   ✅ Puede acceder a Django Admin'
                )
            )
        else:
            # Usuario existe, actualizar permisos de admin
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
            # Usuario existe, verificar/actualizar perfil
            profile, profile_created = UserProfile.objects.get_or_create(
                user=admin_user,
                defaults={'role': 'ADMIN'}
            )
            if not profile_created and profile.role != 'ADMIN':
                profile.role = 'ADMIN'
                profile.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Usuario admin ya existe - Rol y permisos actualizados'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Usuario admin ya existe (Rol: {profile.get_role_display()})\n'
                        f'   ✅ Permisos de admin actualizados'
                    )
                )

        # Crear PERSONAL DE MANTENIMIENTO
        maint_user, created = User.objects.get_or_create(
            username='mantenimiento',
            defaults={
                'email': 'mantenimiento@test.com',
                'first_name': 'Personal',
                'last_name': 'Mantenimiento'
            }
        )
        if created:
            maint_user.set_password('maint123')
            maint_user.save()
            profile, profile_created = UserProfile.objects.get_or_create(
                user=maint_user,
                defaults={'role': 'MAINTENANCE'}
            )
            if not profile_created:
                profile.role = 'MAINTENANCE'
                profile.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ MANTENIMIENTO creado:\n'
                    f'   Email: mantenimiento@test.com\n'
                    f'   Password: maint123\n'
                    f'   Rol: MAINTENANCE'
                )
            )
        else:
            profile, profile_created = UserProfile.objects.get_or_create(
                user=maint_user,
                defaults={'role': 'MAINTENANCE'}
            )
            if not profile_created and profile.role != 'MAINTENANCE':
                profile.role = 'MAINTENANCE'
                profile.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Usuario mantenimiento ya existe - Rol actualizado a MAINTENANCE'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Usuario mantenimiento ya existe (Rol: {profile.get_role_display()})'
                    )
                )

        # Crear OBSERVADOR
        obs_user, created = User.objects.get_or_create(
            username='observador',
            defaults={
                'email': 'observador@test.com',
                'first_name': 'Usuario',
                'last_name': 'Observador'
            }
        )
        if created:
            obs_user.set_password('obs123')
            obs_user.save()
            profile, profile_created = UserProfile.objects.get_or_create(
                user=obs_user,
                defaults={'role': 'OBSERVER'}
            )
            if not profile_created:
                profile.role = 'OBSERVER'
                profile.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ OBSERVADOR creado:\n'
                    f'   Email: observador@test.com\n'
                    f'   Password: obs123\n'
                    f'   Rol: OBSERVER'
                )
            )
        else:
            profile, profile_created = UserProfile.objects.get_or_create(
                user=obs_user,
                defaults={'role': 'OBSERVER'}
            )
            if not profile_created and profile.role != 'OBSERVER':
                profile.role = 'OBSERVER'
                profile.save()
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Usuario observador ya existe - Rol actualizado a OBSERVER'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Usuario observador ya existe (Rol: {profile.get_role_display()})'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                '\n✅ Usuarios de prueba creados exitosamente!\n'
                'Puedes usar estos usuarios para probar el login y roles.'
            )
        )

