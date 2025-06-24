from django.db import models

# Create your models here.
from django.db import models


class ApiAlerta(models.Model):
    sensor = models.ForeignKey('Sensor', models.DO_NOTHING, blank=True, null=True)
    telemetria = models.ForeignKey('Telemetria', models.DO_NOTHING, blank=True, null=True)
    type = models.CharField(max_length=20)
    description = models.TextField()
    created_at = models.DateTimeField()
    resolved = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'api_alerta'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class BarrierEvent(models.Model):
    id_evento = models.BigAutoField(primary_key=True)
    sensor = models.ForeignKey('Sensor', models.DO_NOTHING)
    telemetria = models.ForeignKey('Telemetria', models.DO_NOTHING, blank=True, null=True)
    evento = models.CharField(max_length=4)
    ts_evento = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'barrier_event'


class Cruce(models.Model):
    id_cruce = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    ubicacion = models.CharField(max_length=255)
    estado = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'cruce'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.SmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Sensor(models.Model):
    id_sensor = models.AutoField(primary_key=True)
    id_cruce = models.OneToOneField(Cruce, models.DO_NOTHING, db_column='id_cruce')
    mac_address = models.CharField(unique=True, max_length=17)
    installed_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'sensor'


class Telemetria(models.Model):
    id_telemetria = models.BigAutoField(primary_key=True)
    sensor = models.ForeignKey(Sensor, models.DO_NOTHING)
    ts = models.DateTimeField()
    nivel_bateria = models.FloatField()
    voltaje = models.FloatField()
    estado_barrera = models.BooleanField()
    gabinete_abierto = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'telemetria'
