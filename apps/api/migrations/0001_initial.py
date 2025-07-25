# Generated by Django 5.2.3 on 2025-06-29 03:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApiAlerta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=20)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField()),
                ('resolved', models.BooleanField()),
            ],
            options={
                'db_table': 'api_alerta',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=150, unique=True)),
            ],
            options={
                'db_table': 'auth_group',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthGroupPermissions',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_group_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthPermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('codename', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'auth_permission',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128)),
                ('last_login', models.DateTimeField(blank=True, null=True)),
                ('is_superuser', models.BooleanField()),
                ('username', models.CharField(max_length=150, unique=True)),
                ('first_name', models.CharField(max_length=150)),
                ('last_name', models.CharField(max_length=150)),
                ('email', models.CharField(max_length=254)),
                ('is_staff', models.BooleanField()),
                ('is_active', models.BooleanField()),
                ('date_joined', models.DateTimeField()),
            ],
            options={
                'db_table': 'auth_user',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserGroups',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_groups',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='AuthUserUserPermissions',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'auth_user_user_permissions',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoAdminLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_time', models.DateTimeField()),
                ('object_id', models.TextField(blank=True, null=True)),
                ('object_repr', models.CharField(max_length=200)),
                ('action_flag', models.SmallIntegerField()),
                ('change_message', models.TextField()),
            ],
            options={
                'db_table': 'django_admin_log',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoContentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('app_label', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'django_content_type',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoMigrations',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('app', models.CharField(max_length=255)),
                ('name', models.CharField(max_length=255)),
                ('applied', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_migrations',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='DjangoSession',
            fields=[
                ('session_key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('session_data', models.TextField()),
                ('expire_date', models.DateTimeField()),
            ],
            options={
                'db_table': 'django_session',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Cruce',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('ubicacion', models.CharField(max_length=200)),
                ('coordenadas_lat', models.FloatField(blank=True, null=True)),
                ('coordenadas_lng', models.FloatField(blank=True, null=True)),
                ('estado', models.CharField(default='ACTIVO', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Cruce',
                'verbose_name_plural': 'Cruces',
            },
        ),
        migrations.CreateModel(
            name='Sensor',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('tipo', models.CharField(choices=[('BARRERA', 'Sensor de Barrera'), ('GABINETE', 'Sensor de Gabinete'), ('BATERIA', 'Sensor de Batería'), ('PLC', 'Sensor PLC'), ('TEMPERATURA', 'Sensor de Temperatura')], max_length=20)),
                ('descripcion', models.TextField(blank=True)),
                ('activo', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('cruce', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sensores', to='api.cruce')),
            ],
            options={
                'verbose_name': 'Sensor',
                'verbose_name_plural': 'Sensores',
            },
        ),
        migrations.CreateModel(
            name='Telemetria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('barrier_voltage', models.FloatField()),
                ('battery_voltage', models.FloatField()),
                ('sensor_1', models.IntegerField(blank=True, null=True)),
                ('sensor_2', models.IntegerField(blank=True, null=True)),
                ('sensor_3', models.IntegerField(blank=True, null=True)),
                ('sensor_4', models.IntegerField(blank=True, null=True)),
                ('barrier_status', models.CharField(blank=True, choices=[('UP', 'Barrera Arriba'), ('DOWN', 'Barrera Abajo')], max_length=4, null=True)),
                ('signal_strength', models.IntegerField(blank=True, null=True)),
                ('temperature', models.FloatField(blank=True, null=True)),
                ('cruce', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='telemetrias', to='api.cruce')),
            ],
            options={
                'verbose_name': 'Telemetría',
                'verbose_name_plural': 'Telemetrías',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='BarrierEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('DOWN', 'Barrera Abajo'), ('UP', 'Barrera Arriba')], max_length=4)),
                ('event_time', models.DateTimeField()),
                ('voltage_at_event', models.FloatField()),
                ('cruce', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='barrier_events', to='api.cruce')),
                ('telemetria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='barrier_events', to='api.telemetria')),
            ],
            options={
                'verbose_name': 'Evento de Barrera',
                'verbose_name_plural': 'Eventos de Barrera',
                'ordering': ['-event_time'],
            },
        ),
        migrations.CreateModel(
            name='Alerta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('LOW_BATTERY', 'Batería Baja'), ('SENSOR_ERROR', 'Error de Sensor'), ('BARRIER_STUCK', 'Barrera Bloqueada'), ('VOLTAGE_CRITICAL', 'Voltaje Crítico'), ('COMMUNICATION_LOST', 'Comunicación Perdida'), ('GABINETE_ABIERTO', 'Gabinete Abierto')], max_length=20)),
                ('description', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('resolved', models.BooleanField(default=False)),
                ('resolved_at', models.DateTimeField(blank=True, null=True)),
                ('cruce', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alertas', to='api.cruce')),
                ('sensor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alertas', to='api.sensor')),
                ('telemetria', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='alertas', to='api.telemetria')),
            ],
            options={
                'verbose_name': 'Alerta',
                'verbose_name_plural': 'Alertas',
                'ordering': ['-created_at'],
            },
        ),
    ]
