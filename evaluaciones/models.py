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

    # Cargos que deben rendir esta evaluación
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
            return True
        return self.cargos_requeridos.filter(pk=cargo.pk).exists()


class Pregunta(models.Model):
    """Modelo de pregunta con soporte para múltiples tipos"""

    TIPO_CHOICES = [
        ('abierta', 'Pregunta Abierta'),
        ('vf_bloque', 'VF en bloque'),  # NUEVO: múltiples V/F en un solo bloque
        ('multiple', 'Múltiple Opción (una respuesta)'),
        ('multiple_respuesta', 'Múltiple Respuesta (varias correctas)'),
        ('lista', 'Listar Elementos'),
        ('completar', 'Completar espacios'),
    ]

    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='preguntas'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='multiple',
        help_text='Tipo de pregunta'
    )
    enunciado = models.TextField()
    orden = models.PositiveIntegerField(default=1)
    puntaje = models.DecimalField(max_digits=4, decimal_places=1, default=1.0)

    # Para vf_bloque: guardar las subpreguntas como JSON
    # Ejemplo: [{"texto": "Afirmación 1", "correcta": true}, {"texto": "Afirmación 2", "correcta": false}]
    subpreguntas = models.JSONField(default=list, blank=True, help_text='Para VF en bloque: lista de afirmaciones')

    # Para preguntas de lista o completar - respuestas esperadas
    respuestas_esperadas = models.JSONField(
        default=list, blank=True,
        help_text='Lista de respuestas esperadas (para lista, completar)'
    )

    # Para preguntas abiertas - palabras clave para evaluación automática opcional
    palabras_clave = models.JSONField(
        default=list, blank=True,
        help_text='Palabras clave para evaluar respuesta abierta'
    )

    # Instrucciones adicionales
    instrucciones = models.TextField(
        blank=True,
        help_text='Instrucciones específicas para esta pregunta'
    )

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"[{self.get_tipo_display()}] P{self.orden}: {self.enunciado[:60]}"


class Opcion(models.Model):
    """Opciones para preguntas de tipo múltiple, V/F, etc."""
    pregunta = models.ForeignKey(
        Pregunta, on_delete=models.CASCADE,
        related_name='opciones'
    )
    texto = models.CharField(max_length=300)
    es_correcta = models.BooleanField(default=False)
    orden = models.PositiveIntegerField(default=0, help_text='Orden de aparición')

    class Meta:
        ordering = ['orden', 'id']

    def __str__(self):
        return f"{'✓ ' if self.es_correcta else ''}{self.texto[:60]}"


class Intento(models.Model):
    """Intento de evaluación por un trabajador"""

    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('finalizado', 'Finalizado'),
    ]

    trabajador = models.ForeignKey(
        Trabajador, on_delete=models.CASCADE,
        related_name='intentos'
    )
    evaluacion = models.ForeignKey(
        Evaluacion, on_delete=models.CASCADE,
        related_name='intentos'
    )
    numero_intento = models.PositiveIntegerField(default=1)
    puntuacion = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    aprobado = models.BooleanField(default=False)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('trabajador', 'evaluacion', 'numero_intento')
        ordering = ['evaluacion__nivel', 'fecha_inicio']

    def __str__(self):
        return f"{self.trabajador} — {self.evaluacion} — intento {self.numero_intento}"

    def calcular_puntaje(self):
        """Calcula el puntaje total basado en las respuestas"""
        total = 0
        for respuesta in self.respuestas.all():
            total += respuesta.puntaje_obtenido
        self.puntuacion = total
        self.aprobado = total >= self.evaluacion.nota_minima
        self.save()
        return total


