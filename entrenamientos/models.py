from django.db import models
from personal.models import Trabajador
from evaluaciones.models import Evaluacion
from documentos.models import Documento


class ModuloEntrenamiento(models.Model):
    TIPO_CHOICES = [
        ('gestion', 'Sistema de gestión'),
        ('tecnico', 'Entrenamiento técnico'),
    ]
    titulo      = models.CharField(max_length=200)
    tipo        = models.CharField(max_length=20, choices=TIPO_CHOICES)
    descripcion = models.TextField(blank=True)
    documentos  = models.ManyToManyField(Documento, blank=True, related_name='modulos')
    evaluacion  = models.ForeignKey(
        Evaluacion, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    orden  = models.PositiveIntegerField(default=1)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.titulo}"


class AvanceEntrenamiento(models.Model):
    trabajador       = models.ForeignKey(
        Trabajador, on_delete=models.CASCADE, related_name='avances'
    )
    modulo           = models.ForeignKey(
        ModuloEntrenamiento, on_delete=models.CASCADE, related_name='avances'
    )
    completado       = models.BooleanField(default=False)
    fecha_inicio     = models.DateTimeField(auto_now_add=True)
    fecha_completado = models.DateTimeField(null=True, blank=True)
    observaciones    = models.TextField(blank=True)

    class Meta:
        unique_together = ('trabajador', 'modulo')

    def __str__(self):
        estado = 'completado' if self.completado else 'en progreso'
        return f"{self.trabajador} — {self.modulo} ({estado})"