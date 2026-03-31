from django.db import models
from personal.models import Trabajador
from users.models import User

class RevisionSupervisor(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('aprobado',   'Aprobado'),
        ('observado',  'Con observaciones'),
        ('rechazado',  'Rechazado'),
    ]
    trabajador   = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='revisiones')
    supervisor   = models.ForeignKey(User,       on_delete=models.SET_NULL, null=True, related_name='revisiones_hechas')
    estado       = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    comentario   = models.TextField(blank=True)
    fecha        = models.DateTimeField(auto_now_add=True)
    fecha_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.trabajador} — {self.supervisor} — {self.estado}"