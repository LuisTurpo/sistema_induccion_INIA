from django.db import models
from users.models import User

class Cargo(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self): return self.nombre

class Area(models.Model):
    nombre = models.CharField(max_length=100)
    def __str__(self): return self.nombre

class Trabajador(models.Model):
    ESTADO_CHOICES = [
        ('proceso',  'En proceso'),
        ('activo',   'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    usuario       = models.OneToOneField(User,   on_delete=models.CASCADE, related_name='trabajador')
    cargo         = models.ForeignKey(Cargo,     on_delete=models.SET_NULL, null=True)
    area          = models.ForeignKey(Area,      on_delete=models.SET_NULL, null=True)
    dni           = models.CharField(max_length=8, unique=True)
    telefono      = models.CharField(max_length=15, blank=True)
    fecha_ingreso = models.DateField()
    estado        = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='proceso')
    foto          = models.ImageField(upload_to='fotos/', blank=True, null=True)

    def __str__(self):
        return f"{self.usuario.get_full_name()} — {self.cargo}"