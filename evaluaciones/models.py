from django.db import models
from users.models import User
from personal.models import Trabajador, Cargo


class Evaluacion(models.Model):

    NIVEL_CHOICES = [
        ('induccion',          'Nivel 1 — Inducción General'),
        ('gestion',            'Nivel 2 — Sistema de Gestión'),
        ('tecnico_general',    'Nivel 3 — Técnico General'),
        ('tecnico_especifico', 'Nivel 4 — Técnico Específico'),
    ]

    TIPO_CHOICES = [
        ('induccion', 'Inducción'),
        ('gestion',   'Gestión'),
        ('tecnico',   'Técnico'),
    ]

    titulo         = models.CharField(max_length=200)
    nivel          = models.CharField(
                         max_length=30,
                         choices=NIVEL_CHOICES,
                         default='induccion',
                         help_text='Nivel según MAN-02 LABSAF'
                     )
    tipo           = models.CharField(
                         max_length=20,
                         choices=TIPO_CHOICES,
                         default='induccion',
                         help_text='Tipo para compatibilidad con F-52'
                     )
    descripcion    = models.TextField(blank=True)
    nota_minima    = models.DecimalField(max_digits=4, decimal_places=1, default=14.0)
    max_intentos   = models.PositiveIntegerField(default=3)
    tiempo_limite  = models.PositiveIntegerField(
                         null=True, blank=True,
                         help_text='Minutos. Dejar vacío = sin límite.'
                     )
    activa         = models.BooleanField(default=True)
    creado_por     = models.ForeignKey(
                         User, on_delete=models.SET_NULL,
                         null=True, related_name='evaluaciones_creadas'
                     )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # ── NUEVO: cargos que deben rendir esta evaluación ──────────────────────
    # Si está vacío → aplica a TODOS los cargos (Nivel 1 - Inducción General)
    cargos_requeridos = models.ManyToManyField(
                            Cargo,
                            blank=True,
                            related_name='evaluaciones',
                            help_text='Cargos que deben rendir esta evaluación. '
                                      'Dejar vacío = aplica a TODOS.'
                        )

    class Meta:
        ordering = ['nivel', 'titulo']

    def __str__(self):
        return f"[{self.get_nivel_display()}] {self.titulo}"

    def aplica_a_cargo(self, cargo):
        """True si esta evaluación aplica al cargo dado."""
        if not self.cargos_requeridos.exists():
            return True  # Sin restricción → todos
        return self.cargos_requeridos.filter(pk=cargo.pk).exists()


class Pregunta(models.Model):

    TIPO_CHOICES = [
        ('abierta', 'Abierta'),
        ('vf', 'Verdadero/Falso'),
        ('multiple', 'Opción múltiple'),
    ]

    evaluacion  = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='preguntas'
    )
    enunciado   = models.TextField()
    tipo        = models.CharField(max_length=10, choices=TIPO_CHOICES, default='multiple')
    orden       = models.PositiveIntegerField(default=1)
    puntaje     = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"P{self.orden}: {self.enunciado[:60]}"


class Opcion(models.Model):
    pregunta    = models.ForeignKey(
                      Pregunta, on_delete=models.CASCADE,
                      related_name='opciones'
                  )
    texto       = models.CharField(max_length=300)
    es_correcta = models.BooleanField(default=False)

    def __str__(self):
        return f"{'[OK] ' if self.es_correcta else ''}{self.texto[:60]}"


class Intento(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('finalizado', 'Finalizado'),
    ]

    trabajador     = models.ForeignKey(
                         Trabajador, on_delete=models.CASCADE,
                         related_name='intentos'
                     )
    evaluacion     = models.ForeignKey(
                         Evaluacion, on_delete=models.CASCADE,
                         related_name='intentos'
                     )
    numero_intento = models.PositiveIntegerField(default=1)
    puntuacion     = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    aprobado       = models.BooleanField(default=False)

    # 🔥 ESTE ES EL CAMPO QUE FALTABA
    estado         = models.CharField(
                         max_length=20,
                         choices=ESTADO_CHOICES,
                         default='pendiente'
                     )

    fecha_inicio   = models.DateTimeField(auto_now_add=True)
    fecha_fin      = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('trabajador', 'evaluacion', 'numero_intento')
        ordering = ['evaluacion__nivel', 'fecha_inicio']

    def __str__(self):
        return f"{self.trabajador} — {self.evaluacion} — intento {self.numero_intento}"


class RespuestaIntento(models.Model):
    intento  = models.ForeignKey(
                   Intento, on_delete=models.CASCADE,
                   related_name='respuestas'
               )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)
    opcion   = models.ForeignKey(Opcion,   on_delete=models.CASCADE)
    correcta = models.BooleanField(default=False)

    class Meta:
        unique_together = ('intento', 'pregunta')

    def __str__(self):
        return f"Intento {self.intento.id} — Preg {self.pregunta.orden}"