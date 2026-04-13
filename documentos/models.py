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