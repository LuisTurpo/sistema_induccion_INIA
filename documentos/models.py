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

class DocumentoUsuario(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documentos_usuario')
    titulo = models.CharField(max_length=200, verbose_name='Título')  # ← AGREGAR ESTE CAMPO
    descripcion = models.TextField(blank=True, null=True, verbose_name='Descripción')  # ← AGREGAR ESTE CAMPO
    archivo = models.FileField(upload_to='documentos_usuario/%Y/%m/%d/', verbose_name='Archivo')
    fecha_subida = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de subida')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    observacion = models.TextField(blank=True, null=True, verbose_name='Observaciones')  # ← Este ya lo tienes
    fecha_revision = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de revisión')  # ← Opcional

    def __str__(self):
        return f"{self.titulo} - {self.usuario.get_full_name()} - {self.estado}"
    
    class Meta:
        ordering = ['-fecha_subida']
        verbose_name = 'Documento de usuario'
        verbose_name_plural = 'Documentos de usuarios'

# Agrega esto al final de tu models.py si no lo has hecho:
class HistorialLecturaExamen(models.Model):
    """Registra cuándo un usuario leyó un documento o hizo un examen (fechas reales)"""
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historial_lecturas')
    documento = models.ForeignKey(Documento, on_delete=models.CASCADE, related_name='historial_lecturas')
    fecha_lectura = models.DateField(null=True, blank=True, verbose_name='Fecha real de lectura')
    fecha_examen = models.DateField(null=True, blank=True, verbose_name='Fecha real del examen')
    nota = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name='Nota (%)')
    observaciones = models.TextField(blank=True, verbose_name='Observaciones')
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='historial_creados')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro en sistema')
    actualizado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='historial_actualizados')
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name='Última actualización')

    class Meta:
        unique_together = ['usuario', 'documento']
        ordering = ['-fecha_lectura']
        verbose_name = 'Historial de lectura/examen'
        verbose_name_plural = 'Historiales de lecturas/exámenes'

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.documento.titulo} - Lectura: {self.fecha_lectura or 'Pendiente'}"