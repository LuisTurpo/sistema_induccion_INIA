from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROL_CHOICES = [
        ('admin',      'Administrador'),
        ('personal',   'Personal'),
        ('supervisor', 'Supervisor'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='personal')

    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"

    @property
    def es_admin(self):       return self.rol == 'admin'
    @property
    def es_supervisor(self):  return self.rol == 'supervisor'
    @property
    def es_personal(self):    return self.rol == 'personal'