from django.db import models
from personal.models import Trabajador
from users.models import User

class AutorizacionFinal(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('autorizado', 'Autorizado'),
        ('rechazado',  'Rechazado'),
    ]
    trabajador        = models.OneToOneField(Trabajador, on_delete=models.CASCADE, related_name='autorizacion')
    autorizado_por    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='autorizaciones_dadas')
    estado            = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    observaciones     = models.TextField(blank=True)
    fecha_solicitud   = models.DateTimeField(auto_now_add=True)
    fecha_resolucion  = models.DateTimeField(null=True, blank=True)
    excel_generado    = models.BooleanField(default=False)
    archivo_excel     = models.FileField(upload_to='reportes/', blank=True, null=True)

    def __str__(self):
        return f"Autorización {self.trabajador} — {self.estado}"