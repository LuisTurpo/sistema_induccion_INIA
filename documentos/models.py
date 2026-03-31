from django.db import models
from users.models import User

class Documento(models.Model):
    TIPO_CHOICES = [
        ('induccion', 'Inducción'),
        ('etica',     'Código de ética'),
        ('gestion',   'Gestión'),
        ('tecnico',   'Técnico'),
    ]
    titulo       = models.CharField(max_length=200)
    tipo         = models.CharField(max_length=20, choices=TIPO_CHOICES)
    archivo      = models.FileField(upload_to='documentos/')
    descripcion  = models.TextField(blank=True)
    obligatorio  = models.BooleanField(default=True)
    activo       = models.BooleanField(default=True)
    creado_por   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.titulo