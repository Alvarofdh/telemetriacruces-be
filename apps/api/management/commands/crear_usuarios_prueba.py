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
            admin_user.set_password('Admin123456!')
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
                    f'   Password: Admin123456!\n'
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
            maint_user.set_password('Maint123456!')
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
                    f'   Username: mantenimiento\n'
                    f'   Email: mantenimiento@test.com\n'
                    f'   Password: Maint123456!\n'
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
            obs_user.set_password('Obs123456!')
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
                    f'   Username: observador\n'
                    f'   Email: observador@test.com\n'
                    f'   Password: Obs123456!\n'
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

        separator = '='*70
        self.stdout.write(
            self.style.SUCCESS(
                f'\n{separator}\n'
                f'✅ USUARIOS DE PRUEBA CREADOS EXITOSAMENTE!\n'
                f'{separator}\n'
                f'\n📋 RESUMEN DE USUARIOS:\n'
                f'\n1. ADMINISTRADOR:'
                f'\n   - Email: admin@test.com'
                f'\n   - Password: Admin123456!'
                f'\n   - Rol: ADMIN'
                f'\n   - Permisos: Acceso completo al sistema'
                f'\n'
                f'\n2. MANTENIMIENTO:'
                f'\n   - Email: mantenimiento@test.com'
                f'\n   - Password: Maint123456!'
                f'\n   - Rol: MAINTENANCE'
                f'\n   - Permisos: Gestionar cruces y alertas'
                f'\n'
                f'\n3. OBSERVADOR:'
                f'\n   - Email: observador@test.com'
                f'\n   - Password: Obs123456!'
                f'\n   - Rol: OBSERVER'
                f'\n   - Permisos: Solo lectura'
                f'\n'
                f'\n💡 Puedes usar estos usuarios para probar:'
                f'\n   - Login en /api/login'
                f'\n   - Gestión de usuarios (solo admin)'
                f'\n   - Permisos por rol'
                f'\n   - Django Admin (solo admin)'
                f'\n{separator}'
            )
        )