class RespuestaIntento(models.Model):
    """Respuesta del trabajador a una pregunta"""

    intento = models.ForeignKey(
        Intento, on_delete=models.CASCADE,
        related_name='respuestas'
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE)

    # Para preguntas de opción múltiple/VF
    opcion = models.ForeignKey(
        Opcion, on_delete=models.CASCADE, null=True, blank=True,
        help_text='Para preguntas de tipo múltiple o VF'
    )
    opciones_seleccionadas = models.JSONField(
        default=list, blank=True,
        help_text='Para preguntas de múltiple respuesta o VF en bloque'
    )

    # Para preguntas abiertas, lista, completar
    respuesta_texto = models.TextField(
        blank=True, null=True,
        help_text='Para preguntas abiertas, lista, completar'
    )

    # Calificación
    puntaje_obtenido = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    calificada = models.BooleanField(default=False)
    comentario = models.TextField(blank=True, help_text='Comentario del evaluador')

    # Para compatibilidad con estructura anterior
    correcta = models.BooleanField(default=False)

    class Meta:
        unique_together = ('intento', 'pregunta')

    def __str__(self):
        return f"Intento {self.intento.id} — Preg {self.pregunta.orden}"

    def calificar_automaticamente(self):
        """Intenta calificar automáticamente según el tipo de pregunta"""
        
        if self.pregunta.tipo == 'vf_bloque':
            # Calcular puntaje para VF en bloque
            correctas = 0
            total = len(self.pregunta.subpreguntas)
            
            for i, sub in enumerate(self.pregunta.subpreguntas):
                if i < len(self.opciones_seleccionadas):
                    if self.opciones_seleccionadas[i] == sub.get('correcta', False):
                        correctas += 1
            
            if total > 0:
                self.puntaje_obtenido = (correctas / total) * float(self.pregunta.puntaje)
            else:
                self.puntaje_obtenido = 0
            
            self.calificada = True
            self.correcta = (correctas == total)
            self.save()
            return self.puntaje_obtenido
        
        elif self.pregunta.tipo in ['multiple', 'vf']:
            if self.opcion and self.opcion.es_correcta:
                self.puntaje_obtenido = self.pregunta.puntaje
            else:
                self.puntaje_obtenido = 0
            self.calificada = True
            
        elif self.pregunta.tipo == 'multiple_respuesta':
            opciones_correctas = set(self.pregunta.opciones.filter(es_correcta=True).values_list('id', flat=True))
            seleccionadas = set(self.opciones_seleccionadas)
            
            if opciones_correctas == seleccionadas:
                self.puntaje_obtenido = self.pregunta.puntaje
            elif seleccionadas:
                aciertos = len(opciones_correctas & seleccionadas)
                errores = len(seleccionadas - opciones_correctas)
                puntaje_parcial = (aciertos / len(opciones_correctas)) * float(self.pregunta.puntaje)
                if errores > 0:
                    puntaje_parcial = max(0, puntaje_parcial - (errores * (float(self.pregunta.puntaje) / len(opciones_correctas)) / 2))
                self.puntaje_obtenido = round(puntaje_parcial, 1)
            else:
                self.puntaje_obtenido = 0
            self.calificada = True
            
        elif self.pregunta.tipo == 'lista':
            if self.respuesta_texto:
                respuesta_lista = [item.strip().lower() for item in self.respuesta_texto.split(',')]
                esperadas = [item.strip().lower() for item in self.pregunta.respuestas_esperadas]
                
                aciertos = sum(1 for r in respuesta_lista if r in esperadas)
                if aciertos == len(esperadas):
                    self.puntaje_obtenido = self.pregunta.puntaje
                elif aciertos > 0:
                    puntaje_parcial = (aciertos / len(esperadas)) * float(self.pregunta.puntaje)
                    self.puntaje_obtenido = round(puntaje_parcial, 1)
                else:
                    self.puntaje_obtenido = 0
            self.calificada = True
            
        elif self.pregunta.tipo == 'abierta':
            self.calificada = False
            
        self.correcta = self.puntaje_obtenido >= (float(self.pregunta.puntaje) / 2)
        self.save()
        return self.puntaje_obtenido