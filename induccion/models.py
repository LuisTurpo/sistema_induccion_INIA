from django.db import models
from personal.models import Trabajador
from documentos.models import Documento

class LecturaDocumento(models.Model):
    trabajador  = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='lecturas')
    documento   = models.ForeignKey(Documento,  on_delete=models.CASCADE, related_name='lecturas')
    leido       = models.BooleanField(default=False)
    fecha_leido = models.DateTimeField(null=True, blank=True)
    porcentaje  = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('trabajador', 'documento')

    def __str__(self):
        return f"{self.trabajador} — {self.documento} ({'leído' if self.leido else 'pendiente'})"

class FirmaEtica(models.Model):
    trabajador   = models.OneToOneField(Trabajador, on_delete=models.CASCADE, related_name='firma_etica')
    documento    = models.ForeignKey(Documento, on_delete=models.SET_NULL, null=True)
    fecha_firma  = models.DateTimeField(auto_now_add=True)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    firma_imagen = models.ImageField(upload_to='firmas/', blank=True, null=True)
    aceptado     = models.BooleanField(default=True)

    def __str__(self):
        return f"Firma de {self.trabajador} — {self.fecha_firma.date()}"